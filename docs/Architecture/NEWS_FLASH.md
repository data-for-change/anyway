## Current Processes

## News Flash:
Extracts data from source, processes it and pushes it to NewsFlash table
In Addition - the InfographicsDataCache is filled with relevant data of the newsflash

- **Environment Variables**: GOOGLE_MAPS_KEY (for google's location API)
- **Additional environment variables for the each source**:
   * Ynet Newsflashes. Additional Environment Variables: None
   * Walla Newsflashes. Additional Environment Variables: None
   * Twitter - Adds tweets to NewsFlash table. Additional Environment Variables: TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
- **Relevant input DB Tables**: CBS Tables for location extraction, Future: Waze Table
- **Relevant output DB Tables**: news_flash, infographics_data_cache
- **command**: `python3 main.py process news-flash`
- **Scheduling**: Nowadays runs in Jenkins every 30 minutes


## Future Tasks:

### BE Team
1. Table structure:
   - Create Star/Snowflake schema
     For example, separate NewsFlash contains the newsflash data itself from NewsFlashLocation table, separate source table, add text features table - pedestrian, bicycle, etc)
   - Optional: Add postgis abilities to table (using GPS point) 
2. Separate to multiple stages - see [News Flash in process refactoring](https://docs.google.com/document/d/1LirLg1u7B3ekvcjetj6LhVExijVqctMZ83fJHUYzlrI/edit?usp=sharing)
3. Adding Urban Data to API
4. Improved location extraction using Algorithms / Waze / other sources 
   - Urban
   - Interurban