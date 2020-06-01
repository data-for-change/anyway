#!/usr/bin/env python3
import sys
import urllib.parse

def emit(key, value):
    print(f'export X_{key}="{value}"')

u = urllib.parse.urlparse(sys.argv[1])
for key in ('hostname', 'port', 'username', 'password', 'path'):
    emit(key.upper(), getattr(u, key))