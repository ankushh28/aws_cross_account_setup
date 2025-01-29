
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from constructs import Construct
class LambdaConstruct(Construct):
    def __init__(self, scope: Construct, id: str, 
                 function_name: str,
                 code_path: str,
                 handler: str,
                 runtime: lambda_.Runtime,
                 environment: dict,
                 **kwargs):
        super().__init__(scope, id, **kwargs)
        
        self.lambda_function = lambda_.Function(
            self, "LambdaFunction",
            function_name=function_name,
            runtime=runtime,
            handler=handler,
            code=lambda_.Code.from_asset(code_path),
            environment=environment
        )
