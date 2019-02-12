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
    files = sorted([path for path in os.listdir(directory)])
    accidents_file = None
    for file in files:
        file_path = os.path.join(directory,file)
        for hebrew_file_name, english_file_name in iteritems(CBS_FILES_HEBREW):
            if hebrew_file_name in file.lower() and english_file_name.lower() not in file.lower():
                os.rename(file_path,file_path.replace('.csv', '_' + english_file_name + '.csv'))


def get_accidents_file_data(directory):
    for file_path in os.listdir(directory):
        if file_path.endswith("{0}{1}".format(CBS_FILES_HEBREW['klali'], '.csv')):
            return os.path.join(directory, file_path)


# def main(path):
#     update_cbs_files_names(path)
