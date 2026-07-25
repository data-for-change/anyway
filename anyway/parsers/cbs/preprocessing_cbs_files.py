import os

CBS_FILES_HEBREW = {
    "sadot": "Fields",
    "zmatim_ironiim": "IntersectUrban",
    "zmatim_lo_ironiim": "IntersectNonUrban",
    "rehev": "VehData",
    "rechev": "VehData",
    "milon": "Dictionary",
    "meoravim": "InvData",
    "klali": "AccData",
    "rechovot": "DicStreets",
}


def get_updated_cbs_file_name(file_name):
    for hebrew_file_name, english_file_name in CBS_FILES_HEBREW.items():
        if (
            hebrew_file_name in file_name.lower()
            and english_file_name.lower() not in file_name.lower()
        ):
            return file_name.replace(".csv", "_" + english_file_name + ".csv")
    return file_name


def update_cbs_files_names(directory):
    files = sorted([path for path in os.listdir(directory)])
    for file in files:
        file_path = os.path.join(directory, file)
        updated_file_path = os.path.join(directory, get_updated_cbs_file_name(file))
        if updated_file_path != file_path:
            os.rename(file_path, updated_file_path)


def get_accidents_file_data(directory):
    for file_path in os.listdir(directory):
        if file_path.endswith("{0}{1}".format(CBS_FILES_HEBREW["klali"], ".csv")):
            return os.path.join(directory, file_path)


if __name__ == "__main__":
    pass
