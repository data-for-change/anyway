FROM partlab/ubuntu-java

# Use bash for environment setup
RUN ln -snf /bin/bash /bin/sh

# Install system tools
RUN apt-get -y update && apt-get install -y --no-install-recommends -qq build-essential \
git \
python-pip \
python-dev \
python-tk \
libpq-dev \
vim \
sqlite3 \
&& apt-get clean

# Create required aliases and env variables
RUN echo "export DATABASE_URL=sqlite:////anyway/local.db" >> ~/.bashrc

WORKDIR /anyway
EXPOSE 5000

ADD requirements.txt /anyway
RUN pip install -U setuptools
RUN pip install -r requirements.txt

ADD . /anyway

RUN export "DATABASE_URL=sqlite:////anyway/local.db" && python models.py && python process.py

#docker docker build -t hasdna/anyway .
#docker run -it -p 80:5000 --name anyway hasdna/anyway /bin/bash -c 'export DATABASE_URL=sqlite:////anyway/local.db && python main.py --open'