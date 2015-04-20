CREATE VIRTUAL TABLE marker_index USING rtree(
   id,        -- Integer primary key
   longitude,      -- Minimum and maximum longitude
   latitude       -- Minimum and maximum latitude
);