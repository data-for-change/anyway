# Imports the Google Cloud client library
import html
import sys

from google.cloud import language
from google.cloud import translate
from google.cloud.language import enums
from google.cloud.language import types


def get_location_of_text(text):

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
    result = translate_client.translate(text, target_language="en", source_language="iw")
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
            print('=' * 20)
            print('name: {0}'.format(entity.name))
            print('mentions: {0}'.format(entity.mentions))
            if ' ' in entity.name:
                for item in list(filter(None, entity.name.split(' '))):
                    loc_entities_word_indices.append(
                        [idx for idx, s in enumerate(translated_text_word_split) if item in s][0])
                    loc_entities.append(item)
                    loc_entities_indices.append(translated_text.index(item))
            else:
                loc_entities_word_indices.append(
                    [idx for idx, s in enumerate(translated_text_word_split) if entity.name in s][0])
                loc_entities.append(entity.name)
                loc_entities_indices.append(translated_text.index(entity.name))

            # In case there is a reference to a previous location
            if 'city' == entity.name.lower() or 'town' == entity.name.lower() or 'village' == entity.name.lower() or \
                    'junction' == entity.name.lower() or 'interchange' == entity.name.lower() or \
                    'intersect' == entity.name.lower() or 'street' == entity.name.lower():
                reference_grouping = True

    # Sort entities by appearing order in the string
    loc_entities = [x for _, x in sorted(zip(loc_entities_indices, loc_entities))]
    loc_entities_word_indices = [x for _, x in sorted(zip(loc_entities_indices, loc_entities_word_indices))]

    # Location grouping - takes the largest group of words indicating location based on distance between groups
    if len(loc_entities) >= 1:
        diff = [loc_entities_word_indices[i + 1] - loc_entities_word_indices[i] for i in
                range(len(loc_entities_word_indices) - 1)]
        if max(diff) > 3:  # Distance is greater than 3 words
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
                                     not (len(group) == 1 and "road" == translated_text_word_split[group[0]].lower())]

            # We are not interested in the hospital location, unless the city isn't mentioned elsewhere
            no_hospital_loc_groups = [group for group in no_random_road_groups
                                      if not
                                      any("hospital" in translated_text_word_split[item].lower() for item in group)]
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
                == "the ":
            translated_location = translated_text[
                                  translated_text.index(loc_entities[0]) - 4:translated_text.index(
                                      loc_entities[-1]) + len(
                                      loc_entities[-1])]

        # If a location without name is in the beginning of the string, add the previous word
        if translated_location.lower().startswith("street") or translated_location.lower().startswith("interchange") \
                or translated_location.lower().startswith("village") or translated_location.lower().startswith("town") \
                or translated_location.lower().startswith("city") or translated_location.lower().startswith(
            "intersection") \
                or translated_location.lower().startswith("junction"):
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
            if previous != sys.maxsize and "hospital" not in \
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
                == "the ":
            translated_location = translated_text[
                                  translated_text.index(loc_entities[0]):translated_text.index(loc_entities[0]) + len(
                                      loc_entities[0])]

        # If the entity is a location without name, add previous word
        if translated_location.lower().startswith("street") or translated_location.lower().startswith("interchange") \
                or translated_location.lower().startswith("village") or translated_location.lower().startswith("town") \
                or translated_location.lower().startswith("city") or translated_location.lower().startswith(
            "intersection") \
                or translated_location.lower().startswith("junction"):
            translated_location = translated_text_word_split[translated_text_word_split.index(loc_entities[0]) - 1] \
                                  + ' ' + translated_location

    else:
        translated_location = ""

    # Processing the location
    translated_location = translated_location.strip()
    if ',' == translated_location[-1]:
        translated_location = translated_location[:-1]
    if translated_location != "":
        result = translate_client.translate(translated_location, target_language="iw", source_language="en")
        translated_location = result['translatedText']
        translated_location = html.unescape(translated_location)
    return translated_location
