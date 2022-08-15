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
   "execution_count": 35,
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
    "import matplotlib.pyplot as plt\n",
    "from shapely.geometry import Point, Polygon\n",
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
   "execution_count": 36,
   "metadata": {
    "ExecuteTime": {
     "end_time": "2020-08-20T21:56:51.286975Z",
     "start_time": "2020-08-20T21:56:51.261518Z"
    }
   },
   "outputs": [],
   "source": [
    "PATH_TO_FILE = '/anyway/static/data/schools/total_15_08_22_first_100.csv'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 37,
   "metadata": {},
   "outputs": [],
   "source": [
    "total_df = pd.read_csv(PATH_TO_FILE)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 38,
   "metadata": {},
   "outputs": [],
   "source": [
    "total_df['accident_timestamp'] = pd.to_datetime(total_df.accident_timestamp.values)"
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
   "execution_count": 39,
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
   "execution_count": 22,
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
   "execution_count": 40,
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
   "execution_count": 7,
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
       "array(['אופניים חשמליים', 'הולך רגל', 'אופניים', 'קורקינט חשמלי'],\n",
       "      dtype=object)"
      ]
     },
     "execution_count": 7,
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
   "execution_count": 8,
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
       "(515, 170)"
      ]
     },
     "execution_count": 8,
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
   "execution_count": 31,
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
       "67"
      ]
     },
     "execution_count": 31,
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
   "execution_count": 42,
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
   "execution_count": 13,
   "metadata": {},
   "outputs": [],
   "source": [
    "CITIES_DIRECTORY = '/anyway/static/data/schools/2022'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 19,
   "metadata": {},
   "outputs": [],
   "source": [
    "for city in cities:\n",
    "    city_data = total_df[total_df.school_yishuv_name == city]\n",
    "    city_path = f\"{CITIES_DIRECTORY}/{city}\"\n",
    "    if not os.path.exists(city_path):\n",
    "        os.makedirs(city_path)\n",
    "    file_path = f\"{city_path}/תאונות.csv\"\n",
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
   "execution_count": 20,
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
   "execution_count": 29,
   "metadata": {},
   "outputs": [],
   "source": [
    "def get_injuries_summary(key: str, val: str) -> dict:\n",
    "    relevant_data = total_df[getattr(total_df, key) == val]\n",
    "    killed = relevant_data.loc[relevant_data.injury_severity_hebrew == 'הרוג'].inv_unique_id.nunique()\n",
    "    severe_injured = relevant_data.loc[relevant_data.injury_severity_hebrew == 'פצוע קשה'].inv_unique_id.nunique()\n",
    "    light_injured = relevant_data.loc[relevant_data.injury_severity_hebrew == 'פצוע קל'].inv_unique_id.nunique()\n",
    "    total_accidents = relevant_data.accident_unique_id.nunique()\n",
    "    score = (killed * KILLED_WEIGHT + severe_injured * SEVERE_WEIGHT  + light_injured * LIGHT_INJURED_WEIGHT) * (total_accidents)\n",
    "    return {\n",
    "        'פצועים קל': light_injured,\n",
    "        'פצועים קשה': severe_injured,\n",
    "        'הרוגים': killed,\n",
    "        'מספר התאונות': total_accidents,\n",
    "        'ציון משוקלל': score\n",
    "    }"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 30,
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
   "execution_count": 33,
   "metadata": {},
   "outputs": [],
   "source": [
    "for city in cities:\n",
    "    city_schools = []\n",
    "    city_schools_ids = total_df[total_df.school_yishuv_name == city].school_id.unique()\n",
    "    for school_id in city_schools_ids:\n",
    "        school_data = total_df[total_df.school_id == school_id]\n",
    "        school_name = school_data.iloc[0].school_name\n",
    "        school_json = {\n",
    "            'שם בית הספר': school_name,\n",
    "            **get_injuries_summary(key='school_id', val=school_id)\n",
    "        }\n",
    "        city_schools.append(school_json)\n",
    "    city_path = f\"{CITIES_DIRECTORY}/{city}\"\n",
    "    if not os.path.exists(city_path):\n",
    "        os.makedirs(city_path)\n",
    "    file_path = f\"{city_path}/נפגעים בבתי הספר.csv\"\n",
    "    pd.DataFrame(city_schools).to_csv(file_path, index=False, encoding='utf-8-sig')"
   ]
  }
 ],
 "metadata": {
  "hide_input": false,
  "kernelspec": {
   "display_name": "Python 3.8.10 ('venv3')",
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
    "hash": "3a0b432b6b1f1127c32676ebc2a6bff7927bbebfad79e0b690644c98f0f4a373"
   }
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
