# Imports the Google Cloud client library
import html
import os
import sys

import googlemaps
from google.cloud import language
from google.cloud import translate
from google.cloud.language import enums
from google.cloud.language import types


# from ..anyway.parsers.news_flash import get_latest_id_from_db


def get_location_of_text(input_text, maps_key):
    no_random_road_groups = []
    no_hospital_loc_groups = []
    loc_groups = []
    biggest_group_index = -1
    reference_grouping = False

    # Instantiates the clients
    client = language.LanguageServiceClient()
    translate_client = translate.Client()

    # Translate
    result = translate_client.translate(input_text, target_language='en', source_language='iw')
    translated_text = result['translatedText']
    translated_text = html.unescape(translated_text)
    # Pre-processing - from what I saw only the first line has the location
    translated_text = list(filter(None, translated_text.split('.')))[0]
    # Analyze (Named Entity Recognition)
    document = types.Document(content=translated_text, type=enums.Document.Type.PLAIN_TEXT)
    response = client.analyze_entities(document=document)
    # Getting the location entities and their indices in the text and adding them to a list
    loc_entities = []
    loc_entities_indices = []
    translated_text_word_split = list(filter(None, translated_text.split(' ')))
    loc_entities_word_indices = []
    for entity in response.entities:
        if entity.type == enums.Entity.Type.LOCATION:
            print('=' * 20)
            print('name: {0}'.format(entity.name))
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
    # Original order
    print(translated_text)
    print(loc_entities)
    print(loc_entities_indices)
    # Sort entities by appearing order in the string
    loc_entities = [x for _, x in sorted(zip(loc_entities_indices, loc_entities))]
    loc_entities_new = []
    for item in loc_entities:
        loc_entities_word_indices.append(
            [idx for idx, s in enumerate(translated_text_word_split) if item in s][loc_entities_new.count(item)])
        loc_entities_new.append(item)
    loc_entities = loc_entities_new
    print('\n \n \n')
    print(loc_entities)
    print(loc_entities_word_indices)
    print('reference grouping ' + str(reference_grouping))
    # Copy the string containing the entities for relational data between them
    if len(loc_entities) >= 1:
        # Location grouping - takes the largest group of words indicating location based on distance between groups
        diff = [loc_entities_word_indices[i + 1] - loc_entities_word_indices[i] for i in
                range(len(loc_entities_word_indices) - 1)]
        print(diff)
        if max(diff) > 5:  # distance is greater than 5 words
            avg = sum(diff) / len(diff)
            loc_groups = [[loc_entities_word_indices[0]]]
            for x in loc_entities_word_indices[1:]:
                if x - loc_groups[-1][-1] < avg:
                    loc_groups[-1].append(x)
                else:
                    loc_groups.append([x])
            print(loc_groups)
            no_random_road_groups = [group for group in loc_groups
                                     if
                                     not (len(group) == 1 and 'road' == translated_text_word_split[group[0]].lower())]
            no_hospital_loc_groups = [group for group in no_random_road_groups
                                      if not
                                      any('hospital' in translated_text_word_split[item].lower() for item in group)]
            bounds_loc_groups = [i[-1] - i[0] for ind, i in enumerate(no_hospital_loc_groups)]
            biggest_group_index = bounds_loc_groups.index(max(bounds_loc_groups))
            loc_entities = [translated_text_word_split[item] for item in no_hospital_loc_groups[biggest_group_index]]
            print(loc_entities)
        # Getting the full string from the text indicating the location and not just entities
        translated_location = translated_text[
                              translated_text.index(loc_entities[0]):translated_text.index(loc_entities[-1]) + len(
                                  loc_entities[-1])]
        print(translated_location)
        if translated_text[translated_text.index(loc_entities[0]) - 4:translated_text.index(loc_entities[0])].lower() \
                == 'the ':
            translated_location = translated_text[
                                  translated_text.index(loc_entities[0]) - 4:translated_text.index(
                                      loc_entities[-1]) + len(
                                      loc_entities[-1])]
        print(translated_location)
        if translated_location.lower().startswith('street') or translated_location.lower().startswith('interchange') \
                or translated_location.lower().startswith('village') or translated_location.lower().startswith('town') \
                or translated_location.lower().startswith('city') or translated_location.lower().startswith(
            'intersection') \
                or translated_location.lower().startswith('junction'):
            translated_location = translated_text_word_split[translated_text_word_split.index(loc_entities[0]) - 1] \
                                  + ' ' + translated_location
            reference_grouping = False
        print(translated_location)
        print('\n\n\n')
        # Trying to solve the reference in case there is another group
        if reference_grouping and len(no_hospital_loc_groups) >= 2:
            print('xd0')
            previous = sys.maxsize
            if biggest_group_index > 0:
                previous = no_hospital_loc_groups[biggest_group_index][0] - \
                           no_hospital_loc_groups[biggest_group_index - 1][-1]
            if previous != sys.maxsize:
                text_to_replace = translated_text_word_split[
                    no_hospital_loc_groups[biggest_group_index - 1][-1]]
                print('text to replace' + text_to_replace)
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
        elif reference_grouping and len(no_random_road_groups) >= 2:
            print('check 0')
            previous = sys.maxsize
            bounds_loc_groups = [i[-1] - i[0] for ind, i in enumerate(no_random_road_groups)]
            biggest_group_index = bounds_loc_groups.index(max(bounds_loc_groups))
            if biggest_group_index > 0:
                previous = no_random_road_groups[biggest_group_index][0] - \
                           no_random_road_groups[biggest_group_index - 1][-1]
            if previous != sys.maxsize and 'hospital' not in \
                    translated_text_word_split[no_random_road_groups[biggest_group_index - 1][-1]].lower():
                print('check3')
                text_to_replace = translated_text_word_split[
                    no_random_road_groups[biggest_group_index - 1][-1]]
                print('text to replace' + text_to_replace)
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
        if translated_text[translated_text.index(loc_entities[0]) - 4:translated_text.index(loc_entities[0])].lower() \
                == 'the ':
            translated_location = translated_text[
                                  translated_text.index(loc_entities[0]):translated_text.index(loc_entities[0]) + len(
                                      loc_entities[0])]
        if translated_location.lower().startswith('street') or translated_location.lower().startswith('interchange') \
                or translated_location.lower().startswith('village') or translated_location.lower().startswith('town') \
                or translated_location.lower().startswith('city') or translated_location.lower().startswith(
            'intersection') \
                or translated_location.lower().startswith('junction'):
            translated_location = translated_text_word_split[translated_text_word_split.index(loc_entities[0]) - 1] \
                                  + ' ' + translated_location
    else:
        translated_location = ''
    translated_location = translated_location.strip()
    if ',' == translated_location[-1]:
        translated_location = translated_location[:-1]
    location = html.unescape(translated_location)
    gmaps = googlemaps.Client(key=maps_key)
    print('location: ' + location)
    geocode_result = gmaps.geocode(location)
    if geocode_result is None or geocode_result == []:
        return None
    country = ''
    print(geocode_result)
    for address in geocode_result[0]['address_components']:
        if any('country' in s for s in address['types']):
            country = address['short_name']
            break
    if country == 'IL':
        print(geocode_result[0]['geometry']['location'])
    else:
        return None


if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    text = u'''בית המשפט לתעבורה בפתח תקווה הגיש כתב אישום נגד נהג המשאית עלי עוודאללה, בן 25 מירושלים, בגין גרימת 
    מוות ברשלנות של בריג'יט חבר ז"ל ופציעת שבעה בני אדם, בהם ילדים, בכביש 40 באוגוסט האחרון. '''
    get_location_of_text(text, sys.argv[1])
    # print(get_latest_id_from_db())
