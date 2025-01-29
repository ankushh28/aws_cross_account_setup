from aws_cdk import Stack, aws_lambda as lambda_
from constructs import Construct
from infra.constructs.s3_construct import S3Construct
from infra.constructs.lambda_construct import LambdaConstruct
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy

class AlarmCreatorStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        s3_construct = S3Construct(self, "S3Construct", bucket_name="entsrecwalarmcreator-testankush")
        lambda_construct = LambdaConstruct(
            self, "LambdaConstruct", 
            bucket=s3_construct.bucket,
            function_name="entsrealarmcreator-testankush",
            code_path="src/lambda/alarmCreator",
            handler="index.handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={
                "S3_BUCKET": s3_construct.bucket.bucket_name,
                "S3_KEY": "config/config.json"
            }
        )

        event_rule = events.Rule(
            self, "ScheduleRule",
            schedule=events.Schedule.cron(minute="0", hour="0")
        )
        event_rule.add_target(targets.LambdaFunction(lambda_construct.lambda_function))