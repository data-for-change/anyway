from dataclasses import dataclass


# This class is used for the OAUTH user data collection
@dataclass
class UserData:
    """
    From google the the data that is being received will be correlated as such:
    name can be "name" or "given_name+family_name"
    email is "email"
    service_user_id is "sub"
    service_user_domain is "hd" this is only relevant if the user has a business account? - not sure
    picture is "picture"
    user_profile_url is profile
    *When a field is missing(most of the time most of the fields will be missing) the value will be None
    """

    name: str
    email: str
    service_user_id: str
    service_user_domain: str
    service_user_locale: str
    picture_url: str
    user_profile_url: str
