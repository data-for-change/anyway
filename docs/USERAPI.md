# User API documentation

This is the documentation for the new user API (and only the new one) that was created in 2020.

## Authorization

### Description

User authorization is been done with OAuth 2.0 and Google as the OAuth 2.0 provider. When calling the authentication URL you will
be redirected to Google OAuth system (So the user need to be able to see the screen), after Google will authenticate the user he will be redirected
to https://www.anyway.co.il/authorize/google/callback/google and from there the flow will be redirected to the URL that was given in
the param `redirect_url` or to the default URL.

### URL struct

> https://www.anyway.co.il/authorize/google

### Method

> GET

### Example

> https://www.anyway.co.il/authorize/google

> http://127.0.0.1:5000/authorize/google?redirect_url=http%3A%2F%2F127.0.0.1%3A5000%2F

> http://127.0.0.1:5000/authorize/google?redirect_url=https%3A%2F%2Fanyway-infographics-staging.web.app%2Fxxxxxxxxxxxxxxxxxxxx

### Parameters

**redirect_url** - _string_ This parameter is optional. The param is a URL, if set it will redirect(HTTP 302 code) to
the given URL after the authentication is finished, there is validation on the URL to prevent errors and malicious use:
For local address(127.0.0.1, localhost) you can access by one of the following scheme:
https or http, you can also add a port number and add a path after the domain. 
For non-local address you can only access one of the following domain:
> www.anyway.co.il  
> anyway-infographics-staging.web.app  
> anyway-infographics.web.app  
> anyway-infographics-demo.web.app  

only in https but you can add any path you want after the domain.
### Returns

If no error has occurred then you will be redirected to the given URL or to the default
URL(https://anyway-infographics.web.app/). Otherwise, you will get one of the errors described in the [errors](#Errors) section of
this document.

## User info update

### Description

Update the user personal info. User must be logged in.

### URL struct

> https://www.anyway.co.il/user/update

### Method

> POST

### Example

> https://www.anyway.co.il/user/update

### Parameters

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

**user_work_place** - _string_ ,Optional, the place the user work - Ynet, Police, Tel aviv university . . .  
**user_url** - _string_ ,Optional, a URL to the user site  
**user_desc** - _string_ ,Optional, a self description of the user  

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
  "user_work_place": "ynet",
  "user_url": "http:\\www.a.com",
  "user_desc": "Some text here."
}
```

### Returns

If no error has occurred then you will get an empty HTTP 200 response. Otherwise, you will get one of the errors
described in the [errors](#Errors) section of this document.

## User registration

Registering a user is the same as running [Authorization](#Authorization) and after that [User info update](#User-info-update).
After the user has updated his info for the first time the user entry in the DB will be mark as registration completed.

## Get user info

### Description

Return a JSON with the user info from the DB, User must be logged in.

### URL struct

> https://www.anyway.co.il/user/info

### Method

> GET

### Example

> https://www.anyway.co.il/user/info

### Parameters

There are no params to pass.

### Returns

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
  "work_on_behalf_of_organization": "ynet"
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

Other fields are self-explanatory, so they are not described here.  
Otherwise, you will get one of the errors described in the [errors](#Errors) section of this document.

## Errors

There are 2 types of error - Application errors(created by our code and described in this document) and framework
errors(e.g. Flask error, those can be in difference format then what describe here, like HTML). Example for an error:

```json
{
  "error_code": 4,
  "error_msg": "Bad Request (first name or last name is missing)."
}
```

Error table:
------------

| Error name                          | Error code | Error msg                                                                                    | HTTP return Code |
|-------------------------------------|------------|----------------------------------------------------------------------------------------------|------------------|
| Bad phone number                    | 1          | Bad Request (Bad phone number).                                                              | 400              |
| Bad email                           | 2          | Bad Request (Bad email address).                                                             | 400              |
| No email address was given          | 3          | Bad Request (There is no email in our DB and there is no email in the json of this request). | 400              |
| Missing last name or first name     | 4          | Bad Request (first name or last name is missing).                                            | 400              |
| Bad JSON or no indication of a JSON | 5          | Bad Request (not a JSON or mimetype does not indicate JSON).                                 | 400              |
| User not logged in                  | 6          | User not logged in.                                                                          | 401              |
| User is already logged in           | 7          | User is already logged in.                                                                   | 400              |
| No user id                          | 8          | Couldn't get user id from the OAuth provider.                                                | 500              |
| Bad OAuth provider                  | 9          | Google is the only supported OAuth 2.0 provider.                                             | 400              |
| JSON with unknown field             | 10         | Bad Request (Unknown field {}).                                                              | 400              |
