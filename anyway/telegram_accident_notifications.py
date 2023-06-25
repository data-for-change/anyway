from anyway import secrets
import telebot
import boto3

INFOGRAPHICS_S3_BUCKET = "dfc-anyway-infographics-images"
TELEGRAM_CHAT_ID = -979313450


def publish_notification(newsflash_id):

    bot = telebot.TeleBot(secrets.get("TELEGRAM_BOT_TOKEN"))
#    sent_msg = bot.send_message(chat_id, msg_text)

    urls = create_public_urls_for_infographics_images(newsflash_id)
    for url in urls:
        bot.send_photo(TELEGRAM_CHAT_ID, url)


def create_public_urls_for_infographics_images(folder_name):
    S3_client = boto3.client('s3',
                 aws_access_key_id = secrets.get("AWS_ACCESS_KEY"),
                 aws_secret_access_key = secrets.get("AWS_SECRET_KEY")
                 )
    objects_contents = S3_client.list_objects_v2(Bucket=INFOGRAPHICS_S3_BUCKET,
                                                 Prefix=folder_name)["Contents"]
    keys = [object["Key"] for object in objects_contents]
    presigned_urls = []
    for key in keys:
        url = S3_client.generate_presigned_url('get_object', Params={'Bucket': INFOGRAPHICS_S3_BUCKET,
                                                       'Key': key})
        presigned_urls += [url]
    return presigned_urls