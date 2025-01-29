from aws_cdk import (
    aws_s3 as s3
)
from constructs import Construct
class S3Construct(Construct):
    def __init__(self, scope: Construct, id: str, bucket_name: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        self.bucket = s3.Bucket(
            self, "S3Bucket",
            bucket_name=bucket_name
        )
