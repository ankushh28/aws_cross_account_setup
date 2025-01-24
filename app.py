#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdkproject.cdkproject_stack import CdkprojectStack

env_name = os.getenv("ENV_NAME", "default")
if env_name not in ["int", "bat", "crt"]:
    raise ValueError(f"Invalid environment name: {env_name}")
app = cdk.App()
CdkprojectStack(app, f"CdkprojectStack-{env_name}",
    )

app.synth()
