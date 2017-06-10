CREATE OR REPLACE VIEW
lamas_markers_by_city_and_date AS
SELECT
	id,
	trim(both '* ' FROM (regexp_split_to_array(address, ',\s*'))[2]) AS city,
	severity,
	CAST(date_part('year',  created) AS INTEGER) AS year,
	CAST(date_part('month', created) AS INTEGER) AS month,
	CAST(date_part('dow',   created) AS INTEGER) AS day_of_week
	FROM markers WHERE provider_code = 3 AND address ~ ',';

COMMENT ON COLUMN lamas_markers_by_city_and_date.day_of_week IS 'Sunday = 0 to Saturday = 6';

CREATE OR REPLACE VIEW
lamas_marker_counts_by_city_year_and_severity AS
	SELECT city ,year, severity, COUNT(DISTINCT id) FROM lamas_markers_by_city_and_date
	GROUP BY city, year, severity;
