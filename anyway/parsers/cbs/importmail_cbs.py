import email
import imaplib
import logging
import shutil
import os
import zipfile
from datetime import datetime
from anyway.parsers.cbs.s3.uploader import S3Uploader
from anyway.parsers.cbs import preprocessing_cbs_files
from anyway.parsers.cbs.executor import get_file_type_and_year
from anyway import secrets


class Mail:
    def __init__(self):
        self._username = secrets.get("MAILUSER")
        self._password = secrets.get("MAILPASS")
        self.imap_session = None

    def login(self):
        if not self._username:
            logging.error(
                "Username not set. Please set env var MAILUSER or use the --username argument"
            )
        if not self._password:
            logging.error(
                "Password not set. Please set env var MAILPASS or use the --password argument"
            )
        if self.imap_session is None:
            self.imap_session = imaplib.IMAP4_SSL("imap.gmail.com")
            self.imap_session.login(self._username, self._password)

    def select_dir(self, mail_dir):
        self.imap_session.select(mail_dir)


class MailImporter:
    def __init__(self, mail_dir="cbs/data"):
        self.mail_dir = mail_dir
        self.mail = Mail()
        self.temp_files_dir_path = "cbs_importmail_temp"

    def get_temp_files_dir(self):
        return self.temp_files_dir_path

    def create_temp_files_dir(self) -> None:
        if not os.path.exists(self.temp_files_dir_path):
            os.mkdir(self.temp_files_dir_path)
        else:
            self.delete_temp_files_dir()
            os.mkdir(self.temp_files_dir_path)
            # raise ValueError('temp files dir already exists')

    def delete_temp_files_dir(self) -> None:
        if os.path.exists(self.temp_files_dir_path):
            shutil.rmtree(self.temp_files_dir_path)
        else:
            raise ValueError("temp files dir does not exist")

    def get_recent_cbs_emails(self, emails_num=2, email_search_start_date=""):
        logging.info(f"Trying to import email from label {self.mail_dir}")
        if email_search_start_date == "":
            _, data = self.mail.imap_session.search(None, "ALL")
        else:
            search_start_date = datetime.strptime(email_search_start_date, "%d.%m.%Y").strftime(
                "%d-%b-%Y"
            )
            _, data = self.mail.imap_session.search(None, '(SINCE "{0}")'.format(search_start_date))

        # Iterating over all emails
        logging.info("Login successful! Importing files, please hold...")
        emails_time_dict = {}
        for msgId in data[0].split():
            _, message_parts = self.mail.imap_session.fetch(msgId, "(RFC822)")
            email_body = message_parts[0][1]

            if type(email_body) is bytes:
                email_body = email_body.decode("utf-8")

            mail = email.message_from_string(email_body)
            try:
                mtime = datetime.strptime(mail["Date"][:-6], "%a, %d %b %Y %H:%M:%S")
            except ValueError:
                mtime = datetime.strptime(mail["Date"][:-12], "%a, %d %b %Y %H:%M:%S")
            for part in mail.walk():
                if (
                    part.get_content_maintype() == "multipart"
                    or part.get("Content-Disposition") is None
                ):
                    continue
                filename = part.get_filename()

                if bool(filename) and filename.endswith(".zip"):
                    emails_time_dict[msgId] = mtime
        emails_with_zip_sorted_by_time = sorted(emails_time_dict.items(), key=lambda item: item[1])

        # get recent emails
        recent_cbs_emails = []
        for i in reversed(range(1, emails_num + 1)):
            recent_cbs_emails.append(emails_with_zip_sorted_by_time[-i])
        return recent_cbs_emails

    def import_cbs_data_to_s3(self, emails_num=4, email_search_start_date=""):
        self.mail.login()
        self.mail.select_dir(self.mail_dir)
        recent_cbs_emails = self.get_recent_cbs_emails(
            emails_num=emails_num, email_search_start_date=email_search_start_date
        )
        for msgId, mtime in recent_cbs_emails:
            typ, message_parts = self.mail.imap_session.fetch(msgId, "(RFC822)")
            if typ != "OK":
                logging.error("Error fetching mail.")
                raise Exception("Error fetching mail")

            email_body = message_parts[0][1]
            if type(email_body) is bytes:
                email_body = email_body.decode("utf-8")
            mail = email.message_from_string(email_body)
            for part in mail.walk():
                if (
                    part.get_content_maintype() == "multipart"
                    or part.get("Content-Disposition") is None
                ):
                    continue
                filename = part.get_filename()

                if bool(filename) and filename.endswith(".zip"):
                    filename = "{0}-{1}_{2}-{3}.zip".format(
                        "cbs_data", mtime.date(), mtime.hour, mtime.minute
                    )
                    self.create_temp_files_dir()
                    filepath = os.path.join(self.get_temp_files_dir(), filename)
                    if os.path.isfile(filepath):
                        break
                    logging.info("Currently loading: " + filename + "       ")
                    with open(filepath, "wb+") as fp:
                        fp.write(part.get_payload(decode=True))
                    non_zip_path = filepath.replace("zip", "")
                    with zipfile.ZipFile(filepath, "r") as zf:
                        zf.extractall(non_zip_path)
                    preprocessing_cbs_files.update_cbs_files_names(non_zip_path)
                    acc_data_file_path = preprocessing_cbs_files.get_accidents_file_data(
                        non_zip_path
                    )
                    provider_code, year = get_file_type_and_year(acc_data_file_path)

                    s3_uploader = S3Uploader()

                    # delete current cbs data from s3
                    s3_uploader.delete_from_s3(provider_code, year)

                    # upload new cbs data to s3
                    for file in os.scandir(non_zip_path):
                        s3_uploader.upload_to_s3(
                            local_file_path=file.path, provider_code=provider_code, year=year
                        )
                    self.delete_temp_files_dir()

        self.mail.imap_session.close()
        self.mail.imap_session.logout()


def main():
    importer = MailImporter()
    importer.import_cbs_data_to_s3()
