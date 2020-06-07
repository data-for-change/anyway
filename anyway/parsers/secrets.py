import os
from functools import lru_cache
import logging

# Never log a secret key!
# Note that github-secrets are not accessible for PRs from forks.

SECRETS_DIR = "/run/secrets/"
IS_SECRET_DIR = os.path.isdir(SECRETS_DIR)

if IS_SECRET_DIR:

    @lru_cache(10, typed=True)
    def get(secret_name: str) -> str:
        logging.info("Reading secret for " + repr(secret_name))
        with open(SECRETS_DIR + secret_name) as secret_file:
            return secret_file.read()


else:

    def get(secret_name: str) -> str:
        logging.info("Reading secret for " + repr(secret_name))
        return os.environ[secret_name]


def exists(secret_name: str) -> bool:
    try:
        return bool(get(secret_name))
    except KeyError:
        return False
