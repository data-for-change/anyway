# Anyway Tests

This document details all the tests which you can run to validate the code.

## Automated Tests

The automated tests run using Docker Compose, so install it following instructions in [DOCKER.md](DOCKER.md).

The tests run on a separate testing environment, start it using the following command:

```
sudo docker-compose -f docker-compose-tests.yml up -d --build
```

Wait for DB to be available:

```
docker exec db-tests psql -U anyway -d anyway -c "select 1"
```

Initialize the DB for tests:

```
docker exec anyway-tests alembic upgrade head
docker exec anyway-tests ./main.py process registered-vehicles
docker exec anyway-tests ./main.py process cbs --source local_dir_for_tests_only
```

Install test dependencies:

```
docker exec anyway-tests pip install -r ./test_requirements.txt
```

Run the full testing suite:

```
docker exec anyway-tests pytest -v tests -m "not browser"
```

Pytest has many options for filtering and running specific tests, some examples:

Run a specific test from a specific file with full verbose debug output:

```
docker exec anyway-tests pytest -svv tests/test_flask.py::test_markers
```

Pytest has a lot of options, see [pytest docs](https://docs.pytest.org/) for more details.

## Lint

The linters also run using the docker-compose test environment, so follow the automated tests instructions to set it up

Run the linters:

```
docker exec anyway-tests bin/pylint.sh
docker exec anyway-tests bin/black.sh
```
