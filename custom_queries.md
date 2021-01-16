# Custom Queries

This directory provides specialised views and queries.

* view\_lamas\_markers\_by\_city\_and\_date.sql: Provides following items
  * lamas\_markers\_by\_city\_and\_date view: Extracts city name, year, month and day of week from Lamas data. Note

    that Ihud Hatzala data is not supported here, since there's not consistent way to extract the city name by parsing

    the address fields etc.

  * lamas\_marker\_counts\_by\_city\_year\_and\_severity view: Tabulates the data in view\_lamas\_markers\_by\_city\_and\_date to give

    yearly total accident counts by city and severity

  * severity\_to\_weight stored procedure: Gives a weight by severity, so that severe accidents are given a higher weight in

    the total counts
* accidents\_yoy\_by\_city.sql: A stored procedure that tabulates the total weighted accident count for the

  specified cities and its year-on-year difference 

