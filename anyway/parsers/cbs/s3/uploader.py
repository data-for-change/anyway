import os

from .base import S3DataClass
from .config import ACCIDENTS_TYPE_PREFIX

class S3Uploader(S3DataClass):

    def __init__(self):
        super().__init__()

    def upload_to_S3(self, local_file_path, provider_code, year):

        local_filename = os.path.basename(local_file_path)

        accidents_type_directory = f"{ACCIDENTS_TYPE_PREFIX}_{provider_code}"

        s3_filename = f'{accidents_type_directory}/{year}/{local_filename}'

        with open(local_file_path, 'rb') as file_data:
            self.s3_bucket.upload_fileobj(file_data, s3_filename)
