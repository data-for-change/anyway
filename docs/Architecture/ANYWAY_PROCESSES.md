ANYWAY PROCESSES
=================


Data: Scraping, Processing, DB insertions
------------------------------------------

## News Flash: extracts data from source, processes it and pushes it to NewsFlash table
In Addition - the InfographicsDataCache is filled with relevant data of the newsflash
Environment Variables for the processing part: GOOGLE_MAPS_KEY (for google's location API)
Additional environment variables for the each source:
* Ynet Newsflashes. Additional Environment Variables: None
* Walla Newsflashes. Additional Environment Variables: None
* Twitter - Adds tweets to NewsFlash table. Additional Environment Variables: TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
command: `python3 main.py process news-flash`
Sceduling: Nowadays runs in Jenkins every 30 minutes
Future: this needs to be separated into different processes, that each can trigger the next one (perhaps using Airflow): insertion of newsflash/tweets data into s3, processing newsflash/tweets data and insertion into NewsFlash table and perhaps additional tables, Creating infographics data (perhaps using aggregation tables that will created in CBS process)

## CBS: pulls data from email to s3
Environment Variables: MAILPASS, MAILUSER
command: `python3 main.py scripts importemail`
Sceduling: Nowadays runs in Jenkins once a week
Future: nowadays we pull the last data from last 2 emails and insert data to s3 (after deleting previous data), we need to pull only emails we didn't save to s3 - hence track on the emails we already read and not re-insert them. Optional: We can add CBS data versioning in s3 - right now we delete old data and insert new one.

## CBS: pulls data from s3, processes cbs data and pushes it to CBS tables
Environment Variables: AWS_ACCESS_KEY, AWS_SECRET_KEY
command: `python3 main.py process cbs --load_start_year 2021 --source s3`
Scheduling: to be scheduled
Future: scheduling this process, making sure this process is triggered once new data is inserted to s3, create aggregation tables for infographics data

## Waze: pulls data from waze, saves it in Google Cloud Storage
Scheduling: runs in Google Cloud (not in Jenkins) - runs every 5 minutes
Future: Transfer process to S3

## Waze: pulls data from Google Cloud Storage - Stores in our DB
Environment Variables: GOOGLE_LOGIN_CLIENT_ID, GOOGLE_LOGIN_CLIENT_SECRET
Future: this process's code needs to be finalized
Current command - WIP: python3 main.py process waze-data --from_s3 --start_date 20-04-2020 --end_date 01-11-2020

