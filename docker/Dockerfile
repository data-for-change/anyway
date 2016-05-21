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
&& apt-get clean

# Create required aliases and env variables
RUN echo 'export DATABASE_URL=sqlite:///local.db' >> ~/.bashrc && \
echo 'alias anyway="cd ~/anyway && python main.py"' >> ~/.bashrc

# Fetch repo and install dependencies
RUN git clone https://github.com/hasadna/anyway && \
cd anyway && git pull origin dev && pip install -U setuptools && pip install -r requirements.txt

RUN export DATABASE_URL=sqlite:///local.db && cd anyway && python models.py && python process.py