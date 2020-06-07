import argparse
import os

CBS_FILES_ENDINGS = [
    "AccAverages.xls",
    "AccAverages.pdf",
    "AccData.csv",
    "AccCodebook.pdf",
    "AccCodebook.xls",
    "DicStreets.csv",
    "Dictionary.csv",
    "IntersectNonUrban.csv",
    "IntersectUrban.csv",
    "Introduction.pdf",
    "InvAverages.pdf",
    "InvAverages.xls",
    "InvCodebook.pdf",
    "InvCodebook.xls",
    "InvData.csv",
    "Methodology.pdf",
    "ReadMe.pdf",
    "VehAverages.pdf",
    "VehAverages.xls",
    "VehCodebook.pdf",
    "VehCodebook.xls",
    "VehData.csv",
]


def validate_cbs_directory(dir_path):
    cbs_files_endings_lower = [s.lower() for s in CBS_FILES_ENDINGS]
    extra_files_list = []

    for filename in sorted(os.listdir(dir_path)):
        for file_ending in cbs_files_endings_lower:
            if file_ending in filename.lower():
                cbs_files_endings_lower.remove(file_ending)
                break
        else:
            extra_files_list.append(filename)

    missing_files_list = [s for s in CBS_FILES_ENDINGS if s.lower() in cbs_files_endings_lower]
    return sorted(extra_files_list), sorted(missing_files_list)


def main(cbs_directory_path, all_output_file_name, missing_files_output_file_name):
    all_output_file = open(all_output_file_name, "w")
    missing_data_output_file = open(missing_files_output_file_name, "w")

    for subdir, dirs, files in sorted(os.walk(cbs_directory_path)):
        if (
            subdir.endswith("accidents_type_1")
            or subdir.endswith("accidents_type_3")
            or subdir.endswith("cbs")
            or subdir.endswith("cbs")
        ):
            continue
        extra_files_list, missing_files_list = validate_cbs_directory(subdir)
        all_output_file.write(subdir + ":\n")
        all_output_file.write("\t" + "extra_files_list: " + str(extra_files_list) + "\n")
        all_output_file.write("\t" + "missing_files_list: " + str(missing_files_list) + "\n\n")
        if missing_files_list:
            missing_data_output_file.write(subdir + ":\n")
            missing_data_output_file.write(
                "\t" + "missing_files_list: " + str(missing_files_list) + "\n\n"
            )

    all_output_file.close()
    missing_data_output_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cbs_directory_path", type=str, help="input cbs dir path")
    parser.add_argument(
        "--all_output_file_name", type=str, help="output file name for the whole output"
    )
    parser.add_argument(
        "--missing_files_output_file_name", type=str, help="output file name for the missing data"
    )

    args = parser.parse_args()
    main(args.cbs_directory_path, args.all_output_file_name, args.missing_files_output_file_name)
