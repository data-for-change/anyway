## Current Processes
No Processes

## Future Tasks:

### BE Team
1. Add OSM DB schema to our DB (Israel only)
2. Map GPS -> OSM Location (Polygon/Polyline) (Use Data Team findings)
3. Extract accidents in a specific OSM Location (Polygon/Polyline) (Simple PostGIS query)
4. Replace current CBS Location to OSM Location in system (interurban and/or urban):
   - Change NewsFlash location extraction
   - When creating Infographics Data - make sure OSM Location (using geographic query) is used

#### Relevant Work:
- [See Vickey's Work - starting page 2](https://docs.google.com/document/d/1CHKiw-yI1Yl5eZogSVTtlzdrvsx53zE-sENaZwEqO7k)

### Data Team
1. Create a function that receives a GPS and returns:
   - Interurban: Relevant Road Segments Polygons/Polylines
   - Urban: Relevant street Polygons/Polylines AND city Polygons/Polylines
