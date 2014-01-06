#!/usr/bin/env python
import sys
import os
import urlparse

def main():
    DATABASE_URI = os.getenv('CLEARDB_DATABASE_URL')

    if not DATABASE_URI:
        print >>sys.stderr, 'Environment CLEARDB_DATABASE_URL not set'
        sys.exit(1)

    db = urlparse.urlparse(DATABASE_URI)
    os.execlp('mysql', 'mysql', '-u', db.username, '-p' + db.password, '-h', db.hostname, db.path[1:])

if __name__ == '__main__':
    main()
