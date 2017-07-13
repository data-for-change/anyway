Custom Queries
==============

This directory provides specialised views and queries. Those are written in the dialect of PostgreSQL 9
and are not expected to work on Sqlite.

* view_lamas_markers_by_city_and_date.sql: Provides following items
  * lamas_markers_by_city_and_date view: Extracts city name, year, month and day of week from Lamas data. Note
that Ihud Hatzala data is not supported here, since there's not consistent way to extract the city name by parsing
the address fields etc.
  * lamas_marker_counts_by_city_year_and_severity view: Tabulates the data in view_lamas_markers_by_city_and_date to give
yearly total accident counts by city and severity
  * severity_to_weight stored procedure: Gives a weight by severity, so that severe accidents are given a higher weight in
the total counts
* accidents_yoy_by_city.sql: A stored procedure that tabulates the total weighted accident count for the
specified cities and its year-on-year difference 