## Current Processes

### Waze: pulls data from waze, saves it in Google Cloud Storage
- **Scheduling**: runs in Google Cloud (not in Jenkins) - runs every 5 minutes

### Waze: pulls data from Google Cloud Storage OR from Waze News Feed - Stores in our DB (WIP)
- **Environment Variables**: GOOGLE_LOGIN_CLIENT_ID, GOOGLE_LOGIN_CLIENT_SECRET
- **Relevant DB Tables**: waze_traffic_jams, waze_alerts
- **Current command - WIP**: python3 main.py process waze-data --from_s3 --start_date 20-04-2020 --end_date 01-11-2020

## Future Tasks:

### BE Team
1. Table Structure:
   - Go over waze accidents data feed
   - Examine current table structure - add/modify if needed
2. Load data from waze news feed to our DB
   - jams
   - alerts
3. Possible: Back-fill - waze data - from Google Cloud Storage
4. Either Transfer GCP process to Jenkins and Load current data to s3 and OR Delete GCP process if not needed
5. Possible: Create infographics data for each waze accident
6. Possible: improve news flash GPS using Waze Data

#### Important Notes
- Stages 1,2,3 are almost done - read carefully the code of `python3 main.py process waze-data` before starting this task
