from typing import Callable
import os
import logging

# Never log a secret key!
# Note that github-secrets are not accessible for PRs from forks.


def _get_secret_from_dir(secret_name: str) -> str:
    with open(secrets_dir + secret_name) as secret_file:
        return secret_file.read()


def _get_secret_must_exist(secret_name: str) -> str:
    return os.environ[secret_name]


def _try_get_secret(secret_name: str) -> str:
    return os.environ.get(secret_name)


global get
get: Callable[[str], str]

secrets_dir = "/run/secrets/"
if os.path.isdir(secrets_dir):
    get = _get_secret_from_dir
elif os.environ.get("FLASK_ENV") == "development":
    get = _try_get_secret
else:
    logging.info("Secrets dir found. Fallback to reading from environment.")
    get = _get_secret_must_exist


def exists(secret_name: str) -> bool:
    try:
        return bool(get(secret_name))
    except KeyError:
        return False
    except FileNotFoundError:
        return False
