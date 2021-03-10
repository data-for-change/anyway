from os import environ, makedirs, mkdir
from os.path import basename, dirname, abspath, join as join_path, exists as does_path_exist
from datetime import datetime
from boto3 import resource as resource_builder
from tempfile import mkdtemp
from anyway import secrets

get_environment_variable = environ.get

from .config import ACCIDENTS_TYPE_1, ACCIDENTS_TYPE_3, \
    ANYWAY_BUCKET, LOCAL_CBS_DIRECTORY, ACCIDENTS_TYPE_PREFIX


class S3DataRetriever:
    def __init__(self):
        self.__aws_access_key = secrets.get("AWS_ACCESS_KEY")
        self.__aws_secret_key = secrets.get("AWS_SECRET_KEY")
        self.__accidents_types = [ACCIDENTS_TYPE_1, ACCIDENTS_TYPE_3]
        self.__s3_resource = None
        self.__s3_bucket = None
        self.__temp_directory = None
        self.__local_files_directory = None
        self.__current_year = None
        self.__download_from_s3_callback = None

    @property
    def s3_resource(self):
        if self.__s3_resource is None:
            self.__s3_resource = resource_builder(
                "s3",
                aws_access_key_id=self.__aws_access_key,
                aws_secret_access_key=self.__aws_secret_key,
            )

        return self.__s3_resource

    @property
    def s3_bucket(self):
        if self.__s3_bucket is None:
            self.__s3_bucket = self.s3_resource.Bucket(ANYWAY_BUCKET)

        return self.__s3_bucket

    @property
    def current_year(self):
        if self.__current_year is None:
            now = datetime.now()
            current_year = now.year
            self.__current_year = int(current_year)

        return self.__current_year

    @property
    def local_temp_directory(self):
        if self.__temp_directory is None:
            current_file_path = abspath(__file__)
            current_directory = dirname(current_file_path)
            parent_directory = dirname(current_directory)
            self.__temp_directory = mkdtemp(dir=parent_directory)

        return self.__temp_directory

    @property
    def local_files_directory(self):
        if self.__local_files_directory is None:
            temp_directory = self.local_temp_directory
            files_directory = join_path(temp_directory, LOCAL_CBS_DIRECTORY)

            if not does_path_exist(files_directory):
                makedirs(files_directory)

            self.__local_files_directory = files_directory

        return self.__local_files_directory

    @property
    def download_from_s3_callback(self):
        if self.__download_from_s3_callback is None:
            download_from_s3_callback = self.s3_resource.meta.client.download_file
            self.__download_from_s3_callback = download_from_s3_callback

        return self.__download_from_s3_callback

    def __download_accidents_type_files(self, accidents_type, start_year):
        current_year, s3_bucket, local_directory = (
            self.current_year,
            self.s3_bucket,
            self.local_files_directory,
        )

        download_from_s3_callback = self.download_from_s3_callback

        accidents_type_directory = f"{ACCIDENTS_TYPE_PREFIX}_{accidents_type}"

        for year in range(start_year, current_year + 1):
            s3_files_directory = f"{accidents_type_directory}/{year}"

            for s3_object in s3_bucket.objects.filter(Prefix=s3_files_directory):
                local_dir_path = join_path(local_directory, accidents_type_directory)
                if not does_path_exist(local_dir_path):
                    mkdir(local_dir_path)
                local_dir_path = join_path(local_dir_path, str(year))
                if not does_path_exist(local_dir_path):
                    mkdir(local_dir_path)
                object_key = s3_object.key
                s3_filename = basename(object_key)
                local_file_path = join_path(local_dir_path, s3_filename)
                download_from_s3_callback(
                    Bucket=ANYWAY_BUCKET, Key=object_key, Filename=local_file_path
                )

    def get_files_from_s3(self, start_year, accidents_types=None):
        desired_accidents_types = None

        if accidents_types is None:
            desired_accidents_types = self.__accidents_types
        else:
            desired_accidents_types = accidents_types

        start_year = int(start_year)

        for accidents_type in desired_accidents_types:
            self.__download_accidents_type_files(
                accidents_type=accidents_type, start_year=start_year
            )
