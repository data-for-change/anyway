import os
import logging
from .base import S3DataClass
from .config import ACCIDENTS_TYPE_PREFIX


class S3Uploader(S3DataClass):
    def __init__(self):
        super().__init__()

    def upload_to_S3(self, local_file_path, provider_code, year):
        local_filename = os.path.basename(local_file_path)
        accidents_type_directory = f"{ACCIDENTS_TYPE_PREFIX}_{provider_code}"
        s3_filename = f"{accidents_type_directory}/{year}/{local_filename}"
        with open(local_file_path, "rb") as file_data:
            logging.info(f"Uploading to S3: , {s3_filename}")
            self.s3_bucket.upload_fileobj(file_data, s3_filename)

    def delete_from_s3(self, provider_code, year):
        accidents_type_directory = f"{ACCIDENTS_TYPE_PREFIX}_{provider_code}/{year}"
        logging.info(f"Deleting from S3: ', {accidents_type_directory}")
        self.s3_bucket.objects.filter(Prefix=accidents_type_directory).delete()
