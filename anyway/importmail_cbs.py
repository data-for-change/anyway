from __future__ import print_function
import email
import imaplib
import os
from datetime import datetime
import time
from .utilities import time_delta
import sys
import argparse
import logging

mail_dir = 'cbs/data'


def main(detach_dir, username=None, password=None, email_search_start_date=''):
    try:
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
            if email_search_start_date == '':
                typ, data = imapsession.search(None, 'ALL')
            else:
                search_start_date = datetime.strptime(email_search_start_date, '%d.%m.%Y').strftime('%d-%b-%Y')
                typ, data = imapsession.search(None, '(SINCE "{0}")'.format(search_start_date))
        except imaplib.IMAP4.error:
            logging.error('Error searching given mailbox: %s' % mail_dir)
            exit()

        file_found = False
        if not os.path.exists(detach_dir):
            os.makedirs(detach_dir)
        total = 0

        # Iterating over all emails
        started = datetime.now()
        logging.info("Login successful! Importing files, please hold...")
        filepath = None
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

            for part in mail.walk():
                if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                    continue
                filename = part.get_filename()

                if bool(filename) and filename.endswith(".zip"):
                    filename = '{0}-{1}_{2}-{3}.zip'.format('cbs_data', mtime.date(), mtime.hour, mtime.minute)
                    filepath = os.path.join(detach_dir, filename)
                    if os.path.isfile(filepath):
                        break
                    total += 1
                    print('Currently loading: ' + filename + '       ')
                    sys.stdout.write("\033[F")
                    time.sleep(0.1)
                    with open(filepath, 'wb') as fp:
                        fp.write(part.get_payload(decode=True))
                    file_found = True

            if file_found:
                break

        logging.info("Imported {0} file(s) in {1}".format(total, time_delta(started)))
        imapsession.close()
        imapsession.logout()
        return filepath
    except Exception as _:
        pass # Todo - send an error email to anyway email


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default='')
    parser.add_argument('--password', default='')
    parser.add_argument('--lastmail', action='store_true', default=False)
    args = parser.parse_args()

    main(args.username, args.password, args.lastmail)

