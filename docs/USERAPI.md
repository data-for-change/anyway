# User API documentation

This is the documentation for the new user API (Version 2) that was created in 2020.

Note: All the info about https://www.anyway.co.il is relevant to https://dev.anyway.co.il as well

### Authorization

#### Description

User authorization is been done with OAuth 2.0 and Google as the OAuth 2.0 provider. When calling the authentication URL you will
be redirected to Google OAuth system (So the user need to be able to see the screen), after Google will authenticate the user he will be redirected
to https://www.anyway.co.il/authorize/google/callback/google and from there the flow will be redirected to the URL that was given in
the param `redirect_url` or to the default URL.

#### URL struct

> GET https://www.anyway.co.il/authorize/google

#### Examples

> https://www.anyway.co.il/authorize/google

> http://127.0.0.1:5000/authorize/google?redirect_url=http%3A%2F%2F127.0.0.1%3A5000%2F

> http://127.0.0.1:5000/authorize/google?redirect_url=https%3A%2F%2Fanyway-infographics-staging.web.app%2Fxxxxxxxxxxxxxxxxxxxx

#### Parameters

**redirect_url** - _string_ This parameter is optional. The param is a URL, if set it will redirect(HTTP 302 code) to
the given URL after the authentication is finished, there is validation on the URL to prevent errors and malicious use:
For local address(127.0.0.1, localhost) you can access by one of the following scheme:
https or http, you can also add a port number and add a path after the domain. 
For non-local address you can only access one of the following domain:
> www.anyway.co.il  
> anyway-infographics-staging.web.app  
> anyway-infographics.web.app  
> anyway-infographics-demo.web.app  

only in https, but you can add any path you want after the domain.
#### Returns

If no error has occurred then you will be redirected to the given URL or to the default
URL(https://anyway-infographics.web.app/). Otherwise, you will get one of the errors described in the [errors](#Errors) section of
this document.

### User info update

#### Description

Update the user personal info. User must be logged in.

#### URL struct

> POST https://www.anyway.co.il/user/update

#### Example

> https://www.anyway.co.il/user/update

#### Parameters

There are no params that are passed in the URL query. All params should be passed as JSON in body of the POST request -
the following fields can be present in the JSON:  
**first_name** - _string_ ,Required, the user first name.  
**last_name** - _string_ ,Required, the user last name  
**email** - _string_ ,Required/Optional, if it was not given in the past(By the OAuth provider, or the user) then it is
Required else this Optional, this the email of the user  
**phone** - _string_ ,Optional, phone number, can be given with or without israeli calling code `+972`, can contain `-`, e.g. 03-1234567, 0541234567, 054-123-1234, +972-054-123-1234  
**user_type** - _string_ ,Optional, this param describe if the user is journalist / academic researcher or something else, valid values are:  

1. journalist
2. academic researcher
3. student
4. police
5. non-relevant professional
6. other

**user_url** - _string_ ,Optional, a URL to the user site  
**user_desc** - _string_ ,Optional, a self-description of the user  

Examples for good JSON:

```json
{
  "first_name": "a",
  "last_name": "a",
  "email": "aa@gmail.com"
}
```

```json
{
  "first_name": "a",
  "last_name": "a",
  "email": "aa@gmail.com",
  "phone": "0541234567",
  "user_type": "journalist",
  "user_url": "http:\\www.a.com",
  "user_desc": "Some text here."
}
```

#### Returns

If no error has occurred then you will get an empty HTTP 200 response. Otherwise, you will get one of the errors
described in the [errors](#Errors) section of this document.

### User registration

Registering a user is the same as running [Authorization](#Authorization) and after that [User info update](#User-info-update).
After the user has updated his info for the first time the user entry in the DB will be mark as registration completed.

### Get user info

#### Description

Return a JSON with the user info from the DB, User must be logged in.

#### URL struct

> GET https://www.anyway.co.il/user/info

#### Example

> https://www.anyway.co.il/user/info

#### Parameters

There are no params to pass.

#### Returns

If no error has occurred then you will get a JSON with an HTTP 200 response. Example of expected result:

```json
{
  "email": "ronemail@gmail.com",
  "first_name": "Ron",
  "id": 7,
  "is_active": true,
  "is_user_completed_registration": true,
  "last_name": "Cohen",
  "oauth_provider": "google",
  "oauth_provider_user_name": null,
  "oauth_provider_user_picture_url": "https://lh4.googleusercontent.com/SomeURL/photo.jpg",
  "phone": "0541234567",
  "user_desc": "A student in the Open university, and a part time journalist.",
  "user_register_date": "Thu, 24 Dec 2020 13:59:11 GMT",
  "user_type": "journalist",
  "user_url": "http:\\www.ynet.com",
  "roles": ["admins"]
}
```

**email** - _string_ ,What was given by the OAuth provider or by the user.  
**id** - _int_ ,Our id for this user.  
**is_active** - _bool_ ,Is the user active.  
**is_user_completed_registration** - _bool_ ,Have the user completed the registration process.  
**oauth_provider_user_name** - _string_ ,Sometimes we are given a username by the OAuth provider.  
**oauth_provider_user_picture_url** - _string_ ,A URL for a picture of the user(only available if the OAuth provider
have given us, Sometimes the OAuth provider is given us a blank picture).  
**phone** - _string_ , Phone number - e.g. 03-1234567, 0541234567, 054-123-1234, +972-054-123-1234  
**roles** - _[string]_ ,The roles assigned to the user - e.g. admins . . .   
Other fields are self-explanatory, so they are not described here.  
Otherwise, you will get one of the errors described in the [errors](#Errors) section of this document.

### Logout

#### Description

Logging out the user.

#### URL struct

> GET https://www.anyway.co.il/logout

#### Example

> https://www.anyway.co.il/logout

#### Parameters

There are no params to pass.

#### Returns

You will get HTTP 200 response.

### Enable/Disable user

#### Description

Enable or disable a user, this API doesn't delete the user from the DB,
user with admin rights must be logged in to use this api.  
An inactive user (disabled user) can't log in to the site.

#### URL struct

> POST https://www.anyway.co.il/user/change_user_active_mode

#### Example

> https://www.anyway.co.il/user/change_user_active_mode

#### Parameters
JSON with the fields:  
**email** - _string_ ,Required , email.  
**mode** - _bool_ ,Required , true for active, false for inactive/disabled user.  

#### Returns

If no error has occurred then you will get an empty HTTP 200 response. Otherwise, you will get one of the errors
described in the [errors](#Errors) section of this document.

### Add a role to DB

#### Description

Add a role to DB, user with admin rights must be logged in to use this api.

#### URL struct

> POST https://www.anyway.co.il/user/add_role

#### Example

> https://www.anyway.co.il/user/add_role

#### Parameters
JSON with the fields:  
**name** - _string_ ,Required, at lest 2 chars and less than 127 chars, can contain only chars from regex "a-zA-Z0-9_-".  
**description** - _string_ ,Required, up to 255 chars.

#### Returns

If no error has occurred then you will get an empty HTTP 200 response. Otherwise, you will get one of the errors
described in the [errors](#Errors) section of this document.

### Add user to role

#### Description

Add user to role, user with admin rights must be logged in to use this api.

#### URL struct

> POST https://www.anyway.co.il/user/add_to_role

#### Example

> https://www.anyway.co.il/user/add_to_role

#### Parameters
JSON with the fields:  
**role** - _string_ ,Required, a role from the DB.  
**email** - _string_ , Required, email of the user that will be added to the role.

#### Returns

If no error has occurred then you will get an empty HTTP 200 response. Otherwise, you will get one of the errors
described in the [errors](#Errors) section of this document.

### Remove user from role

#### Description

Remove user from role, user with admin rights must be logged in to use this api.

#### URL struct

> POST https://www.anyway.co.il/user/remove_from_role

#### Example

> https://www.anyway.co.il/user/remove_from_role

#### Parameters
JSON with the fields:  
**role** - _string_ ,Required, a role from the DB.  
**email** - _string_ , Required, email of the user that will be removed from the role.

#### Returns

If no error has occurred then you will get an empty HTTP 200 response. Otherwise, you will get one of the errors
described in the [errors](#Errors) section of this document.

### Get roles list from DB

#### Description

Return a JSON with a list of roles in the DB, user with admin rights must be logged in to use this api.

#### URL struct

> GET https://www.anyway.co.il/get_roles_list

#### Example

> https://www.anyway.co.il/get_roles_list

#### Parameters

There are no params to pass.

#### Returns

If no error has occurred then you will get a JSON with an HTTP 200 response. Example of expected result:

```json
[
    {
        "id": 1,
        "name": "admins",
        "description": "This is the default admin role."
    },
    {
        "id": 2,
        "name": "or_yarok",
        "description": "This is the role for or yarok members."
    }
]
```

struct:

[  
{  
**id** - _int_ ,Id of the role, int.  
**name** - _string_ , Name of the role.  
**description** - _string_ , Name of the role.  
}  
]  

Otherwise, you will get one of the errors described in the [errors](#Errors) section of this document.


### Get infographic data

#### Description

This is a partial documentation of this API (only what is user specific).  
This API allows user specific and user unspecific data retrieval of infographic data.

#### URL struct

> GET https://www.anyway.co.il/api/infographics-data

#### Example

> https://www.anyway.co.il/api/infographics-data?lang=he&news_flash_id=38203&years_ago=5&personalized=true
> 
> https://www.anyway.co.il/api/infographics-data?lang=he&news_flash_id=38203&years_ago=5

#### Parameters

**personalized** - _bool_ ,Optional, Get user specific infographic data.  

And other params that are not documented here. . . 

#### Returns

If no error has occurred then you will get a JSON with HTTP 200 response.   
In some cases of error (like user not logged in and personalized=true) you will receive user unspecific data.


### Errors

There are 2 types of error - Application errors(created by our code and described in this document) and framework
errors(e.g. Flask error, those can be in difference format then what describe here, like HTML). Example for an error:

```json
{
  "error_code": 4,
  "error_msg": "Bad Request (first name or last name is missing)."
}
```

### Get users list with info

#### Description

Return a JSON with the users list info from the DB, user with admin rights must be logged in to use this api.

#### URL struct

> GET https://www.anyway.co.il/user/get_all_users_info

#### Example

> https://www.anyway.co.il/user/get_all_users_info

#### Parameters

There are no params to pass.

#### Returns

If no error has occurred then you will get a JSON with an HTTP 200 response. Example of expected result:

```json
[
  {
    "email": "vvvvv@gmail.com",
    "first_name": "Ron",
    "id": 14,
    "is_active": true,
    "is_user_completed_registration": true,
    "last_name": "Cohen",
    "oauth_provider": "google",
    "oauth_provider_user_name": null,
    "oauth_provider_user_picture_url": "https://lh3.googleusercontent.com/a/default-user=s96-c",
    "phone": "0541234567",
    "roles": [
      
    ],
    "user_desc": "A student in the Open university, and a part time journalist.",
    "user_register_date": "Wed, 02 Jun 2021 21:00:08 GMT",
    "user_type": "journalist",
    "user_url": "http:\\www.ynet.com"
  }
]
```
each dict object in the list has the following struct:  
**email** - _string_ ,What was given by the OAuth provider or by the user.  
**id** - _int_ ,Our id for this user.  
**is_active** - _bool_ ,Is the user active.  
**is_user_completed_registration** - _bool_ ,Have the user completed the registration process.  
**oauth_provider_user_name** - _string_ ,Sometimes we are given a username by the OAuth provider.  
**oauth_provider_user_picture_url** - _string_ ,A URL for a picture of the user(only available if the OAuth provider
have given us, Sometimes the OAuth provider is given us a blank picture).  
**phone** - _string_ , Phone number - e.g. 03-1234567, 0541234567, 054-123-1234, +972-054-123-1234  
**roles** - _[string]_ ,The roles assigned to the user - e.g. admins . . .   
Other fields are self-explanatory, so they are not described here.  
Otherwise, you will get one of the errors described in the [errors](#Errors) section of this document.

### User info update by admin

#### Description

Update the user's info in the DB, user with admin rights must be logged in to use this api.

#### URL struct

> POST https://www.anyway.co.il/user/update_user

#### Example

> https://www.anyway.co.il/user/update_user

#### Parameters

There are no params that are passed in the URL query. All params should be passed as JSON in body of the POST request -
the following fields must be present in the JSON:  
**user_current_email** - _string_ ,Required, the "id" of the relevant user.  
**email** - _string_ ,Required, new email.  
**first_name** - _string_ ,Required, the user first name.  
**is_user_completed_registration** - _bool_, Required, self-explanatory.  
**last_name** - _string_ ,Required, the user last name.  
**phone** - _string_ ,Required, phone number, can be given with or without israeli calling code `+972`, can contain `-`, e.g. 03-1234567, 0541234567, 054-123-1234, +972-054-123-1234  
**user_desc** - _string_ ,Required, a self-description of the user  
**user_type** - _string_ ,Required, this param describe if the user is journalist / academic researcher or something else, valid values are:  

1. journalist
2. academic researcher
3. student
4. police
5. non-relevant professional
6. other

**user_url** - _string_ ,Required, a URL to the user site  

Please note that all fields are Required, if no change was made in one of the field then send the same value as you got 
from the [Get users list with info](# Get users list with info) API.

Examples for good JSON:
```json
{
  "user_current_email": "aaaa@gmail.com",
  "email": "vvvvv@gmail.com",
  "first_name": "Ron",
  "is_user_completed_registration": true,
  "last_name": "Cohen",
  "phone": "0541234567",
  "user_desc": "A student in the Open university, and a part time journalist.",
  "user_type": "journalist",
  "user_url": "http:\\www.ynet.com"
}
```

#### Returns

If no error has occurred then you will get an empty HTTP 200 response. Otherwise, you will get one of the errors
described in the [errors](#Errors) section of this document.

#### Error table:

| Error name                          | Error code | Error msg                                                                                    | HTTP return Code |
|-------------------------------------|------------|----------------------------------------------------------------------------------------------|------------------|
| Invalid phone number                | 1          | Bad Request (Bad phone number).                                                              | 400              |
| Invalid email                       | 2          | Bad Request (Bad email address).                                                             | 400              |
| No email address was given          | 3          | Bad Request (There is no email in our DB and there is no email in the json of this request). | 400              |
| Missing last name or first name     | 4          | Bad Request (first name or last name is missing).                                            | 400              |
| Invalid JSON or no JSON mimetype    | 5          | Bad Request (not a JSON or mimetype does not indicate JSON).                                 | 400              |
| User not logged in                  | 6          | User not logged in.                                                                          | 401              |
| User is already logged in           | 7          | User is already logged in.                                                                   | 400              |
| No user id                          | 8          | Couldn't get user id from the OAuth provider.                                                | 500              |
| Bad OAuth provider                  | 9          | Google is the only supported OAuth 2.0 provider.                                             | 400              |
| JSON with unknown field             | 10         | Bad Request (Unknown field {}).                                                              | 400              |
| JSON without role name              | 11         | Bad Request (Role name is missing from request json).                                        | 400              |
| Role name is not in DB              | 12         | Bad Request (Role {} doesn't exist in DB).                                                   | 400              |
| User not found                      | 13         | Bad Request (User(email:{}) not found).                                                      | 400              |
| User is already member in role      | 14         | Bad Request (User(email:{}) is already in role {}).                                          | 400              |
| User is missing permission          | 15         | Bad Request (User is missing permission {}).                                                 | 401              |
| User is not in role                 | 16         | Bad Request (User(email:{}) is not in role {}).                                              | 400              |
| User is not active                  | 17         | Bad Request (User is not active).                                                            | 401              |
| Invalid role name                   | 18         | Bad Request (Bad role name, need to be more then 2 char, less then 127 and only those chars - a-zA-Z0-9_-). | 400              |
| Role name already exists            | 19         | Bad Request (Role name already exists).                                                      | 400              |
| Invalid role description            | 20         | Bad Request (Bad role description, need to be less then 255 chars).                          | 400              |
| Role description is missing         | 21         | Bad Request (Role description is missing from request json).                                 | 400              |
| Missing mode in json                | 22         | Bad Request (Mode is missing from request json).                                             | 400              |
| Invalid mode value                  | 23         | Bad Request (Bad mode value).                                                                | 400              |
| Field missing                       | 24         | Bad Request (Field {} is missing from json).                                                 | 400              |


