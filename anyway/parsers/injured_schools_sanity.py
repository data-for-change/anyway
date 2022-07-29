import json

def check():
    original_json = json.load(open("static/data/schools/injured_around_schools_api_2020.json"))
    carmels_json = json.load(open("static/data/schools/injured_around_schools_api_carmel_sanity.json"))

    schools_ids = list(original_json.keys())

    invalid_schools = set()
    missing_schools = set()

    for school_id in schools_ids:
        is_school_valid = True
        print(f"🏢 Checking school '{school_id}'")
        original_school_data = original_json.get(school_id)
        if carmels_school_data := carmels_json.get(school_id):
            if len(original_school_data) != len(carmels_school_data):
                is_school_valid = False
                invalid_schools.add(school_id)
                print(f"❌ school '{school_id}' in original file has {len(original_school_data)} items, whereas in carmel's file it has {len(carmels_school_data)} items")
            else:
                sorted_original = sorted(original_school_data, key=lambda school: school.get('accident_year'))
                sorted_carmel = sorted(carmels_school_data, key=lambda school: school.get('accident_year'))
                for idx in range(len(sorted_original)):
                    original_item, carmels_item = sorted_original[idx], sorted_carmel[idx]
                    for key in original_item.keys():
                        if original_item.get(key) != carmels_item.get(key):
                            is_school_valid = False
                            invalid_schools.add(school_id)
                            print(f"❌ school '{school_id}' in original file has value '{original_item.get(key)}' for key '{key}', whereas carmel's file has the value of '{carmels_item.get(key)}' (accident year {original_item.get('accident_year')})")
        else:
            is_school_valid = False
            missing_schools.add(school_id)
            print(f"😱 school '{school_id}' does not exist in carmel's file!")
        if is_school_valid:
            print(f"✅ school '{school_id}' is valid!")

    if len(invalid_schools) == 0 and len(missing_schools) == 0:
        print(f'🎉 all schools are valid!')
    else:
        print(f"Invalid schools: {float(len(invalid_schools)/len(schools_ids)*100)}%,  missing schools: {float(len(missing_schools)/len(schools_ids)*100)}%")

if __name__ == '__main__':
    check()