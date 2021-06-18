from anyway import secrets
from boto3 import resource as resource_builder
from .config import ANYWAY_BUCKET


class S3DataClass:

    def __init__(self):
        self._aws_access_key = secrets.get("AWS_ACCESS_KEY")
        self._aws_secret_key = secrets.get("AWS_SECRET_KEY")
        self._s3_resource = None
        self._s3_bucket = None
        self._client = None

    @property
    def s3_resource(self):
        if self._s3_resource is None:
            self._s3_resource = resource_builder(
                "s3",
                aws_access_key_id=self._aws_access_key,
                aws_secret_access_key=self._aws_secret_key,
            )
        return self._s3_resource

    @property
    def s3_bucket(self):
        if self._s3_bucket is None:
            self._s3_bucket = self.s3_resource.Bucket(ANYWAY_BUCKET)
        return self._s3_bucket
