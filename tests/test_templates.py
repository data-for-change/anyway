import os
import pytest
import re
from jinja2 import Environment
from webassets.ext.jinja2 import AssetsExtension


_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "../templates")
_environment = Environment(extensions=[AssetsExtension])

def _error_handler(e):
    raise e


def _iter_templates():
    for path, _, files in os.walk(_TEMPLATE_DIR, onerror=_error_handler):
        for filename in files:
            if filename.endswith('.html'):
                yield os.path.join(path, filename)


_TEMPLATE_FILES = list(_iter_templates())


@pytest.mark.parametrize("template_file", _TEMPLATE_FILES)
def test_no_trailing_spaces(template_file):
    with open(template_file, "r") as f:
        template = f.read()
        if re.search(r"[ \t]+$", template, flags=re.MULTILINE):
            raise Exception("Trailing spaces found in {}".format(os.path.abspath(template_file)))


@pytest.mark.parametrize("template_file", _TEMPLATE_FILES)
def test_template_syntax(template_file):
    with open(template_file, "r") as f:
        _environment.parse(f.read().decode("utf-8"))
