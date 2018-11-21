# Imports the Google Cloud client library
import html
import sys

from google.cloud import language
from google.cloud import translate
from google.cloud.language import enums
from google.cloud.language import types


def get_location_of_text(text):
    loc_segments = []
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
    loc_entities = []
    loc_entities_indices = []
    translated_text_word_split = list(filter(None, translated_text.split(' ')))
    loc_entities_word_indices = []
    for entity in response.entities:
        if entity.type == enums.Entity.Type.LOCATION:
            if ' ' in entity.name:
                for item in list(filter(None, entity.name.split(' '))):
                    loc_entities_word_indices.append(
                        [idx for idx, s in enumerate(translated_text_word_split) if item in s][0])
            else:
                loc_entities_word_indices.append(
                    [idx for idx, s in enumerate(translated_text_word_split) if entity.name in s][0])
            if 'city' == entity.name.lower() or 'town' == entity.name.lower() or 'village' == entity.name.lower():
                reference_grouping = True
            loc_entities.append(entity.name)
            loc_entities_indices.append(translated_text.index(entity.name))
    # Sort entities by appearing order in the string
    loc_entities = [x for _, x in sorted(zip(loc_entities_indices, loc_entities))]
    # Copy the string containing the entities for relational data between them
    if len(loc_entities) >= 1:
        # Location grouping - takes the largest group of words indicating location based on distance between groups
        loc_entities_word_indices.sort()
        diff = [loc_entities_word_indices[i + 1] - loc_entities_word_indices[i] for i in
                range(len(loc_entities_word_indices) - 1)]

        if max(diff) > 3 and not reference_grouping:  # distance is greater than 3 words
            avg = sum(diff) / len(diff)
            loc_segments = [[loc_entities_word_indices[0]]]
            for x in loc_entities_word_indices[1:]:
                if x - loc_segments[-1][-1] < avg:
                    loc_segments[-1].append(x)
                else:
                    loc_segments.append([x])
            bounds_loc_segments = [i[-1] - i[0] for ind, i in enumerate(loc_segments)]
            biggest_group_index = bounds_loc_segments.index(max(bounds_loc_segments))
            loc_entities = [translated_text_word_split[item] for item in loc_segments[biggest_group_index]]
        # Getting the full string from the text indicating the location and not just entities
        translated_location = translated_text[
                              translated_text.index(loc_entities[0]):translated_text.index(loc_entities[-1]) + len(
                                  loc_entities[-1])]
        if translated_text[translated_text.index(loc_entities[0]) - 4:translated_text.index(loc_entities[0])].lower() \
                == "the ":
            translated_location = translated_text[
                                  translated_text.index(loc_entities[0]) - 4:translated_text.index(
                                      loc_entities[-1]) + len(
                                      loc_entities[-1])]
            # Solving the reference in case there is another group, by making use of it
            if reference_grouping and len(loc_segments) >= 2:
                previous = sys.maxsize
                after = sys.maxsize
                if biggest_group_index > 0:
                    previous = loc_segments[biggest_group_index][0] - loc_segments[biggest_group_index - 1][-1]
                if biggest_group_index < len(loc_segments) - 1:
                    after = loc_segments[biggest_group_index + 1][0] - loc_segments[biggest_group_index][-1]
                if min(previous, after) != sys.maxsize:
                    if previous == min(previous, after):
                        text_to_replace = translated_text_word_split[
                            loc_segments[biggest_group_index - 1][-1]]
                        if len(loc_segments[biggest_group_index - 1]) > 1:
                            last = loc_segments[biggest_group_index - 1][-1]
                            for index, val in enumerate(loc_segments[biggest_group_index - 1][::-1][1:]):
                                if last - val == 1:
                                    text_to_replace = translated_text_word_split[
                                                          loc_segments[biggest_group_index - 1][
                                                              -2 - index]] + ' ' + text_to_replace
                                    last = val
                                else:
                                    break
                        translated_location = translated_location.replace(
                            'the city', text_to_replace).replace(
                            'city', text_to_replace).replace(
                            'the town', text_to_replace).replace(
                            'town', text_to_replace).replace(
                            'the village', text_to_replace).replace(
                            'village', text_to_replace)
                    else:
                        text_to_replace = translated_text_word_split[
                            loc_segments[biggest_group_index + 1][0]]
                        if len(loc_segments[biggest_group_index + 1]) > 1:
                            last = loc_segments[biggest_group_index + 1][0]
                            for index, val in enumerate(loc_segments[biggest_group_index + 1][1:]):
                                if val - last == 1:
                                    text_to_replace = translated_text_word_split[
                                                          loc_segments[biggest_group_index + 1][
                                                              1 + index]] + ' ' + text_to_replace
                                    last = val
                                else:
                                    break
                        translated_location = translated_location.replace(
                            'the city', text_to_replace).replace(
                            'city', text_to_replace).replace(
                            'the town', text_to_replace).replace(
                            'town', text_to_replace).replace(
                            'the village', text_to_replace).replace(
                            'village', text_to_replace)

    elif len(loc_entities) == 1:
        translated_location = loc_entities
        if translated_text[translated_text.index(loc_entities[0]) - 4:translated_text.index(loc_entities[0])].lower() \
                == "the ":
            translated_location = translated_text[
                                  translated_text.index(loc_entities[0]):translated_text.index(loc_entities[0]) + len(
                                      loc_entities[0])]
    else:
        translated_location = ""
    location = translated_location.strip()
    if ',' == location[-1]:
        location = location[:-1]
    if location != "":
        result = translate_client.translate(location, target_language="iw", source_language="en")
        location = result['translatedText']
        location = html.unescape(location)
    return location
