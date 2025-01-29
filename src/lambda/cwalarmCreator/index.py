import os
import json
import boto3

REQUIRED_ENV_VARS = {
    "S3_BUCKET": "S3 bucket name",
    "S3_KEY": "S3 object key",
    "ROLE_ARN": "IAM Role ARN for cross-account access",
    "TARGET_REGION": "AWS region for CloudWatch alarms",
}

STATE_FILE_PATH = "/tmp/state.json"

def validate_environment():
    missing = [var for var in REQUIRED_ENV_VARS if var not in os.environ]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

def load_local_state():
    try:
        with open(STATE_FILE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"etag": None}

def save_local_state(state):
    with open(STATE_FILE_PATH, "w") as f:
        json.dump(state, f)

def get_config_etag(s3_bucket, s3_key):
    s3 = boto3.client("s3")
    response = s3.head_object(Bucket=s3_bucket, Key=s3_key)
    return response["ETag"]

def config_changed(s3_bucket, s3_key):
    current_etag = get_config_etag(s3_bucket, s3_key)
    local_state = load_local_state()
    if local_state["etag"] == current_etag:
        return False
    local_state["etag"] = current_etag
    save_local_state(local_state)
    return True

def get_cloudwatch_client(role_arn, region):
    sts = boto3.client("sts")
    assumed_role = sts.assume_role(RoleArn=role_arn, RoleSessionName="CloudWatchAlarmCreationSession")
    credentials = assumed_role["Credentials"]
    return boto3.client(
        "cloudwatch",
        region_name=region,
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )

def validate_alarm_configuration(config):
    required_params = {
        "AlarmName", "Namespace", "MetricName", "Statistic",
        "Period", "EvaluationPeriods", "Threshold", "ComparisonOperator"
    }
    missing = required_params - set(config.keys())
    if missing:
        raise ValueError(f"Missing parameters: {', '.join(missing)}")
    if config.get("Statistic") not in {"SampleCount", "Average", "Sum", "Minimum", "Maximum"}:
        raise ValueError("Invalid Statistic")
    if not isinstance(config.get("Period"), int) or config["Period"] < 1:
        raise ValueError("Period must be a positive integer")

def get_alarm_configurations(s3_bucket, s3_key):
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
    configs = json.loads(response["Body"].read().decode("utf-8"))
    if not isinstance(configs, list):
        raise ValueError("Config should be a JSON array")
    return configs

def get_existing_alarm_names(cloudwatch, configs):
    alarm_names = [cfg["AlarmName"] for cfg in configs]
    existing_names = set()
    for i in range(0, len(alarm_names), 100):
        chunk = alarm_names[i:i+100]
        response = cloudwatch.describe_alarms(AlarmNames=chunk)
        existing_names.update(alarm["AlarmName"] for alarm in response.get("MetricAlarms", []))
    return existing_names

def create_alarms(cloudwatch, configs):
    existing_names = get_existing_alarm_names(cloudwatch, configs)
    results = []
    for config in configs:
        alarm_name = config.get("AlarmName")
        if alarm_name in existing_names:
            results.append({"AlarmName": alarm_name, "Status": "Skipped", "Message": "Already exists"})
            continue
        try:
            validate_alarm_configuration(config)
            cloudwatch.put_metric_alarm(**config)
            results.append({"AlarmName": alarm_name, "Status": "Success", "Message": "Created"})
        except Exception as e:
            results.append({"AlarmName": alarm_name, "Status": "Failed", "Error": str(e)})
    return results

def handler(event, context):
    try:
        validate_environment()
        s3_bucket = os.environ["S3_BUCKET"]
        s3_key = os.environ["S3_KEY"]
        role_arn = os.environ["ROLE_ARN"]
        target_region = os.environ["TARGET_REGION"]

        if not config_changed(s3_bucket, s3_key):
            return {"statusCode": 200, "body": "Configuration unchanged"}

        cloudwatch = get_cloudwatch_client(role_arn, target_region)
        configs = get_alarm_configurations(s3_bucket, s3_key)
        results = create_alarms(cloudwatch, configs)

        success = sum(1 for r in results if r["Status"] == "Success")
        failed = sum(1 for r in results if r["Status"] == "Failed")
        return {
            "statusCode": 200,
            "body": {"created": success, "failed": failed, "results": results}
        }
    except Exception as e:
        return {"statusCode": 500, "body": f"Error: {str(e)}"}