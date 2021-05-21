from http import HTTPStatus


class Errors:
    BR_BAD_PHONE = 1
    BR_BAD_EMAIL = 2
    BR_NO_EMAIL = 3
    BR_FIRST_NAME_OR_LAST_NAME_MISSING = 4
    BR_BAD_JSON = 5
    BR_USER_NOT_LOGGED_IN = 6
    BR_USER_ALREADY_LOGGED_IN = 7
    BR_NO_USER_ID = 8
    BR_ONLY_SUPPORT_GOOGLE = 9
    BR_UNKNOWN_FIELD = 10
    BR_ROLE_NAME_MISSING = 11
    BR_ROLE_NOT_EXIST = 12
    BR_USER_NOT_FOUND = 13
    BR_USER_ALREADY_IN_ROLE = 14
    BR_MISSING_PERMISSION = 15
    BR_USER_NOT_IN_ROLE = 16
    BR_USER_NOT_ACTIVE = 17
    BR_BAD_ROLE_NAME = 18
    BR_ROLE_EXIST = 19
    BR_BAD_ROLE_DESCRIPTION = 20
    BR_ROLE_DESCRIPTION_MISSING = 21
    BR_NO_MODE = 22
    BR_BAD_MODE = 23


ERROR_TO_STRING_DICT = {
    Errors.BR_BAD_PHONE: "Bad Request (Bad phone number).",
    Errors.BR_BAD_EMAIL: "Bad Request (Bad email address).",
    Errors.BR_NO_EMAIL: "Bad Request (There is no email in our DB and there is no email in the json of this request).",
    Errors.BR_FIRST_NAME_OR_LAST_NAME_MISSING: "Bad Request (first name or last name is missing).",
    Errors.BR_BAD_JSON: "Bad Request (not a JSON or mimetype does not indicate JSON).",
    Errors.BR_USER_ALREADY_LOGGED_IN: "User is already logged in.",
    Errors.BR_USER_NOT_LOGGED_IN: "User not logged in.",
    Errors.BR_NO_USER_ID: "Couldn't get user id from the OAuth provider.",
    Errors.BR_ONLY_SUPPORT_GOOGLE: "Google is the only supported OAuth 2.0 provider.",
    Errors.BR_UNKNOWN_FIELD: "Bad Request (Unknown field {}).",
    Errors.BR_ROLE_NAME_MISSING: "Bad Request (Role name is missing from request json).",
    Errors.BR_ROLE_NOT_EXIST: "Bad Request (Role {} doesn't exist in DB).",
    Errors.BR_USER_NOT_FOUND: "Bad Request (User(email:{}) not found).",
    Errors.BR_USER_ALREADY_IN_ROLE: "Bad Request (User(email:{}) is already in role {}).",
    Errors.BR_MISSING_PERMISSION: "Bad Request (User is missing permission {}).",
    Errors.BR_USER_NOT_IN_ROLE: "Bad Request (User(email:{}) is not in role {}).",
    Errors.BR_USER_NOT_ACTIVE: "Bad Request (User is not active).",
    Errors.BR_BAD_ROLE_NAME: "Bad Request (Bad role name, need to be more then 2 char, less then 127 and only those chars - a-zA-Z0-9_-).",
    Errors.BR_ROLE_EXIST: "Bad Request (Role name already exists).",
    Errors.BR_BAD_ROLE_DESCRIPTION: "Bad Request (Bad role description, need to be less then 255 chars).",
    Errors.BR_ROLE_DESCRIPTION_MISSING: "Bad Request (Role description is missing from request json).",
    Errors.BR_NO_MODE: "Bad Request (Mode is missing from request json).",
    Errors.BR_BAD_MODE: "Bad Request (Bad mode value).",
}

ERROR_TO_HTTP_CODE_DICT = {
    Errors.BR_BAD_PHONE: HTTPStatus.BAD_REQUEST,
    Errors.BR_BAD_EMAIL: HTTPStatus.BAD_REQUEST,
    Errors.BR_NO_EMAIL: HTTPStatus.BAD_REQUEST,
    Errors.BR_FIRST_NAME_OR_LAST_NAME_MISSING: HTTPStatus.BAD_REQUEST,
    Errors.BR_BAD_JSON: HTTPStatus.BAD_REQUEST,
    Errors.BR_USER_ALREADY_LOGGED_IN: HTTPStatus.BAD_REQUEST,
    Errors.BR_USER_NOT_LOGGED_IN: HTTPStatus.UNAUTHORIZED,
    Errors.BR_NO_USER_ID: HTTPStatus.INTERNAL_SERVER_ERROR,
    Errors.BR_ONLY_SUPPORT_GOOGLE: HTTPStatus.BAD_REQUEST,
    Errors.BR_UNKNOWN_FIELD: HTTPStatus.BAD_REQUEST,
    Errors.BR_ROLE_NAME_MISSING: HTTPStatus.BAD_REQUEST,
    Errors.BR_ROLE_NOT_EXIST: HTTPStatus.BAD_REQUEST,
    Errors.BR_USER_NOT_FOUND: HTTPStatus.BAD_REQUEST,
    Errors.BR_USER_ALREADY_IN_ROLE: HTTPStatus.BAD_REQUEST,
    Errors.BR_MISSING_PERMISSION: HTTPStatus.UNAUTHORIZED,
    Errors.BR_USER_NOT_IN_ROLE: HTTPStatus.BAD_REQUEST,
    Errors.BR_USER_NOT_ACTIVE: HTTPStatus.UNAUTHORIZED,
    Errors.BR_BAD_ROLE_NAME: HTTPStatus.BAD_REQUEST,
    Errors.BR_ROLE_EXIST: HTTPStatus.BAD_REQUEST,
    Errors.BR_BAD_ROLE_DESCRIPTION: HTTPStatus.BAD_REQUEST,
    Errors.BR_ROLE_DESCRIPTION_MISSING: HTTPStatus.BAD_REQUEST,
    Errors.BR_NO_MODE: HTTPStatus.BAD_REQUEST,
    Errors.BR_BAD_MODE: HTTPStatus.BAD_REQUEST,
}


def build_json_for_user_api_error(error_code: int, argv) -> dict:
    if argv is None:
        error_msg = ERROR_TO_STRING_DICT[error_code]
    elif isinstance(argv, str):
        error_msg = ERROR_TO_STRING_DICT[error_code].format(argv)
    else:  # list or tuple
        error_msg = ERROR_TO_STRING_DICT[error_code].format(*argv)
    return {"error_code": error_code, "error_msg": error_msg}
