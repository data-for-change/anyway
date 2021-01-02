from anyway.utilities import is_valid_number, is_a_safe_redirect_url
from anyway.utilities import parse_age_from_range


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
        "https//www.cnn.com" "https://www.anyway.co.il.com",
        "http://www.anyway.co.il.com",
        "https://anyway.com" "www.anyway-infographics-staging.web.app",
        "https://anyway-infographics-staging.web.app.com" "anyway-infographics-staging.web.app.com",
        "anyway-infographics-staging.web.app",
        "anyway-infographics-staging.web.app/test",
        "localhost",
        "localhost:8000",
        "localhost.com",
        "anyway-infographics.web.app",
        "anyway-infographics-demo.web.app",
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


def test_parse_age_from_range():
    bad_values = [
        "",
        "adf",
        "0-1234",
        "12-23-45",
        "12+14",
        "1a-12",
        "12",
        "12123123",
        "1213-123",
        "12++",
        "12--",
        "0-5",
        "14-r3",
    ]

    good_values = {
        "01-25": (1, 25),
        "06-89": (6, 89),
        "98-99": (98, 99),
        "99-120": (99, 120),
        "101-120": (101, 120),
        "01-03": (1, 3),
        "12+": (12, 200),
        "123+": (123, 200),
    }

    for bad in bad_values:
        assert parse_age_from_range(bad) is None

    for key, value in good_values.items():
        assert parse_age_from_range(key) == value
