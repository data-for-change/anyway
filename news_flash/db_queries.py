import psycopg2


def get_latest_date_from_db():
    conn = psycopg2.connect("dbname=anyway_news_flash user=postgres password=123321")
    cur = conn.cursor()
    cur.execute("SELECT date FROM news_flash ORDER BY id DESC LIMIT 1")
    latest_date = cur.fetchone()
    cur.close()
    conn.close()
    if latest_date is None:
        return None
    return latest_date[0].replace(tzinfo=None)


def get_latest_id_from_db():
    conn = psycopg2.connect("dbname=anyway_news_flash user=postgres password=123321")
    cur = conn.cursor()
    cur.execute("SELECT id FROM news_flash ORDER BY id DESC LIMIT 1")
    id_flash = cur.fetchone()
    cur.close()
    conn.close()
    if id_flash is None:
        return -1
    return id_flash[0]
