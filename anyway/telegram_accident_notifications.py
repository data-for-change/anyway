import logging

from anyway import secrets
from anyway.models import TelegramForwardedMessages
from anyway.utilities import trigger_airflow_dag
from anyway.app_and_db import db
from anyway.infographics_utils import get_infographics_data_by_newsflash
import telebot
import boto3
import time
import requests

ANYWAY_BASE_API_URL = "https://www.anyway.co.il/api"
INFOGRAPHICS_S3_BUCKET = "dfc-anyway-infographics-images"

TELEGRAM_CHANNEL_CHAT_ID = "-1001666083560"
TELEGRAM_POST_VERIFICATION_CHANNEL_CHAT_ID = "-1002064130267"
TELEGRAM_LINKED_GROUP_CHAT_ID = -1001954877540
TELEGRAM_POST_VERIFICATION_LINKED_GROUP_CHAT_ID = -1001990172076
telegram_linked_group_by_channel = {TELEGRAM_CHANNEL_CHAT_ID: TELEGRAM_LINKED_GROUP_CHAT_ID,
                                    TELEGRAM_POST_VERIFICATION_CHANNEL_CHAT_ID: TELEGRAM_POST_VERIFICATION_LINKED_GROUP_CHAT_ID}
TEXT_FOR_AFTER_INFOGRAPHICS_MESSAGE = 'מקור המידע בלמ"ס. נתוני התאונה שבמבזק לא נכללים באינפוגרפיקה. ' \
                                      'הופק באמצעות ANYWAY מבית "נתון לשינוי" למידע נוסף:'

def send_initial_message_in_channel(bot, text, chat_id):
    return bot.send_message(chat_id, text)


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


def get_transcription_by_widget_name(widgets):
    transcription_by_widget_name = {widget["name"]: widget["data"]["text"]["transcription"]
                                    for widget in widgets
                                    if "transcription" in widget["data"]["text"]}
    return transcription_by_widget_name


def send_after_infographics_message(bot, message_id_in_group, newsflash_id, linked_group):
    newsflash_link = f"https://media.anyway.co.il/newsflash/{newsflash_id}"
    message = f"{TEXT_FOR_AFTER_INFOGRAPHICS_MESSAGE}\n{newsflash_link}"
    return bot.send_message(linked_group, message, reply_to_message_id=message_id_in_group)


#this function sends the "root" message for the newsflash in telegram.
#the flow continues when the telegram server sends a request to our /api/telegram/webhook
def publish_notification(newsflash_id, chat_id=TELEGRAM_CHANNEL_CHAT_ID):
    accident_text = create_accident_text(newsflash_id)
    bot = telebot.TeleBot(secrets.get("BOT_TOKEN"))
    initial_message_in_channel = send_initial_message_in_channel(bot, accident_text, chat_id)
    forwarded_message = TelegramForwardedMessages(message_id=initial_message_in_channel.message_id,
                                                  newsflash_id=newsflash_id,
                                                  group_sent=chat_id
                                                  )
    db.session.add(forwarded_message)
    db.session.commit()


def get_items_for_send(newsflash_id):
    items = []
    widgets = get_infographics_data_by_newsflash(newsflash_id)["widgets"]
    transcription_by_widget_name = get_transcription_by_widget_name(widgets)
    urls_by_infographic_name = create_public_urls_for_infographics_images(str(newsflash_id))
    for widget in widgets:
        name = widget.get("name")
        if name in urls_by_infographic_name:
            url = urls_by_infographic_name.get(name)
            text = transcription_by_widget_name.get(name)
            items.append((url, text))
    return items


def send_infographics_to_telegram(root_message_id, newsflash_id, channel_of_initial_message):
    #every message in the channel is automatically forwarded to the linked discussion group.
    #to create a comment on the channel message, we need to send a reply to the
    #forwareded message in the discussion group.
    bot = telebot.TeleBot(secrets.get("BOT_TOKEN"))

    linked_group = telegram_linked_group_by_channel[channel_of_initial_message]
    items_for_send = get_items_for_send(newsflash_id)
    for url, text in items_for_send:
        bot.send_photo(linked_group, url, reply_to_message_id=root_message_id, caption=text)

    send_after_infographics_message(bot, root_message_id, newsflash_id, linked_group)
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


def trigger_generate_infographics_and_send_to_telegram(newsflash_id, pre_verification_chat=True):
    dag_conf = {"news_flash_id": newsflash_id}
    dag_conf["chat_id"] = TELEGRAM_CHANNEL_CHAT_ID if pre_verification_chat \
        else TELEGRAM_POST_VERIFICATION_CHANNEL_CHAT_ID
    trigger_airflow_dag("generate-and-send-infographics-images", dag_conf)
