{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Imports"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 61,
   "metadata": {
    "ExecuteTime": {
     "end_time": "2020-08-20T21:56:51.244151Z",
     "start_time": "2020-08-20T21:56:47.505237Z"
    }
   },
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "from collections import defaultdict\n",
    "import os\n",
    "import math"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Load the data"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {
    "ExecuteTime": {
     "end_time": "2020-08-20T21:56:51.286975Z",
     "start_time": "2020-08-20T21:56:51.261518Z"
    }
   },
   "outputs": [],
   "source": [
    "PATH_TO_FILE = #the file with all the data (accidents, involved, injured, schools, etc...)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {},
   "outputs": [],
   "source": [
    "total_df = pd.read_csv(PATH_TO_FILE)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Add involved unique ID"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "metadata": {
    "ExecuteTime": {
     "end_time": "2020-08-20T21:59:46.947464Z",
     "start_time": "2020-08-20T21:59:46.891626Z"
    }
   },
   "outputs": [],
   "source": [
    "total_df['inv_unique_id'] = total_df['provider_and_id'].astype(str) + '_' +  total_df['involve_id'].astype(str) + '_' + total_df['accident_year'].astype(str)\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Add accident unique ID"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "metadata": {},
   "outputs": [],
   "source": [
    "total_df['accident_unique_id'] = total_df['provider_and_id'].astype(str) + '_' +  total_df['accident_year'].astype(str)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Add 'vehicle_or_pedastrian' field"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "metadata": {
    "ExecuteTime": {
     "end_time": "2020-08-20T21:59:49.440900Z",
     "start_time": "2020-08-20T21:59:47.340779Z"
    }
   },
   "outputs": [],
   "source": [
    "total_df['vehicle_or_pedastrian'] = total_df.apply(lambda x: x['involve_vehicle_type_hebrew'] if x['injured_type_hebrew'] != 'הולך רגל' else  x['injured_type_hebrew'],\n",
    "                                                  axis=1)\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### check vehicle_or_pedastrian"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "metadata": {
    "ExecuteTime": {
     "end_time": "2020-08-20T21:59:49.453251Z",
     "start_time": "2020-08-20T21:59:49.442971Z"
    }
   },
   "outputs": [
    {
     "data": {
      "text/plain": [
       "array(['הולך רגל', 'אופניים', 'אופניים חשמליים', 'קורקינט חשמלי'],\n",
       "      dtype=object)"
      ]
     },
     "execution_count": 11,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "total_df['vehicle_or_pedastrian'].unique()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 12,
   "metadata": {
    "ExecuteTime": {
     "end_time": "2020-08-20T21:59:49.461634Z",
     "start_time": "2020-08-20T21:59:49.455598Z"
    }
   },
   "outputs": [
    {
     "data": {
      "text/plain": [
       "(5831, 171)"
      ]
     },
     "execution_count": 12,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "total_df.shape"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### count schools"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 13,
   "metadata": {
    "ExecuteTime": {
     "end_time": "2020-08-20T21:59:49.483874Z",
     "start_time": "2020-08-20T21:59:49.475725Z"
    }
   },
   "outputs": [
    {
     "data": {
      "text/plain": [
       "1203"
      ]
     },
     "execution_count": 13,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "total_df.school_id.nunique()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Generate accidents per city files"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 19,
   "metadata": {},
   "outputs": [],
   "source": [
    "cities = [\n",
    "    \"מודיעין עילית\",\n",
    "    \"אבו גוש\",\n",
    "    \"אור יהודה\",\n",
    "    \"בחן\",\n",
    "    \"בית שמש\",\n",
    "    \"ביתר עילית\",\n",
    "    \"בן שמן (כפר נו\",\n",
    "    \"הוד השרון\",\n",
    "    \"חגי\",\n",
    "    \"חדרה\",\n",
    "    \"חולון\",\n",
    "    \"ירושלים\",\n",
    "    \"נצרת עילית\",\n",
    "    \"נתניה\",\n",
    "    \"קרית שמונה\",\n",
    "    \"שריד\",\n",
    "    \"תל אביב - יפו\",\n",
    "    \"תראבין א-צאנע(\",\n",
    "    \"אשדוד\",\n",
    "    \"הרצליה\",\n",
    "    \"חיפה\",\n",
    "    \"חשמונאים\",\n",
    "    \"טירה\",\n",
    "    \"כפר ביאליק\",\n",
    "    \"לוד\",\n",
    "    \"מתתיהו\",\n",
    "    \"קרית ביאליק\",\n",
    "    \"ראשון לציון\",\n",
    "    \"רחובות\",\n",
    "    \"רמלה\",\n",
    "    \"באר שבע\",\n",
    "    \"פתח תקווה\",\n",
    "    \"רמת גן\",\n",
    "    \"אלעד\",\n",
    "    \"בני ברק\"\n",
    "]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 20,
   "metadata": {},
   "outputs": [],
   "source": [
    "CITIES_DIRECTORY = # a directory in which all the folders representing cities are saved"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 21,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "שמירת כל התאונות בעיר מודיעין עילית\n",
      "שמירת כל התאונות בעיר אבו גוש\n",
      "שמירת כל התאונות בעיר אור יהודה\n",
      "שמירת כל התאונות בעיר בחן\n",
      "שמירת כל התאונות בעיר בית שמש\n",
      "שמירת כל התאונות בעיר ביתר עילית\n",
      "שמירת כל התאונות בעיר בן שמן (כפר נו\n",
      "שמירת כל התאונות בעיר הוד השרון\n",
      "שמירת כל התאונות בעיר חגי\n",
      "שמירת כל התאונות בעיר חדרה\n",
      "שמירת כל התאונות בעיר חולון\n",
      "שמירת כל התאונות בעיר ירושלים\n",
      "שמירת כל התאונות בעיר נצרת עילית\n",
      "שמירת כל התאונות בעיר נתניה\n",
      "שמירת כל התאונות בעיר קרית שמונה\n",
      "שמירת כל התאונות בעיר שריד\n",
      "שמירת כל התאונות בעיר תל אביב - יפו\n",
      "שמירת כל התאונות בעיר תראבין א-צאנע(\n",
      "שמירת כל התאונות בעיר אשדוד\n",
      "שמירת כל התאונות בעיר הרצליה\n",
      "שמירת כל התאונות בעיר חיפה\n",
      "שמירת כל התאונות בעיר חשמונאים\n",
      "שמירת כל התאונות בעיר טירה\n",
      "שמירת כל התאונות בעיר כפר ביאליק\n",
      "שמירת כל התאונות בעיר לוד\n",
      "שמירת כל התאונות בעיר מתתיהו\n",
      "שמירת כל התאונות בעיר קרית ביאליק\n",
      "שמירת כל התאונות בעיר ראשון לציון\n",
      "שמירת כל התאונות בעיר רחובות\n",
      "שמירת כל התאונות בעיר רמלה\n",
      "שמירת כל התאונות בעיר באר שבע\n",
      "שמירת כל התאונות בעיר פתח תקווה\n",
      "שמירת כל התאונות בעיר רמת גן\n",
      "שמירת כל התאונות בעיר אלעד\n",
      "שמירת כל התאונות בעיר בני ברק\n"
     ]
    }
   ],
   "source": [
    "for city in cities:\n",
    "    print(f\"שמירת כל התאונות בעיר {city}\")\n",
    "    city_data = total_df[total_df.school_yishuv_name == city]\n",
    "    city_path = f\"{CITIES_DIRECTORY}/{city}\"\n",
    "    if not os.path.exists(city_path):\n",
    "        os.makedirs(city_path)\n",
    "    file_path = f\"{city_path}/תאונות בסביבת בתי הספר.csv\"\n",
    "    city_data.to_csv(file_path, index=False, encoding='utf-8-sig')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Get injuries summary for each city"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 14,
   "metadata": {},
   "outputs": [],
   "source": [
    "KILLED_WEIGHT = 8\n",
    "SEVERE_WEIGHT = 5\n",
    "LIGHT_INJURED_WEIGHT = 1"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 15,
   "metadata": {},
   "outputs": [],
   "source": [
    "PRAT_KILLED_WEIGHT = 6600/7581\n",
    "PRAT_SEVERE_WEIGHT = 956/7581\n",
    "PRAT_LIGHT_WEIGHT = 25/7581"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 16,
   "metadata": {},
   "outputs": [],
   "source": [
    "def get_injuries_summary(key: str, val: str) -> dict:\n",
    "    relevant_data = total_df[getattr(total_df, key) == val]\n",
    "    killed = relevant_data.loc[relevant_data.injury_severity_hebrew == 'הרוג'].inv_unique_id.nunique()\n",
    "    severe_injured = relevant_data.loc[relevant_data.injury_severity_hebrew == 'פצוע קשה'].inv_unique_id.nunique()\n",
    "    light_injured = relevant_data.loc[relevant_data.injury_severity_hebrew == 'פצוע קל'].inv_unique_id.nunique()\n",
    "    total_accidents = relevant_data.accident_unique_id.nunique()\n",
    "    prat_score = (killed * PRAT_KILLED_WEIGHT + severe_injured * PRAT_SEVERE_WEIGHT  + light_injured * PRAT_LIGHT_WEIGHT) * (total_accidents)\n",
    "    heuristic_score = killed * KILLED_WEIGHT + severe_injured * SEVERE_WEIGHT + light_injured * LIGHT_INJURED_WEIGHT\n",
    "    return {\n",
    "        'פצועים קל': light_injured,\n",
    "        'פצועים קשה': severe_injured,\n",
    "        'הרוגים': killed,\n",
    "        'מספר התאונות': total_accidents,\n",
    "        'ציון פר\"ת': round(prat_score, 4),\n",
    "        'ציון יוריסטי': round(heuristic_score, 4)\n",
    "    }"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 25,
   "metadata": {},
   "outputs": [],
   "source": [
    "cities_injuries_summary = [{\n",
    "    'שם העיר': city,\n",
    "    **get_injuries_summary(key='school_yishuv_name', val=city)\n",
    "    } for city in cities]\n",
    "injuries_summary_df = pd.DataFrame(cities_injuries_summary)\n",
    "file_path = f\"{CITIES_DIRECTORY}/נפגעים בערים.csv\"\n",
    "injuries_summary_df.to_csv(file_path, index=False, encoding='utf-8-sig')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Get injuries summary per school"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 54,
   "metadata": {},
   "outputs": [],
   "source": [
    "def get_bounding_box(latitude, longitude, distance_in_km):\n",
    "    latitude = math.radians(latitude)\n",
    "    longitude = math.radians(longitude)\n",
    "\n",
    "    radius = 6371\n",
    "    # Radius of the parallel at given latitude\n",
    "    parallel_radius = radius * math.cos(latitude)\n",
    "\n",
    "    lat_min = latitude - distance_in_km / radius\n",
    "    lat_max = latitude + distance_in_km / radius\n",
    "    lon_min = longitude - distance_in_km / parallel_radius\n",
    "    lon_max = longitude + distance_in_km / parallel_radius\n",
    "    rad2deg = math.degrees\n",
    "\n",
    "    return rad2deg(lat_min), rad2deg(lon_min), rad2deg(lat_max), rad2deg(lon_max)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 29,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "חישוב פצועים בעיר מודיעין עילית\n",
      "חישוב פצועים בעיר אבו גוש\n",
      "חישוב פצועים בעיר אור יהודה\n",
      "חישוב פצועים בעיר בחן\n",
      "חישוב פצועים בעיר בית שמש\n",
      "חישוב פצועים בעיר ביתר עילית\n",
      "חישוב פצועים בעיר בן שמן (כפר נו\n",
      "חישוב פצועים בעיר הוד השרון\n",
      "חישוב פצועים בעיר חגי\n",
      "חישוב פצועים בעיר חדרה\n",
      "חישוב פצועים בעיר חולון\n",
      "חישוב פצועים בעיר ירושלים\n",
      "חישוב פצועים בעיר נצרת עילית\n",
      "חישוב פצועים בעיר נתניה\n",
      "חישוב פצועים בעיר קרית שמונה\n",
      "חישוב פצועים בעיר שריד\n",
      "חישוב פצועים בעיר תל אביב - יפו\n",
      "חישוב פצועים בעיר תראבין א-צאנע(\n",
      "חישוב פצועים בעיר אשדוד\n",
      "חישוב פצועים בעיר הרצליה\n",
      "חישוב פצועים בעיר חיפה\n",
      "חישוב פצועים בעיר חשמונאים\n",
      "חישוב פצועים בעיר טירה\n",
      "חישוב פצועים בעיר כפר ביאליק\n",
      "חישוב פצועים בעיר לוד\n",
      "חישוב פצועים בעיר מתתיהו\n",
      "חישוב פצועים בעיר קרית ביאליק\n",
      "חישוב פצועים בעיר ראשון לציון\n",
      "חישוב פצועים בעיר רחובות\n",
      "חישוב פצועים בעיר רמלה\n",
      "חישוב פצועים בעיר באר שבע\n",
      "חישוב פצועים בעיר פתח תקווה\n",
      "חישוב פצועים בעיר רמת גן\n",
      "חישוב פצועים בעיר אלעד\n",
      "חישוב פצועים בעיר בני ברק\n"
     ]
    }
   ],
   "source": [
    "for city in cities:\n",
    "    print(f\"חישוב פצועים בעיר {city}\")\n",
    "    city_schools = []\n",
    "    city_schools_ids = total_df[total_df.school_yishuv_name == city].school_id.unique()\n",
    "    for school_id in city_schools_ids:\n",
    "        school_data = total_df[total_df.school_id == school_id]\n",
    "        # using the last row to get the most updated data\n",
    "        school_name = school_data.iloc[-1].school_name\n",
    "        school_long, school_lat = school_data.iloc[-1].longitude, \\\n",
    "            school_data.iloc[-1].latitude\n",
    "        lat_min, lon_min, lat_max, lon_max = get_bounding_box(latitude=school_lat, longitude=school_long,\n",
    "        distance_in_km=0.5)\n",
    "        baseX = lon_min\n",
    "        baseY = lat_min\n",
    "        distanceX = lon_max\n",
    "        distanceY = lat_max\n",
    "        school_json = {\n",
    "            'סמל בית הספר': school_id,\n",
    "            'שם בית הספר': school_name,\n",
    "            **get_injuries_summary(key='school_id', val=school_id),\n",
    "            '(x1, y1)': (baseX, baseY),\n",
    "            '(x1, y2)': (baseX, distanceY),\n",
    "            '(x2, y2)': (distanceX, distanceY),\n",
    "            '(x2, y1)': (distanceX, baseY)\n",
    "        }\n",
    "        city_schools.append(school_json)\n",
    "    city_path = f\"{CITIES_DIRECTORY}/{city}\"\n",
    "    if not os.path.exists(city_path):\n",
    "        os.makedirs(city_path)\n",
    "    file_path = f\"{city_path}/נפגעים בבתי הספר.csv\"\n",
    "    pd.DataFrame(city_schools).to_csv(file_path, index=False, encoding='utf-8-sig')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Get injured with POINT(longitude, latitude)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 42,
   "metadata": {},
   "outputs": [],
   "source": [
    "injured_with_points = total_df.copy()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 43,
   "metadata": {},
   "outputs": [],
   "source": [
    "injured_with_points['WKT'] = injured_with_points.apply(lambda row: f'POINT ({row.longitude} {row.latitude})', axis=1)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 44,
   "metadata": {},
   "outputs": [],
   "source": [
    "injured_with_points = injured_with_points[['WKT', 'vehicle_or_pedastrian', 'injury_severity_hebrew', 'age_group_hebrew', 'longitude', 'latitude', 'accident_timestamp']]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 45,
   "metadata": {},
   "outputs": [],
   "source": [
    "# otherwise excel auto-detects this column as \"Date\" column\n",
    "injured_with_points.age_group_hebrew = injured_with_points.age_group_hebrew.apply(lambda val: f' {val}')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 46,
   "metadata": {},
   "outputs": [],
   "source": [
    "injured_with_points.rename(columns={\n",
    "    'vehicle_or_pedastrian': 'סוג נפגע',\n",
    "    'injury_severity_hebrew': 'חומרת פגיעה',\n",
    "    'age_group_hebrew': 'קבוצת גיל',\n",
    "    'accident_timestamp': 'תאריך התאונה'\n",
    "}, inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 48,
   "metadata": {},
   "outputs": [],
   "source": [
    "injured_with_points.to_csv('{YOUR_PATH}/נפגעים עם מיקום.csv',\n",
    "index=False, encoding='utf-8-sig')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Get schools with polygons"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 50,
   "metadata": {},
   "outputs": [],
   "source": [
    "ids = total_df.school_id.unique()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 57,
   "metadata": {},
   "outputs": [],
   "source": [
    "schools_with_polygons = []\n",
    "\n",
    "for id_ in ids:\n",
    "    school_data = total_df[total_df.school_id == id_]\n",
    "    school_record = school_data.iloc[-1] # get the last record of the school\n",
    "    # to get the most updated data\n",
    "    school_long, school_lat = school_record.school_longitude, school_record.school_latitude\n",
    "    lat_min, lon_min, lat_max, lon_max = get_bounding_box(latitude=school_lat, longitude=school_long, \n",
    "    distance_in_km=0.5)\n",
    "    baseX = lon_min\n",
    "    baseY = lat_min\n",
    "    distanceX = lon_max\n",
    "    distanceY = lat_max\n",
    "    pol_str = \"POLYGON (({0} {1}, {0} {3}, {2} {3}, {2} {1}, {0} {1}))\".format(\n",
    "        baseX, baseY, distanceX, distanceY\n",
    "    )\n",
    "    schools_with_polygons.append({\n",
    "      'WKT': pol_str,\n",
    "      'שם מוסד': school_record.school_name,\n",
    "      'ישוב': school_record.school_yishuv_name,\n",
    "      'longitude': school_long,\n",
    "      'latitude': school_lat\n",
    "    })\n",
    "\n",
    "schools_with_polygons_df = pd.DataFrame(schools_with_polygons)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 59,
   "metadata": {},
   "outputs": [],
   "source": [
    "schools_with_polygons_df.to_csv('{YOUR_PATH}/בתי ספר עם פוליגונים.csv',\n",
    "index=False, encoding='utf-8-sig')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "hide_input": false,
  "kernelspec": {
   "display_name": "Python 3.8.10 ('venv': venv)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.10"
  },
  "toc": {
   "base_numbering": 1,
   "nav_menu": {},
   "number_sections": true,
   "sideBar": true,
   "skip_h1_title": false,
   "title_cell": "Table of Contents",
   "title_sidebar": "Contents",
   "toc_cell": true,
   "toc_position": {
    "height": "calc(100% - 180px)",
    "left": "10px",
    "top": "150px",
    "width": "339px"
   },
   "toc_section_display": true,
   "toc_window_display": true
  },
  "vscode": {
   "interpreter": {
    "hash": "9c03cf2cb83db7534e4967cd34bf82d9c9704dddd07f7aa50cb8259b513d1c3c"
   }
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
