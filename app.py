#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdkproject.cdkproject_stack import CdkprojectStack


app = cdk.App()
CdkprojectStack(app, "CdkprojectStack",
    )

app.synth()
