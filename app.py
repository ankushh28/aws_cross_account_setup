import os

import aws_cdk as cdk

from infra.stacks.entsre_stack import AlarmCreatorStack

env_name = os.getenv("ENV_NAME", "default")
if env_name not in ["int", "bat", "crt"]:
    raise ValueError(f"Invalid environment name: {env_name}")

app = cdk.App()
AlarmCreatorStack(app, f"CdkprojectStack-{env_name}",)

app.synth()