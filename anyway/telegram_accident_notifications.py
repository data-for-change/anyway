from dataclasses import dataclass, asdict
from typing import List

import requests
from anyway import secrets
#import telegram
#from telegram import ParseMode
from anyway.models import NewsFlash
from anyway.parsers.infographics_data_cache_updater import is_in_cache
import telebot

INFOGRAPHIC_URL = "https://media.anyway.co.il/newsflash/"

def publish_notification(newsflash: NewsFlash):
    from anyway.slack_accident_notifications import fmt_lnk_mrkdwn

    bot_token = "5826636904:AAFy6lIfzYNA8IB8zZeUo7WhtLAyude4tis"
    bot_user_name = "boty"
    TOKEN = bot_token
    bot = telebot.TeleBot(bot_token)

    #notification = gen_notification(newsflash)
    #requests.post(secrets.get("SLACK_WEBHOOK_URL"), json=asdict(notification))
    chat_id = -790458867 #5826636904
    newsflash_id = 14680 #newsflash.id
#    msg_text = fmt_lnk_mrkdwn(f"{INFOGRAPHIC_URL}{newsflash_id}", "infographic")
    msg_text = "hi"
    sent_msg = bot.send_message(chat_id, msg_text, parse_mode="Markdown")

bot_token = "5826636904:AAFy6lIfzYNA8IB8zZeUo7WhtLAyude4tis"
bot_user_name = "boty"

# import everything
#from flask import Flask, request
#import telegram
#from telebot.credentials import bot_token, bot_user_name,URL
# global bot
# global TOKEN
#TOKEN = bot_token
#bot = telegram.Bot(token=TOKEN)

def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    #update = telegram.Update.de_json("miao", bot)

    #chat_id = update.message.chat.id
    chat_id = 5826636904
    msg_id = update.message.message_id

    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode()
    # for debugging purposes only
    print("got text message :", text)
    # the first time you chat with the bot AKA the welcoming message
    bot.sendMessage(chat_id=chat_id, text="miao")