import os
import logging

# Never log a secret key!
# Note that github-secrets are not accessible for PRs from forks.


def get(secret_name: str) -> str:
    env = os.environ.get("FLASK_ENV")
    logging.info("Reading secret for " + repr(secret_name))
    secrets_dir = "/run/secrets/"
    if os.path.isdir(secrets_dir):
        with open(secrets_dir + secret_name) as secret_file:
            return secret_file.read()
    logging.info("No secret dir found.")
    if env == "development":
        return os.environ.get(secret_name)
    else:
        return os.environ[secret_name]


def exists(secret_name: str) -> bool:
    try:
        return bool(get(secret_name))
    except KeyError:
        return False
