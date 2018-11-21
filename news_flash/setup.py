from setuptools import setup

setup(
    name='news_flash',
    version='1.0.0',
    packages=[''],
    url='',
    license='',
    author='Mano',
    author_email='emanuelgarbin97@gmail.com',
    description='scraps flash news and stores in db', install_requires=['feedparser', 'scrapy', 'psycopg2', 'google',
                                                                        'googlemaps']
)
