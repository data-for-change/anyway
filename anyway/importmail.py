import email
import imaplib
import os
from datetime import datetime, timedelta
import time
from .utilities import time_delta
import sys
import argparse
import logging

##############################################################################################
# importmail.py is responsible for extracting and downloading united hatzala email attachments
# Requirements: Setting an environment variable named MAILPASS containing the password
#               And another named MAILUSER containing the mail account username
# Note: 1. This script is being called by united.py prior to DB import
#       2. If 'detach_dir' is empty the script would download all available files
#          If it's not, only the last file would be downloaded
#       3. Consider emptying the mail directory from time to time to speed things up
#       4. Command line arguments:
#           --username can be used to set mail user without env var
#           --password can be used to set mail password without env var
#           --lastmail is currently set to default False
##############################################################################################

mail_dir = 'united-hatzala/data'
detach_dir = 'static/data/united'


def main(username=None, password=None, lastmail=False):

    username = username or os.environ.get('MAILUSER')
    password = password or os.environ.get('MAILPASS')
    if not username:
        logging.error("Username not set. Please set env var MAILUSER or use the --username argument")
    if not password:
        logging.error("Password not set. Please set env var MAILPASS or use the --password argument")
    if not username or not password:
        exit()

    imapsession = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
        imapsession.login(username, password)
    except imaplib.IMAP4.error:
        logging.error('Bad credentials, unable to sign in!')
        exit()

    try:
        imapsession.select(mail_dir)
        typ, data = imapsession.search(None, 'ALL')
    except imaplib.IMAP4.error:
        logging.error('Error searching given mailbox: %s' % mail_dir)
        exit()

    file_found = False
    listdir = os.listdir(detach_dir)

    is_empty = len(listdir) <= 1 or not lastmail
    total = 0

    # Iterating over all emails
    started = datetime.now()
    logging.info("Login successful! Importing files, please hold...")
    for msgId in data[0].split():
        typ, message_parts = imapsession.fetch(msgId, '(RFC822)')
        if typ != 'OK':
            logging.error('Error fetching mail.')
            raise Exception('Error fetching mail')

        email_body = message_parts[0][1]
        mail = email.message_from_string(email_body)
        try:
            mtime = datetime.strptime(mail['Date'][:-6], '%a, %d %b %Y %H:%M:%S')
        except ValueError:
            mtime = datetime.strptime(mail['Date'][:-12], '%a, %d %b %Y %H:%M:%S')

        if not is_empty:
            # Accident folder is not empty, we only need the latest
            if datetime.now() - mtime < timedelta(hours=4):
                file_found = True
            else:
                continue

        # Handles Gmail bug which hasn't physically removed some of the deleted files
        mail_date = datetime(2015, 10, 06, 10)
        if mtime < mail_date:
            continue

        for part in mail.walk():
            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()

            if bool(filename) and filename.endswith(".csv"):
                filename = 'UH-{0}_{1}-{2}.csv'.format(mtime.date(), mtime.hour, mtime.minute)
                filepath = os.path.join(detach_dir, filename)
                if os.path.isfile(filepath):
                    break
                total += 1
                print 'Currently loading: ' + filename + '       '
                sys.stdout.write("\033[F")
                time.sleep(0.1)
                with open(filepath, 'wb') as fp:
                    fp.write(part.get_payload(decode=True))

        if file_found:
            break

    logging.info("Imported {0} file(s) in {1}".format(total, time_delta(started)))
    imapsession.close()
    imapsession.logout()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default='')
    parser.add_argument('--password', default='')
    parser.add_argument('--lastmail', action='store_true', default=False)
    args = parser.parse_args()

    main(args.username, args.password, args.lastmail)

