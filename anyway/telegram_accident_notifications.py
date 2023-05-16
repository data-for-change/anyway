
from anyway import secrets
from anyway.models import NewsFlash
import telebot

INFOGRAPHIC_URL = "https://media.anyway.co.il/newsflash/"

def publish_notification(newsflash: NewsFlash):
    from anyway.slack_accident_notifications import fmt_lnk_mrkdwn

    bot_token = "5826636904:AAFy6lIfzYNA8IB8zZeUo7WhtLAyude4tis"
    bot_user_name = "boty"
    TOKEN = bot_token
    bot = telebot.TeleBot(bot_token)

    chat_id = -790458867 #5826636904
    newsflash_id = 14680 #newsflash.idhttps://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.theguardian.com%2Flifeandstyle%2F2020%2Fsep%2F05%2Fwhat-cats-mean-by-miaow-japans-pet-guru-knows-just-what-your-feline-friend-wants&psig=AOvVaw3-OBnj2Q2HMs0SkdjGM2W4&ust=1682542879439000&source=images&cd=vfe&ved=0CBEQjRxqFwoTCIDCtOf2xf4CFQAAAAAdAAAAABAE
#    sent_msg = bot.send_message(chat_id, msg_text, parse_mode="Markdown")
    link = "https://i.guim.co.uk/img/media/26392d05302e02f7bf4eb143bb84c8097d09144b/446_167_3683_2210/master/3683.jpg?width=465&quality=85&dpr=1&s=none"
    bot.send_photo(chat_id, link)

bot_user_name = "boty"