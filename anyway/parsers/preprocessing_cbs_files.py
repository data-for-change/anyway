from six import iteritems
import os

CBS_FILES_HEBREW = {'sadot': 'Fields',
                    'zmatim_ironiim': 'IntersectUrban',
                    'zmatim_lo_ironiim': 'IntersectNonUrban',
                    'rehev': 'VehData',
                    'milon':'Dictionary',
                    'meoravim': 'InvData',
                    'klali': 'AccData',
                    'rechovot':'DicStreets'}

def update_cbs_files_names(directory):
    files = sorted([path.lower() for path in os.listdir(directory)])
    for file in files:
        file_path = os.path.join(directory,file)
        for hebrew_file_name, english_file_name in iteritems(CBS_FILES_HEBREW):
            if hebrew_file_name in file and english_file_name.lower() not in file:
                os.rename(file_path,file_path.replace('.csv', '_' + english_file_name + '.csv'))

def main(path):
    update_cbs_files_names(path)
