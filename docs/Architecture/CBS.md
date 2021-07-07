## Current Processes

### CBS: pulls data from email to s3
- **Environment Variables**: MAILPASS, MAILUSER
- **Relevant input**: input emails from CBS containing zip files
- **Relevant output**: unzipped CBS files saved in S3
- **Relevant Storage directory**: S3 -> Bucket: anyway-cbs
- **command**: `python3 main.py scripts importemail`
- **Scheduling**: Nowadays runs in Jenkins once a week

### CBS: pulls data from s3, processes cbs data and pushes it to CBS tables
Environment Variables: AWS_ACCESS_KEY, AWS_SECRET_KEY
- **Relevant input**: S3 -> Bucket: anyway-cbs
- **Relevant output**: DB Tables: markers, vehicles, involved, vehicles_hebrew, involved_hebrew, vehicles_hebrew, involved_markers_hebrew, vehicles_markers_hebrew, All CBS Dictionary Tables
- **command**: `python3 main.py process cbs --load_start_year 2021 --source s3`
- **Scheduling**: to be scheduled
- **Future**: scheduling this process, making sure this process is triggered once new data is inserted to s3

## Future Tasks:

### BE Team
1. Table Structure: Current tables are Legacy Tables - based on tables built for our Map
   - We might (not necessarily) want to create new tables OR modify current ones
     Note: We need to be compatible with current APIs OR create new tables
   - Star/Snowflake schema exists but can be improved
   - Pick indices wisely (e.g. avoid large text fields)
   - Possible Minor Affect: Table Size and Tables Index will be reduced - [see current sizes](https://app.redash.io/hasadna/queries/833839/source)
2. Adding Data Documentation:
   - Best Practices / Tools
   - Separate calculated fields and original CBS fields
   - Spreadsheet with [Definitions of CBS Fields](https://docs.google.com/spreadsheets/d/1qaVV7NKXVYNmnxKZ4he2MKZDAjWPHiHfq-U5dcNZM5k)
3. Translation Dictionaries:
    - Validation when inserting data - CBS dictionaries are mostly backwards compatible - but not always
   - Do we want to create our own dictionaries?
   - Auto insertion of new values
   - Failure/Alert when there is no backwards compatibility of CBS Data in loading time
   - Using our DB dictionaries when building infographics data (rather than re-creating dictionaries in backend_constants.py file)
4. Data Cleaning and Enrichment Pipeline:
    - Handling Missing Values
    - Adding calculated fields  
    - CBS Accidents Duplicates across years (remove early year data - minor issue - [see query here](https://app.redash.io/hasadna/queries/834111/source))
5. Hebrew Tables Creation
    - Nowadays used by infographics utils and by data team (exported to csvs or [using redash](https://app.redash.io/hasadna))
    - Nowadays creation consumes a lot of memory - since the whole table is loaded to DB - this needs to be improved (perhaps use views / materialized views instead of a table?)
    - Add process creating csv files for the Data Team to work with
5. Data Loading - Separate to multiple stages - see [CBS ETL in process refactoring](https://docs.google.com/document/d/1LirLg1u7B3ekvcjetj6LhVExijVqctMZ83fJHUYzlrI/edit?usp=sharing)
   Make sure data is not loaded multiple times and that no duplicates are created
   - Current Flow: email -> s3 -> updated tables
     email -> s3: can be scheduled once a week / even a day
     s3 -> Data Tables: Needs to be scheduled when both accident type 1 and accident type 3 of that months are in s3
     Explanation: Nowadays we pull the last data from last 2 emails and insert data to s3 (after deleting previous data), we need to pull only emails we didn't save to s3 - hence track on the emails we already read and not re-insert them.
     Optional: We can add CBS data versioning in s3 - right now we delete old data and insert new one.
6. API + Documentation (Swagger) - 
   - CBS Raw DATA AND/OR CBS Processed Data
7. CBS Localization
   - Do we want to enhance Localization Infrastructure at this stage? 
   - Relevant work: Ziv’s work in code, Dvir’s code for adding translations, Yaron’s experience with localization
8. Infographics Data Related Tasks (might be done at a later stage):
   - Data enrichment using additional aggregation tables AND/OR columns for Infographics tasks

#### Important Notes
- Make sure we use our PostGIS’s abilities for current/future geographic queries

#### Relevant Work:
- [Dvir's value_mapping branch](https://github.com/dvirein/anyway-backend/tree/value_mapping)
- [Current Data Base models and methods](https://github.com/hasadna/anyway/blob/dev/anyway/models.py)
- [Current CBS Data Processing Code](https://github.com/hasadna/anyway/blob/dev/anyway/parsers/cbs/executor.py)
- [Current tables usage in infographics utils](https://github.com/hasadna/anyway/blob/dev/anyway/infographics_utils.py)
- [Dictionaries that are constants in infographics utils](https://github.com/hasadna/anyway/blob/dev/anyway/infographics_dictionaries.py)

### Data Team
1. Data Exploration
   - Find discrepancies in location - GPS vs CBS Locations
   - Explore trends, Create infographics
