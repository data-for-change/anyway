import gdown
import os

file_id = os.environ["GDRIVE_FILE_ID"]
url = os.environ["GDRIVE_URL"]
output = os.environ["DB_DUMP_PATH"]
url_with_id = url + file_id
gdown.download(url=url_with_id, output=output)
