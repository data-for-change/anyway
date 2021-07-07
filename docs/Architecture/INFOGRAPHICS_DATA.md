## Current Processes

## Data created in News Flash process
- **Relevant output DB Tables**: infographics_data_cache, news_flash
- **command**: `python3 main.py process news-flash`
- **Scheduling**: Nowadays runs in Jenkins every 30 minutes
See NEWS_FLASH.md for more details

## Recreate infographics cache table
- **command**: `python3 main.py process infographics_data_cache --update --no-info`
- **Relevant output DB Tables**: infographics_data_cache, infographics_data_cache_temp

## Future Tasks:

### BE Team

1. Architecture Planning:
   - Create aggregation tables for infographics data, if needed
   - Possibility: Query data in location geographically rather than categorically (depends on OSM tasks)
   - Rule Based - [see Assaf’s work here](https://github.com/hasadna/anyway/pull/1737)
   - Possible: Recommender System
3. Documentation including swagger
4. Possible: Infographics Templates (Bar Graph, )
5. Adding Urban Data to API
6. Add additional widgets

#### Important Notes
- Make sure we use our PostGIS’s abilities for geographic queries
- Align with CBS dictionaries:
  when creating a new infographic that use CBS data - use existing CBS dictionaries rather than duplicating them in code

### Data Team
1. Create additional widgets
