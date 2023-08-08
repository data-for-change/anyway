import logging

from anyway import secrets
import telebot
import boto3
import time
import requests

ANYWAY_BASE_API_URL = "https://www.anyway.co.il/api"
INFOGRAPHICS_S3_BUCKET = "dfc-anyway-infographics-images"

TELEGRAM_CHANNEL_CHAT_ID = -1001666083560
TELEGRAM_LINKED_GROUP_CHAT_ID = -1001954877540
TEXT_FOR_AFTER_INFOGRAPHICS_MESSAGE = 'מקור המידע בלמ"ס. נתוני התאונה שבמבזק לא נכללים באינפוגרפיקה. ' \
                                      'הופק באמצעות ANYWAY מבית "נתון לשינוי" למידע נוסף:'

def send_initial_message_in_channel(bot, text):
    return bot.send_message(TELEGRAM_CHANNEL_CHAT_ID, text)


def fetch_message_id_for_initial_message_in_discussion_group(bot, thread_starting_message_in_channel):
    tries = 3
    for _ in range(tries):
        time.sleep(10)
        updates = bot.get_updates(allowed_updates=[])
        for update in updates:
            if update.message and update.message.content_type == "text" \
                    and update.message.forward_from_message_id == thread_starting_message_in_channel.message_id:
                return update.message.message_id
    logging.error("failed to fetch message id in group")
    return None


def remove_seconds_from_time_and_date(time_and_date):
    return time_and_date[:time_and_date.rindex(":")]


def create_accident_text(newsflash_id):
    newsflash = requests.get(f"{ANYWAY_BASE_API_URL}/news-flash/{newsflash_id}").json()
    organization = newsflash['organization']
    date_and_time = remove_seconds_from_time_and_date(newsflash['date'])
    first_line = f"[{organization}] {date_and_time}:"
    return f"{first_line}\n\n{newsflash['description']}"


def fetch_transcription_by_widget_name(newsflash_id):
    widgets_url = f"{ANYWAY_BASE_API_URL}/infographics-data?lang=he&news_flash_id={newsflash_id}&years_ago=5"
    widgets_json = requests.get(widgets_url).json()
    transcription_by_widget_name = {widget["name"]: widget["data"]["text"]["transcription"]
                                    for widget in widgets_json["widgets"]
                                    if "transcription" in widget["data"]["text"]}
    return transcription_by_widget_name


def send_after_infographics_message(bot, message_id_in_group, newsflash_id):
    newsflash_link = f"https://media.anyway.co.il/newsflash/{newsflash_id}"
    message = f"{TEXT_FOR_AFTER_INFOGRAPHICS_MESSAGE}\n{newsflash_link}"
    return bot.send_message(TELEGRAM_LINKED_GROUP_CHAT_ID, message, reply_to_message_id=message_id_in_group)

def publish_notification(newsflash_id):
    #fetch data for send
    accident_text = create_accident_text(newsflash_id)
    transcription_by_widget_name = fetch_transcription_by_widget_name(newsflash_id)
    urls_by_infographic_name = create_public_urls_for_infographics_images(str(newsflash_id))

    bot = telebot.TeleBot(secrets.get("BOT_TOKEN"))
    initial_message_in_channel = send_initial_message_in_channel(bot, accident_text)
    #every message in the channel is automatically forwarded to the linked discussion group.
    #to create a comment on the channel message, we need to send a reply to the
    #forwareded message in the discussion group.
    message_id_in_group = \
        fetch_message_id_for_initial_message_in_discussion_group(bot, initial_message_in_channel)

    if message_id_in_group:
        for infographic_name, url in urls_by_infographic_name.items():
            text = transcription_by_widget_name[infographic_name] \
                if infographic_name in transcription_by_widget_name else None
            bot.send_photo(TELEGRAM_LINKED_GROUP_CHAT_ID, url, reply_to_message_id=message_id_in_group, caption=text)
        send_after_infographics_message(bot, message_id_in_group, newsflash_id)
    logging.info("notification send done")

def extract_infographic_name_from_s3_object(s3_object_name):
    left = s3_object_name.rindex("/")
    right = s3_object_name.rindex(".")
    return s3_object_name[left + 1: right]


def create_public_urls_for_infographics_images(folder_name):
    S3_client = boto3.client('s3',
                             aws_access_key_id=secrets.get("AWS_ACCESS_KEY"),
                             aws_secret_access_key=secrets.get("AWS_SECRET_KEY")
                             )
    objects_contents = S3_client.list_objects_v2(Bucket=INFOGRAPHICS_S3_BUCKET,
                                                 Prefix=folder_name)["Contents"]
    presigned_urls = {}
    for object in objects_contents:
        key = object["Key"]
        url = S3_client.generate_presigned_url('get_object', Params={'Bucket': INFOGRAPHICS_S3_BUCKET,
                                                                     'Key': key})
        infographic_name = extract_infographic_name_from_s3_object(key)
        presigned_urls[infographic_name] = url
    return presigned_urls
