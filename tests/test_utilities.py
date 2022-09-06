from anyway import config
from anyway.utilities import is_valid_number, is_a_safe_redirect_url, split_query_to_chunks, TableForTest
from anyway.app_and_db import db
from sqlalchemy import Column, Integer
from sqlalchemy.inspection import inspect

# The main logic is implemented in external library, the only reason for this test is to make sure that this library
# will continue to support israeli numbers
def test_validate_phone():
    # Bad numbers
    short_numbers = [
        "1",
        "+213",
        "+9721234",
        "972234",
        "0541243",
        "+213",
        "+972-1234",
        "972-234",
        "054-1243",
    ]
    long_numbers = [
        "+9721234567890",
        "031234567890",
        "0541246805232",
        "+972-123-456-7890",
        "03123-4567-890",
        "05412-4680-5232",
    ]
    # Good number
    good_numbers = [
        "+9720541234567",
        "+972541234567",
        "+97254-123-4567",
        "+972-54-123-4567",
        "+972-03-123-4567",
        "03-123-4567",
        "031234567",
        "0541234567",
        "054-1234567",
        "054-123-4567",
        "+972-054-123-4567",
    ]

    for phone in short_numbers + long_numbers:
        assert not is_valid_number(phone)

    for phone in good_numbers:
        assert is_valid_number(phone)


def test_url_redirect_checker():
    bad_urls = [
        "127,0.0.1",
        "127,0.0.1:50",
        "127.0.0.a:50",
        "127.0.0.1:50a",
        "https://127.0.0.a:50",
        "https://127.0.0.2:50",
        "https://127.0.0.1:50a",
        "https://127.0.0.1:a",
        "https://127.0.0.1:12345678",
        "https://127.0.0.1:12345678",
        "https://127.0.0.1.com",
        "127.0.0.1:50/test" "127.0.0.1",
        "127.0.0.1:50",
        "www.anyway.co.il",
        "https://www.anyway.com",
        "anyway.co.il",
        "https//cnn.com",
        "https//www.cnn.com",
        "https://www.anyway.co.il.com",
        "http://www.anyway.co.il.com",
        "https://anyway.com",
        "www.anyway-infographics-staging.web.app",
        "https://anyway-infographics-staging.web.app.com",
        "anyway-infographics-staging.web.app.com",
        "anyway-infographics-staging.web.app",
        "anyway-infographics-staging.web.app/test",
        "localhost",
        "localhost:8000",
        "localhost.com",
        "anyway-infographics.web.app",
        "anyway-infographics-demo.web.app",
        "https://www.dev.anyway.co.il",
        "dev.anyway.co.il",
        "www.dev.anyway.co.il",
    ]

    good_urls = [
        "https://127.0.0.1",
        "https://127.0.0.1:50",
        "http://localhost",
        "http://localhost:8000",
        "https://127.0.0.1:50/test",
        "https://www.anyway.co.il/test",
        "https://www.anyway.co.il",
        "https://anyway-infographics-staging.web.app",
        "https://anyway-infographics-staging.web.app/test",
        "https://anyway-infographics.web.app",
        "https://anyway-infographics-demo.web.app",
    ]

    for url in bad_urls:
        assert not is_a_safe_redirect_url(url)

    for url in good_urls:
        assert is_a_safe_redirect_url(url)


def test_url_redirect_checker_dev():
    config.SERVER_ENV = "dev"
    bad_urls = [
        "dev.anyway.co.il",
        "www.dev.anyway.co.il",
    ]

    good_urls = [
        "https://www.dev.anyway.co.il",
        "https://dev.anyway.co.il",
    ]

    for url in bad_urls:
        assert not is_a_safe_redirect_url(url)

    for url in good_urls:
        assert is_a_safe_redirect_url(url)


def test_split_query_to_chunks():
    data_for_less_then_chunk_size = [{"id": 1}]
    with TableForTest().create_table_with_data(db, "table_for_test1",
                                               [Column('id', Integer, primary_key=True)],
                                               data_for_less_then_chunk_size) as table:
        results = [x for x in split_query_to_chunks(db.session.query(table), inspect(table).primary_key, 2)]
        assert results == [[{'id': 1}]]

    data_for_data_size_divisive_by_chunk_size = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
    with TableForTest().create_table_with_data(db, "table_for_test2",
                                               [Column('id', Integer, primary_key=True)],
                                               data_for_data_size_divisive_by_chunk_size) as table:
        results = [x for x in split_query_to_chunks(db.session.query(table), inspect(table).primary_key, 2)]
        assert results == [[{'id': 1}, {'id': 2}], [{'id': 3}, {'id': 4}], []]

    data_for_data_size_larger_than_chunk_size = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]
    with TableForTest().create_table_with_data(db, "table_for_test3",
                                               [Column('id', Integer, primary_key=True)],
                                               data_for_data_size_larger_than_chunk_size) as table:
        results = [x for x in split_query_to_chunks(db.session.query(table), inspect(table).primary_key, 2)]
        assert results == [[{'id': 1}, {'id': 2}], [{'id': 3}, {'id': 4}], [{'id': 5}]]

    data_for_two_primary_keys = [{"first": 1, "second": 2},
                                 {"first": 1, "second": 1},
                                 {"first": 2, "second": 2},
                                 {"first": 2, "second": 1}]
    with TableForTest().create_table_with_data(db, "table_for_test4",
                                               [Column('first', Integer, primary_key=True),
                                                Column('second', Integer, primary_key=True)],
                                               data_for_two_primary_keys) as table:
        results = [x for x in split_query_to_chunks(db.session.query(table), inspect(table).primary_key, 2)]
        assert results == [[{"first": 1, "second": 1}, {"first": 1, "second": 2}],
                           [{"first": 2, "second": 1}, {"first": 2, "second": 2}],
                           []]
