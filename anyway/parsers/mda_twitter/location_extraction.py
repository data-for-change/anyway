# coding=utf-8
# Imports the Google Cloud client library
import logging
import string
import sys

import html
import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from google.cloud import language
from google.cloud import translate
from google.cloud.language import enums
from google.cloud.language import types


def get_ner_location_of_text(text):
    no_random_road_groups = []
    no_hospital_loc_groups = []
    loc_groups = []
    loc_entities = []
    loc_entities_indices = []
    loc_entities_word_indices = []
    biggest_group_index = -1
    reference_grouping = False

    # Instantiates the clients
    client = language.LanguageServiceClient()
    translate_client = translate.Client()

    # Translate
    result = translate_client.translate(text, target_language='en', source_language='iw')
    translated_text = result['translatedText']
    translated_text = html.unescape(translated_text)

    # Pre-processing - from what I saw only the first line has the location
    translated_text = list(filter(None, translated_text.split('.')))[0]

    # Analyze (Named Entity Recognition)
    document = types.Document(content=translated_text, type=enums.Document.Type.PLAIN_TEXT)
    response = client.analyze_entities(document=document)

    # Getting the location entities and their indices in the text and adding them to a list
    translated_text_word_split = list(filter(None, translated_text.split(' ')))
    for entity in response.entities:
        if entity.type == enums.Entity.Type.LOCATION:
            if ' ' in entity.name:
                for item in list(filter(None, entity.name.split(' '))):
                    loc_entities.append(item)
                    loc_entities_indices.append(translated_text.index(entity.name) + entity.name.index(item))
            else:
                loc_entities.append(entity.name)
                loc_entities_indices.append(translated_text.index(entity.name))
                # In case there is a reference to a previous location
            if 'city' == entity.name.lower() or 'town' == entity.name.lower() or 'village' == entity.name.lower() or \
                    'junction' == entity.name.lower() or 'interchange' == entity.name.lower() or \
                    'intersect' == entity.name.lower() or 'street' == entity.name.lower():
                reference_grouping = True

    # Sort entities by appearing order in the string
    loc_entities = [x for _, x in sorted(zip(loc_entities_indices, loc_entities))]
    loc_entities_new = []
    for item in loc_entities:
        loc_entities_word_indices.append(
            [idx for idx, s in enumerate(translated_text_word_split) if item in s][loc_entities_new.count(item)])
        loc_entities_new.append(item)
    loc_entities = loc_entities_new

    # Location grouping - takes the largest group of words indicating location based on distance between groups
    if len(loc_entities) >= 1:
        diff = [loc_entities_word_indices[i + 1] - loc_entities_word_indices[i] for i in
                range(len(loc_entities_word_indices) - 1)]
        if diff and max(diff) > 5:  # Distance is greater than 5 words
            avg = sum(diff) / len(diff)
            loc_groups = [[loc_entities_word_indices[0]]]
            for x in loc_entities_word_indices[1:]:
                if x - loc_groups[-1][-1] < avg:
                    loc_groups[-1].append(x)
                else:
                    loc_groups.append([x])

            # 'road' alone is recognised as a location, so if road is alone in the group, ignore it
            no_random_road_groups = [group for group in loc_groups
                                     if
                                     not (len(group) == 1 and 'road' == translated_text_word_split[group[0]].lower())]

            # We are not interested in the hospital location, unless the city isn't mentioned elsewhere
            no_hospital_loc_groups = [group for group in no_random_road_groups
                                      if not
                                      any('hospital' in translated_text_word_split[item].lower() for item in group)]
            bounds_loc_groups = [i[-1] - i[0] for ind, i in enumerate(no_hospital_loc_groups)]
            biggest_group_index = bounds_loc_groups.index(max(bounds_loc_groups))

            # Entities of the largest group
            loc_entities = [translated_text_word_split[item] for item in no_hospital_loc_groups[biggest_group_index]]

        # Getting the full string from the text indicating the location and not just entities
        translated_location = translated_text[
                              translated_text.index(loc_entities[0]):translated_text.index(loc_entities[-1]) + len(
                                  loc_entities[-1])]

        # If there was a 'the' before the string, add it
        if translated_text[translated_text.index(loc_entities[0]) - 4:translated_text.index(loc_entities[0])].lower() \
                == 'the ':
            translated_location = translated_text[
                                  translated_text.index(loc_entities[0]) - 4:translated_text.index(
                                      loc_entities[-1]) + len(
                                      loc_entities[-1])]

        # If a location without name is in the beginning of the string, add the previous word
        if translated_location.lower().startswith('street') or translated_location.lower().startswith('interchange') \
                or translated_location.lower().startswith('village') or translated_location.lower().startswith('town') \
                or translated_location.lower().startswith('city') or translated_location.lower().startswith(
            'intersection') \
                or translated_location.lower().startswith('junction'):
            translated_location = translated_text_word_split[translated_text_word_split.index(loc_entities[0]) - 1] \
                                  + ' ' + translated_location
            reference_grouping = False

        # Trying to solve the reference in case there is another group - first without the hospital group
        if reference_grouping and len(no_hospital_loc_groups) >= 2:
            previous = sys.maxsize
            if biggest_group_index > 0:
                previous = no_hospital_loc_groups[biggest_group_index][0] - \
                           no_hospital_loc_groups[biggest_group_index - 1][-1]

            # Take the previous group, and from there, the last word, closest road to current group
            if previous != sys.maxsize:
                text_to_replace = translated_text_word_split[
                    no_hospital_loc_groups[biggest_group_index - 1][-1]]
                if len(no_hospital_loc_groups[biggest_group_index - 1]) > 1:
                    last = no_hospital_loc_groups[biggest_group_index - 1][-1]
                    for index, val in enumerate(loc_groups[biggest_group_index - 1][::-1][1:]):
                        if last - val == 1:
                            text_to_replace = translated_text_word_split[
                                                  no_hospital_loc_groups[biggest_group_index - 1][
                                                      -2 - index]] + ' ' + text_to_replace
                            last = val
                        else:
                            break
                translated_location = translated_location.replace(
                    'the junction', text_to_replace).replace(
                    'the intersect', text_to_replace).replace(
                    'the interchange', text_to_replace).replace(
                    'the street', text_to_replace).replace(
                    'the city', text_to_replace).replace(
                    'the town', text_to_replace).replace(
                    'the village', text_to_replace)

        # Without hospital there weren't enough groups, so use it as well
        elif reference_grouping and len(no_random_road_groups) >= 2:
            previous = sys.maxsize
            bounds_loc_groups = [i[-1] - i[0] for ind, i in enumerate(no_random_road_groups)]
            biggest_group_index = bounds_loc_groups.index(max(bounds_loc_groups))
            if biggest_group_index > 0:
                previous = no_random_road_groups[biggest_group_index][0] - \
                           no_random_road_groups[biggest_group_index - 1][-1]

            # Take the previous group, and from there, the last word, closest road to current group
            if previous != sys.maxsize and 'hospital' not in \
                    translated_text_word_split[no_random_road_groups[biggest_group_index - 1][-1]].lower():
                text_to_replace = translated_text_word_split[
                    no_random_road_groups[biggest_group_index - 1][-1]]
                if len(no_random_road_groups[biggest_group_index - 1]) > 1:
                    last = no_random_road_groups[biggest_group_index - 1][-1]
                    for index, val in enumerate(loc_groups[biggest_group_index - 1][::-1][1:]):
                        if last - val == 1:
                            text_to_replace = translated_text_word_split[
                                                  no_random_road_groups[biggest_group_index - 1][
                                                      -2 - index]] + ' ' + text_to_replace
                            last = val
                        else:
                            break
                translated_location = translated_location.replace(
                    'the junction', text_to_replace).replace(
                    'the intersect', text_to_replace).replace(
                    'the interchange', text_to_replace).replace(
                    'the street', text_to_replace).replace(
                    'the city', text_to_replace).replace(
                    'the town', text_to_replace).replace(
                    'the village', text_to_replace)

    elif len(loc_entities) == 1:
        translated_location = loc_entities

        # If there was 'the' before the entity, add it
        if translated_text[translated_text.index(loc_entities[0]) - 4:translated_text.index(loc_entities[0])].lower() \
                == 'the ':
            translated_location = translated_text[
                                  translated_text.index(loc_entities[0]):translated_text.index(loc_entities[0]) + len(
                                      loc_entities[0])]

        # If the entity is a location without name, add previous word
        if translated_location.lower().startswith('street') or translated_location.lower().startswith('interchange') \
                or translated_location.lower().startswith('village') or translated_location.lower().startswith('town') \
                or translated_location.lower().startswith('city') or translated_location.lower().startswith(
            'intersection') \
                or translated_location.lower().startswith('junction'):
            translated_location = translated_text_word_split[translated_text_word_split.index(loc_entities[0]) - 1] \
                                  + ' ' + translated_location

    else:
        translated_location = ''

    # Processing the location
    translated_location = translated_location.strip()
    if translated_location != '' and ',' == translated_location[-1]:
        translated_location = translated_location[:-1]
    translated_location = html.unescape(translated_location)
    if translated_location == '':
        translated_location = 'failed to extract location'
    logging.info('location found: ' + translated_location)
    return translated_location


def remove_text_inside_brackets(text, brackets="()[]{}"):
    count = [0] * (len(brackets) // 2)  # count open/close brackets
    saved_chars = []
    for character in text:
        for i, b in enumerate(brackets):
            if character == b:  # found bracket
                kind, is_close = divmod(i, 2)
                count[kind] += (-1) ** is_close  # `+1`: open, `-1`: close
                if count[kind] < 0:  # unbalanced bracket
                    count[kind] = 0  # keep it
                else:  # found bracket to remove
                    break
        else:  # character is not a [balanced] bracket
            if not any(count):  # outside brackets
                saved_chars.append(character)
    return ''.join(saved_chars)


def preprocess_text(text, get_first=False):
    table_no_dot = str.maketrans(string.punctuation.replace('.', ''),
                                 ' ' * len(string.punctuation.replace('.', '')))  # remove punctuation, without '.'
    table = str.maketrans(string.punctuation, ' ' * len(string.punctuation))  # remove punctuation
    if type(text) != str:
        text = str(text)
    if any(key in text for key in '()[]{}'):
        text = remove_text_inside_brackets(text)
    if get_first:
        return (' '.join(text.translate(table_no_dot).split())).strip().split('.')[
            0]  # remove multiple whitespaces and return first sentence
    else:
        return (' '.join(text.translate(table).split())).strip()  # remove multiple whitespaces


def preprocess_intersection(intersections):
    intersections = intersections.replace('יישוב', '')
    intersections = intersections.replace('ישוב', '')
    intersections = intersections.replace('מושבה', '')
    intersections = intersections.replace('מושב', '')
    intersections = intersections.replace('צומת ל', '')
    intersections = intersections.replace('צומת', '')
    intersections = intersections.replace('מחלף', '')
    intersections = intersections.replace('כניסה ל', '')
    intersections = intersections.strip()
    return intersections


def process_streets_table(addresses_df):
    streets = pd.DataFrame(addresses_df.drop(
        ['road1', 'road2', 'non_urban_intersection_hebrew'], axis=1))
    streets.yishuv_name = streets.yishuv_name.astype(str)
    streets.street1_hebrew = streets.street1_hebrew.astype(str)
    streets.street2_hebrew = streets.street2_hebrew.astype(str)
    streets['city'] = streets.yishuv_name
    streets['street1'] = streets.street1_hebrew
    streets['street2'] = streets.street2_hebrew
    streets.city = streets.city.apply(preprocess_text)
    streets.street1 = streets.street1.apply(preprocess_text)
    streets.street2 = streets.street2.apply(preprocess_text)
    streets = streets[(streets.city != streets.street1) & (streets.city != streets.street2)
                      & (streets.city != 'NaN')]
    streets = streets.replace('NaN', np.nan)
    streets = streets.dropna(how='all')
    streets = streets.drop_duplicates()
    streets = streets.replace(np.nan, 'NaN')
    return streets


def process_roads_table(addresses_df):
    roads = pd.DataFrame(addresses_df[['road1', 'road2', 'non_urban_intersection_hebrew']])
    roads.road1 = roads.road1.astype(str)
    roads.road2 = roads.road2.astype(str)
    roads.non_urban_intersection_hebrew = roads.non_urban_intersection_hebrew.astype(str)
    roads['first_road'] = roads.road1
    roads['second_road'] = roads.road2
    roads['intersection'] = roads.non_urban_intersection_hebrew
    roads.first_road = 'כביש ' + roads.first_road
    roads.second_road = 'כביש ' + roads.second_road
    roads.loc[roads.first_road == 'כביש -1'] = np.nan
    roads.loc[roads.second_road == 'כביש -1'] = np.nan
    roads.loc[roads.intersection == 'צומת'] = np.nan
    roads.loc[roads.intersection == 'מחלף'] = np.nan
    roads.intersection = roads.intersection.apply(preprocess_text)
    roads.intersection = roads.intersection.apply(preprocess_intersection)
    roads = roads.replace('nan', np.nan)
    roads = roads.dropna(how='all')
    roads = roads.drop_duplicates()
    roads = roads.replace(np.nan, 'NaN')
    return roads


def first_init():
    addresses_df = pd.read_excel('anyway/parsers/news_flash/Addresses_new.xlsx', sheet_name='Sheet1')
    addresses_df = addresses_df.fillna('NaN')
    streets = process_streets_table(addresses_df)
    roads = process_roads_table(addresses_df)
    cities = streets.city.drop_duplicates()
    streets.to_excel('anyway/parsers/news_flash/streets.xlsx')
    roads.to_excel('anyway/parsers/news_flash/roads.xlsx')
    cities.to_excel('anyway/parsers/news_flash/cities.xlsx')


def preprocess_urban_text(text, cities, threshold=90):
    text_new = text
    if 'רחוב ' in text:
        text_new = text.split('רחוב ')[1].strip()
        suspected_city = process.extractOne(text_new, cities, scorer=fuzz.partial_ratio, score_cutoff=threshold)
        if suspected_city is None:
            text_new = text
    elif 'דרך' in text:
        text_new = text.split('דרך')[1]
        text_new = ('דרך' + text_new).strip()
        suspected_city = process.extractOne(text_new, cities, scorer=fuzz.partial_ratio, score_cutoff=threshold)
        if suspected_city is None:
            text_new = text
    elif "שד'" in text:
        text_new = text.split("שד'")[1]
        text_new = ("שד'" + text_new).strip()
        suspected_city = process.extractOne(text_new, cities, scorer=fuzz.partial_ratio, score_cutoff=threshold)
        if suspected_city is None:
            text_new = text
    return text_new


def preprocess_nonurban_text(text, intersections, threshold=80):
    text_new = text
    if 'צומת' in text:
        text_new = text.split('צומת')[1].strip()
        suspected_intersection = process.extractOne(text_new, intersections.intersection, scorer=fuzz.token_set_ratio,
                                                    score_cutoff=threshold)
        if suspected_intersection is None:
            text_new = text
    elif 'מחלף' in text:
        text_new = text.split('מחלף')[1].strip()
        suspected_intersection = process.extractOne(text_new, intersections.intersection, scorer=fuzz.token_set_ratio,
                                                    score_cutoff=threshold)
        if suspected_intersection is None:
            text_new = text
    elif 'כניסה ל' in text:
        text_new = text.split('כניסה ל')[1].strip()
        suspected_intersection = process.extractOne(text_new, intersections.intersection, scorer=fuzz.token_set_ratio,
                                                    score_cutoff=threshold)
        if suspected_intersection is None:
            text_new = text
    elif 'כביש' in text:
        text_new = text.split('כביש')[1].strip()
        suspected_intersection = process.extractOne(text_new, intersections.intersection, scorer=fuzz.token_set_ratio,
                                                    score_cutoff=threshold)
        if suspected_intersection is None:
            text_new = text
    return text_new


class UrbanAddress:
    def __init__(self, city='NaN', street='NaN', street2='NaN'):
        self.city = city
        self.street = street
        self.street2 = street2

    def __str__(self):
        return 'city: ' + str(self.city) + ', street: ' + \
               str(self.street) + ', street2 :' + str(self.street2)

    def __repr__(self):
        return "UrbanAddress(%s, %s, %s)" % (self.city, self.street, self.street2)

    def __eq__(self, other):
        if isinstance(other, UrbanAddress):
            return (self.city == other.city) and (self.street == other.street) and (self.street2 == other.street2)
        else:
            return False

    def __hash__(self):
        return hash(self.__repr__())


class NonUrbanAddress:
    def __init__(self, road1='NaN', road2='NaN', intersection='NaN'):
        self.road1 = road1
        self.road2 = road2
        self.intersection = intersection

    def __str__(self):
        return 'road1: ' + str(self.road1) + ', road2:' \
               + str(self.road2) + ', intersection: ' + str(self.intersection)

    def __repr__(self):
        return "NonUrbanAddress(%s, %s, %s)" % (self.road1, self.road2, self.intersection)

    def __eq__(self, other):
        if isinstance(other, NonUrbanAddress):
            return ((self.road1 == other.road1) and (self.road2 == other.road2) and (
                    self.intersection == other.intersection))
        else:
            return False

    def __hash__(self):
        return hash(self.__repr__())


def process_urban_with_geo_dict(text, streets, cities, threshold_city=70,
                                threshold_street=50, ratio=0.85,
                                city='', street1='', street2=''):
    if city != '':
        suspected_city = process.extractOne(city, cities, scorer=fuzz.partial_ratio, score_cutoff=threshold_city)
    else:
        suspected_city = process.extractOne(text, cities, scorer=fuzz.partial_ratio, score_cutoff=threshold_city)
    if suspected_city is not None:
        suspected_city = suspected_city[0]
        streets_in_city = streets.loc[streets.city == suspected_city]
        relevant_streets_1 = streets_in_city.loc[(streets_in_city.street1 != 'NaN')].street1
        relevant_streets_2 = streets_in_city.loc[(streets_in_city.street2 != 'NaN')].street2
        relevant_streets = relevant_streets_1.append(relevant_streets_2).drop_duplicates()
        relevant_streets_scores = relevant_streets.apply(lambda x: streets_in_city
                                                         .loc[(streets_in_city.street1 == x) |
                                                              (streets_in_city.street2 == x)].avg_accidents.max())
        relevant_streets = pd.DataFrame(
            {'street': relevant_streets.tolist(), 'avg_accidents': relevant_streets_scores.tolist()})
        result_streets = []
        result_city = []
        for street in [street1, street2]:
            if street != '':
                try:
                    suspected_streets = process.extract(street, list(set(relevant_streets.street.dropna().tolist())),
                                                    scorer=fuzz.token_set_ratio, limit=3)
                except Exception:
                    return UrbanAddress(city=city)
                if len(suspected_streets) > 0:
                    relevant_streets_scores = relevant_streets.loc[
                        relevant_streets.street.isin(
                            [suspected_street[0] for suspected_street in suspected_streets])].copy()
                    relevant_streets_scores.avg_accidents = (
                            relevant_streets_scores.avg_accidents / relevant_streets_scores.avg_accidents.max()).copy()
                    suspected_streets = [(suspected_street[0],
                                          (ratio * fuzz.token_set_ratio(text,
                                                                        suspected_city[0] + ' ' + suspected_street[0]))
                                          + ((1 - ratio) * 100 * relevant_streets_scores.loc[
                                              relevant_streets_scores.street == suspected_street[0]].avg_accidents.iloc[
                                              0]))
                                         for suspected_street in suspected_streets if suspected_street is not None and
                                         (ratio * fuzz.token_set_ratio(text,
                                                                       suspected_city[0] + ' ' + suspected_street[0]))
                                         + ((1 - ratio) * 100 *
                                            relevant_streets_scores.loc[relevant_streets_scores.street ==
                                                                        suspected_street[0]].avg_accidents.iloc[
                                                0]) > threshold_street]
                if len(suspected_streets) > 0:
                    suspected_street = max(suspected_streets, key=lambda x: x[1])
                    suspected_street = suspected_street[0]
                    if suspected_street in streets_in_city.street1.tolist():
                        suspected_street = streets_in_city.loc[streets_in_city.street1 == suspected_street].iloc[0]
                        suspected_street_street = suspected_street.street1_hebrew
                    else:
                        suspected_street = streets_in_city.loc[streets_in_city.street2 == suspected_street].iloc[0]
                        suspected_street_street = suspected_street.street2_hebrew
                    suspected_street_city = suspected_street.yishuv_name
                    result_streets.append(suspected_street_street)
                    result_city.append(suspected_street_city)
        if len(result_streets) > 0:
            if len(result_streets) == 1:
                return UrbanAddress(city=result_city[0], street=result_streets[0])
            else:
                return UrbanAddress(city=result_city[0], street=result_streets[0], street2=result_streets[1])
        else:
            return UrbanAddress(city=streets.loc[streets.city == suspected_city].yishuv_name.iloc[0])
    return None


def process_urban(text, streets, cities, threshold_city=70, threshold_street=50, ratio=0.85):
    text = preprocess_urban_text(text, cities)
    suspected_city = process.extractOne(text, cities, scorer=fuzz.partial_ratio, score_cutoff=threshold_city)
    if suspected_city is not None:
        suspected_city = suspected_city[0]
        streets_in_city = streets.loc[streets.city == suspected_city]
        relevant_streets_1 = streets_in_city.loc[(streets_in_city.street1 != 'NaN')].street1
        relevant_streets_2 = streets_in_city.loc[(streets_in_city.street2 != 'NaN')].street2
        relevant_streets = relevant_streets_1.append(relevant_streets_2).drop_duplicates()
        relevant_streets_scores = relevant_streets.apply(lambda x: streets_in_city
                                                         .loc[(streets_in_city.street1 == x) |
                                                              (streets_in_city.street2 == x)].avg_accidents.max())
        relevant_streets = pd.DataFrame(
            {'street': relevant_streets.tolist(), 'avg_accidents': relevant_streets_scores.tolist()})
        suspected_streets = process.extract(text, list(set(relevant_streets.street.dropna().tolist())),
                                            scorer=fuzz.token_set_ratio, limit=3)
        if len(suspected_streets) > 0:
            relevant_streets_scores = relevant_streets.loc[
                relevant_streets.street.isin([suspected_street[0] for suspected_street in suspected_streets])].copy()
            relevant_streets_scores.avg_accidents = (
                    relevant_streets_scores.avg_accidents / relevant_streets_scores.avg_accidents.max()).copy()
            suspected_streets = [(suspected_street[0],
                                  (ratio * fuzz.token_set_ratio(text, suspected_city[0] + ' ' + suspected_street[0]))
                                  + ((1 - ratio) * 100 * relevant_streets_scores.loc[
                                      relevant_streets_scores.street == suspected_street[0]].avg_accidents.iloc[0]))
                                 for suspected_street in suspected_streets if suspected_street is not None and
                                 (ratio * fuzz.token_set_ratio(text, suspected_city[0] + ' ' + suspected_street[0]))
                                 + ((1 - ratio) * 100 * relevant_streets_scores.loc[
                    relevant_streets_scores.street == suspected_street[0]].avg_accidents.iloc[0])
                                 > threshold_street]
        if len(suspected_streets) > 0:
            suspected_street = max(suspected_streets, key=lambda x: x[1])
            suspected_street = suspected_street[0]
            if suspected_street in streets_in_city.street1.tolist():
                suspected_street = streets_in_city.loc[streets_in_city.street1 == suspected_street].iloc[0]
                return UrbanAddress(city=suspected_street.yishuv_name, street=suspected_street.street1_hebrew)
            else:
                suspected_street = streets_in_city.loc[streets_in_city.street2 == suspected_street].iloc[0]
                return UrbanAddress(city=suspected_street.yishuv_name, street=suspected_street.street2_hebrew)
        return UrbanAddress(city=streets.loc[streets.city == suspected_city].yishuv_name.iloc[0])
    return None


def process_intersection_first_road(text, roads, road1_candidates, threshold=50):
    relevant_intersections = None
    for road1_candidate in road1_candidates:
        if relevant_intersections is None:
            relevant_intersections = roads.loc[
                (roads.first_road == road1_candidate) | (roads.second_road == road1_candidate)]
        else:
            relevant_intersections = relevant_intersections.append(
                roads.loc[(roads.first_road == road1_candidate) | (roads.second_road == road1_candidate)])
    if relevant_intersections is not None:
        relevant_intersections = relevant_intersections.drop_duplicates()
        text = preprocess_nonurban_text(text, relevant_intersections)
        suspected_intersection = process.extractOne(text,
                                                    list(set(relevant_intersections.intersection.dropna().tolist())),
                                                    scorer=fuzz.token_set_ratio, score_cutoff=threshold)
        if suspected_intersection is not None:
            suspected_intersection = suspected_intersection[0]
            suspected_road = \
                relevant_intersections.loc[relevant_intersections.intersection == suspected_intersection].iloc[0]
            first_road_value = suspected_road.road1
            second_road_value = suspected_road.road2
            intersection_value = suspected_road.non_urban_intersection_hebrew
            return NonUrbanAddress(road1=first_road_value, road2=second_road_value, intersection=intersection_value)
    return NonUrbanAddress(road1=road1_candidates[0].replace('כביש ', ''))


def process_intersection_no_roads(text, roads, threshold=50):
    relevant_intersections = roads.drop_duplicates()
    text = preprocess_nonurban_text(text, relevant_intersections)
    suspected_intersection = process.extractOne(text, list(set(relevant_intersections.intersection.dropna().tolist())),
                                                scorer=fuzz.token_set_ratio, score_cutoff=threshold)
    if suspected_intersection is not None:
        suspected_intersection = suspected_intersection[0]
        suspected_road = relevant_intersections.loc[relevant_intersections.intersection == suspected_intersection].iloc[
            0]
        first_road_value = suspected_road.road1
        second_road_value = suspected_road.road2
        intersection_value = suspected_road.non_urban_intersection_hebrew
        return NonUrbanAddress(road1=first_road_value, road2=second_road_value, intersection=intersection_value)
    return None


def process_intersections_both_roads(text, roads, roads_candidates, threshold=50):
    relevant_intersections = None
    for candidate in roads_candidates:
        if relevant_intersections is None:
            relevant_intersections = roads.loc[
                ((roads.first_road == candidate[0]) & (roads.second_road == candidate[1])) | (
                        (roads.first_road == candidate[1]) & (roads.second_road == candidate[0]))]
        else:
            relevant_intersections = relevant_intersections.append(roads.loc[((roads.first_road == candidate[0]) & (
                    roads.second_road == candidate[1])) | ((roads.first_road == candidate[1]) &
                                                           (roads.second_road == candidate[0]))])
    if relevant_intersections is not None:
        relevant_intersections = relevant_intersections.drop_duplicates()
        text = preprocess_nonurban_text(text, relevant_intersections)
        suspected_intersection = process.extractOne(text,
                                                    list(set(relevant_intersections.intersection.dropna().tolist())),
                                                    scorer=fuzz.token_set_ratio, score_cutoff=threshold)
        if suspected_intersection is not None:
            suspected_intersection = suspected_intersection[0]
            suspected_road = \
                relevant_intersections.loc[relevant_intersections.intersection == suspected_intersection].iloc[0]
            first_road_value = suspected_road.road1
            second_road_value = suspected_road.road2
            intersection_value = suspected_road.non_urban_intersection_hebrew
            return NonUrbanAddress(road1=first_road_value, road2=second_road_value, intersection=intersection_value)
    return NonUrbanAddress(road1=roads_candidates[0][0].replace('כביש ', ''),
                           road2=roads_candidates[0][1].replace('כביש ', ''))


def is_urban(text, geo_location_dict=None):
    if geo_location_dict is not None:
        if  geo_location_dict['road_no'] == '':
            # check if any of geo_location_dict values contains a road mention
            road_examples = ['כביש ' + str(digit) for digit in range(10)]
            for value in geo_location_dict.values():
                if value in road_examples:
                    return True
        else:
            return False
    road_examples = ['כביש ' + str(digit) for digit in range(10)]
    return not any(road_example in text for road_example in road_examples)


def process_nonurban(text, roads):
    road1_candidates = []
    roads_candidates = []
    for road1 in roads.first_road:
        if text.find(road1) != -1:
            if text.endswith(road1) or not \
                    ('0' <= text[text.find(road1) + len(road1)] <= '9'):
                road1_candidates.append(road1)
    if len(road1_candidates) > 0:
        road1_candidates = list(sorted(set(road1_candidates)))
        for road1 in road1_candidates:
            road2_candidates = roads.loc[roads.first_road == road1].second_road.dropna().tolist()
            for road2 in road2_candidates:
                if text.find(road2) != -1:
                    if text.endswith(road2) or not \
                            ('0' <= text[text.find(road2) + len(road2)] <= '9'):
                        roads_candidates.append((road1, road2))
        if len(roads_candidates) > 0:
            roads_candidates = list(sorted(set(roads_candidates)))
            return process_intersections_both_roads(text, roads, roads_candidates)
        else:
            return process_intersection_first_road(text, roads, road1_candidates)
    else:
        return process_intersection_no_roads(text, roads)


def get_db_matching_location_of_text(text, geo_location_dict=None):
    text = preprocess_text(text, True)
    if is_urban(text, geo_location_dict=geo_location_dict):
        streets = pd.read_excel('anyway/parsers/news_flash/streets.xlsx')
        cities = pd.read_excel('anyway/parsers/news_flash/cities.xlsx', sheet_name='Sheet1').city.tolist()
        if geo_location_dict is not None:
            street1 = geo_location_dict['street']
            street2 = ''
            if geo_location_dict['intersection'] != '':
                if len(geo_location_dict['intersection'].split('&')) > 1:
                    street1 = geo_location_dict['intersection'].split('&')[0].strip()
                    street2 = geo_location_dict['intersection'].split('&')[1].strip()
                else:
                    street1 = geo_location_dict['intersection'].split('&')[0].strip()
                    street2 = ''
            return process_urban_with_geo_dict(text, streets, cities,
                                               city=geo_location_dict['city'],
                                               street1=street1, street2=street2)
        return process_urban(text, streets, cities)
    else:
        roads = pd.read_excel('anyway/parsers/news_flash/roads.xlsx', sheet_name='Sheet1')
        return process_nonurban(text, roads)


def manual_filter_location_of_text(text):
    filter_ind = float('inf')
    if text.find('.') != -1:
        text = text[:text.find('.')]
    try:
        forbid_words = ['תושב']
        hospital_words = ['בבית החולים', 'בית חולים', 'בית החולים', 'מרכז רפואי']
        hospital_names = ['שיבא', 'וולפסון', 'תל השומר', 'סוראסקי', 'הלל יפה', 'רמב"ם', 'רמבם', 'בני ציון', 'רוטשילד',
                          'גליל מערבי', 'זיו', 'פוריה', 'ברזילי', 'אסף הרופא', 'סורוקה', 'רבין', 'בלינסון', 'גולדה',
                          'כרמל', 'עמק', 'מאיר', 'קפלן', 'יוספטל', 'הדסה', 'שערי צדק', 'צאנז', 'לניאדו', 'אסותא',
                          'מעיני הישועה', 'מדיקל סנטר', 'איטלקי', 'המשפחה הקדושה']
        forbid_words.extend(hospital_words)
        for forbid_word in forbid_words:
            found_hospital = False
            removed_punc = False
            if forbid_word in text:
                forbid_ind = text.find(forbid_word)
                for punc_to_try in [',', ' - ']:
                    punc_before_ind = text.find(punc_to_try, 0, forbid_ind)
                    punc_after_ind = text.find(punc_to_try, forbid_ind)
                    if punc_before_ind != -1 or punc_after_ind != -1:
                        if punc_before_ind == -1:
                            text = text[(punc_after_ind + 1):]
                        elif punc_after_ind == -1:
                            text = text[:punc_before_ind]
                        else:
                            text = text[:punc_before_ind] + ' ' + text[(punc_after_ind + 1):]
                        removed_punc = True
                        break
                if (not removed_punc) and (forbid_word in hospital_words):
                    for hospital_name in hospital_names:
                        hospital_ind = text.find(hospital_name)
                        if hospital_ind == forbid_ind + len(forbid_word) + 1 or hospital_ind == forbid_ind + len(
                                forbid_word) + 2:
                            text = text[:hospital_ind] + text[hospital_ind + len(hospital_name) + 1:]
                            forbid_ind = text.find(forbid_word)
                            text = text[:forbid_ind] + text[forbid_ind + len(forbid_word) + 1:]
                            found_hospital = True
                if (not found_hospital) and (not removed_punc):
                    text = text[:forbid_ind] + text[text.find(' ', forbid_ind + len(forbid_word) + 2):]

    except Exception as _:
        pass
    if 'כביש' in text:
        filter_ind = min(filter_ind, text.find('כביש'))
    if 'שדרות' in text:
        filter_ind = min(filter_ind, text.find('שדרות'))
    if 'רחוב' in text:
        filter_ind = min(filter_ind, text.find('רחוב'))
    if 'מחלף' in text:
        filter_ind = min(filter_ind, text.find('מחלף'))
    if 'צומת' in text:
        filter_ind = min(filter_ind, text.find('צומת'))
    if 'סמוך ל' in text:
        filter_ind = min(filter_ind, text.find('סמוך ל') + len('סמוך ל'))
    if 'יישוב' in text:
        filter_ind = min(filter_ind, text.find('יישוב'))
    if 'מושב' in text:
        filter_ind = min(filter_ind, text.find('מושב'))
    if 'קיבוץ' in text:
        filter_ind = min(filter_ind, text.find('קיבוץ'))
    if 'התנחלות' in text:
        filter_ind = min(filter_ind, text.find('התנחלות'))
    if 'שכונת' in text:
        filter_ind = min(filter_ind, text.find('שכונת'))
    if 'בדרך' in text:
        filter_ind = min(filter_ind, text.find('בדרך'))
    if filter_ind != float('inf'):
        text = text[filter_ind:]
    return text
