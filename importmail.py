import email
import imaplib
import os
from datetime import datetime, timedelta
import time
from process import time_delta
import sys
import argparse

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
#           --lastmail is currently set to default True
##############################################################################################


def main():
    maildir = 'united-hatzala/data'
    detach_dir = 'static/data/united'

    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default='')
    parser.add_argument('--password', default='')
    parser.add_argument('--lastmail', action='store_true', default=False)
    args = parser.parse_args()

    try:
        if args.username:
            username = args.username
        else:
            username = os.environ['MAILUSER']     # Set and environment variable MAILUSER with the password
    except:
        print "Please set env var MAILUSER, or provide one using importmail.py --username <username>"
        exit()

    try:
        if args.password:
            passwd = args.password
        else:
            passwd = os.environ['MAILPASS']     # Set and environment variable MAILPASS with the password
    except:
        print "Please set env var MAILPASS, or provide one using importmail.py --password <pass>"
        exit()

    imapsession = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
        imapsession.login(username, passwd)
    except:
        print 'Bad credentials, Not able to sign in!'
        exit()

    try:
        imapsession.select(maildir)
        typ, data = imapsession.search(None, 'ALL')
    except:
        print 'Error searching given maibox: %s' % maildir
        exit()

    filefound = False
    listdir = os.listdir(detach_dir)

    isempty = True if not listdir or len(listdir) == 1 or not args.lastmail else False
    total = 0

    # Iterating over all emails
    started = datetime.now()
    print "Login successful! Importing files, please hold..."
    for msgId in data[0].split():
        typ, messageparts = imapsession.fetch(msgId, '(RFC822)')
        if typ != 'OK':
            print 'Error fetching mail.'
            raise

        emailbody = messageparts[0][1]
        mail = email.message_from_string(emailbody)
        mtime = datetime.strptime(mail['Date'][:-6], '%a, %d %b %Y %H:%M:%S')

        if not isempty:
            # Accident folder is not empty, we only need the latest
            if datetime.now() - mtime < timedelta(hours=4):
                filefound = True
            else:
                continue

        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()

            if bool(filename) and filename[-3:] == "csv":
                filename = 'UH-{0}_{1}-{2}.csv'.format(mtime.date(), mtime.hour, mtime.minute)
                filepath = os.path.join(detach_dir, filename)
                if os.path.isfile(filepath):
                    break
                total += 1
                print 'Currently loading: ' + filename + '       '
                sys.stdout.write("\033[F")
                time.sleep(0.1)
                fp = open(filepath, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

        if filefound:
            break

    print("Imported {0} file(s) in {1}".format(total, time_delta(started)))
    imapsession.close()
    imapsession.logout()

if __name__ == "__main__":
    main()
