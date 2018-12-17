from ..constants import CONST
from six import iteritems
import os

def update_cbs_files_names(directory):
    files = sorted([path.lower() for path in os.listdir(directory)])
    for file in files:
        file_path = os.path.join(directory,file)
        for hebrew_file_name, english_file_name in iteritems(CONST.CBS_FILES_HEBREW):
            if hebrew_file_name in file and english_file_name.lower() not in file:
                os.rename(file_path,file_path.replace('.csv', '_' + english_file_name + '.csv'))

def main(path):
    update_cbs_files_names(path)
