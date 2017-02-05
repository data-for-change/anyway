## United Hatzalah Data

This document describes the data obtained from [United Hatzalah](https://israelrescue.org)
It contains information about traffic accidents from 2015 onward, including location, time, and severity of the accident.

The data is sent from United Hatzalah as an automatic period report containing a CSV file to our Gmail inbox, anyway@anyway.co.il.
A Gmail filter assigns it the label `united-hatzala/data`.
On our production environment, a `crontab` entry invokes the `united.py` script.
The script calls `importmail.py`, which, given the `MAILUSER` and `MAILPASS` environment variables are set correctly,
connects to the Gmail inbox and downloads all attachments in the matching threads.
Then `united.py` goes through the downloaded data files and imports them to the database.

Before February 2017 the data format was slightly different, which is why `united.py` is able to load both old and new data.
