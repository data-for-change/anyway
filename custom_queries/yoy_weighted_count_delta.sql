CREATE OR REPLACE FUNCTION accidents_yoy_by_city(TEXT ARRAY)
RETURNS TABLE(city TEXT, year INTEGER, total_weighted_count NUMERIC, weighted_count_yoy_delta NUMERIC)
AS $$
	SELECT
		city,
		year,
		sum(weighted_count) AS total_weighted_count,
		sum(weighted_count) - lag(sum(weighted_count)) OVER (PARTITION BY city ORDER BY year) AS weighted_count_yoy_delta
	FROM lamas_marker_counts_by_city_year_and_severity
	WHERE city = ANY($1)
GROUP BY city, year
$$ LANGUAGE SQL;

-- Example invocation:
-- SELECT accidents_yoy_by_city(ARRAY[ 'רמת גן', 'חיפה' ]);
