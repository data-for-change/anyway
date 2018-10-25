CREATE OR REPLACE VIEW
lamas_markers_by_city_and_date AS
SELECT
	id,
	trim(both '* ' FROM (regexp_split_to_array(address, ',\s*'))[2]) AS city,
	accident_severity,
	CAST(date_part('year',  created) AS INTEGER) AS year,
	CAST(date_part('month', created) AS INTEGER) AS month,
	CAST(date_part('dow',   created) AS INTEGER) AS day_of_week
	FROM markers WHERE provider_code = 3 AND address ~ ',';

COMMENT ON COLUMN lamas_markers_by_city_and_date.day_of_week IS 'Sunday = 0 to Saturday = 6';

CREATE OR REPLACE FUNCTION severity_to_weight(INTEGER) RETURNS INTEGER
AS $$
BEGIN
	CASE ($1)
	WHEN 1 THEN -- Fatal
		RETURN 7;
	WHEN 2 THEN -- Serious injury
		RETURN 5;
	ELSE
		RETURN 1;
	END CASE;
END
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE VIEW
lamas_marker_counts_by_city_year_and_severity AS
	SELECT city ,year, accident_severity,
	COUNT(DISTINCT id) AS count,
	severity_to_weight(accident_severity) * COUNT(DISTINCT id) AS weighted_count
	FROM lamas_markers_by_city_and_date
	GROUP BY city, year, accident_severity;
