from get_mda_tweets import get_user_tweets
from anyway.utilities import init_flask
from flask_sqlalchemy import SQLAlchemy

app = init_flask()
db = SQLAlchemy(app)

def get_latest_tweet_id_from_db():
    tweet_id = db.session.execute('SELECT id FROM news_flash where source=\'twitter\' ORDER BY date DESC LIMIT 1').fetchone()
    return tweet_id[0]


if __name__ == "__main__":
    CONSUMER_KEY = 'E9dYIFqekzkQGCv6KbQWNLFQz'
    CONSUMER_SECRET = 'TiPAQqG76tXzvFBnRCVEIk6W9iIF7PmoPcSV1sHjl0LP7bKt9z'
    ACCESS_KEY = '4023017482-kDubkC77jz48soKqHRfpSiLqenFMeRUE10s2f2A'
    ACCESS_SECRET = 'un4FjkHNdRAjgkUlu4nv2wLF1etdcb0ClQIZovSWWbb6S'

    twitter_user = 'mda_israel'

    GOOGLE_MAPS_API_KEY = 'AIzaSyABPdbNQeWHizVpNptlIyHVsjCsj6BO1bM'

    latest_tweet_id = get_latest_tweet_id_from_db()

    mda_tweets = get_user_tweets(twitter_user, latest_tweet_id, CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET, GOOGLE_MAPS_API_KEY)