import json

import requests
import typing
from flask import current_app, url_for, request, redirect
from rauth import OAuth2Service

from anyway.dataclasses.user_data import UserData


class OAuthSignIn(object):
    providers = {}

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config["OAUTH_CREDENTIALS"][provider_name]
        self.consumer_id = credentials["id"]
        self.consumer_secret = credentials["secret"]

    def authorize(self):
        pass

    def callback(self) -> typing.Optional[UserData]:
        pass

    def get_callback_url(self):
        return url_for("oauth_callback", provider=self.provider_name, _external=True)

    @classmethod
    def get_provider(self, provider_name):
        # This is quick fix for the DEMO - to make sure that anyway.co.il is fully compatible with https://anyway-infographics-staging.web.app/
        if provider_name != "google":
            return None

        if not self.providers:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class FacebookSignIn(OAuthSignIn):
    def __init__(self):
        super(FacebookSignIn, self).__init__("facebook")
        self.service = OAuth2Service(
            name="facebook",
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url="https://graph.facebook.com/oauth/authorize",
            access_token_url="https://graph.facebook.com/oauth/access_token",
            base_url="https://graph.facebook.com/",
        )

    def authorize(self):
        return redirect(
            self.service.get_authorize_url(
                scope="email", response_type="code", redirect_uri=self.get_callback_url()
            )
        )

    def callback(self) -> typing.Optional[UserData]:
        if "code" not in request.args:
            return None
        oauth_session = self.service.get_auth_session(
            data={
                "code": request.args["code"],
                "grant_type": "authorization_code",
                "redirect_uri": self.get_callback_url(),
            },
            decoder=json.loads,
        )
        # TODO: enrich facebook data collection
        me = oauth_session.get("me?fields=id,email").json()
        name = me.get("email").split("@")[0],  # Facebook does not provide username, so the email's user is used instead
        data_of_user = UserData(name=name, email=me.get("email"), service_user_id="facebook$" + me["id"])


        return data_of_user


class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__("google")
        googleinfo = requests.get("https://accounts.google.com/.well-known/openid-configuration")
        googleinfo.raise_for_status()
        google_params = googleinfo.json()
        self.service = OAuth2Service(
            name="google",
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url=google_params.get("authorization_endpoint"),
            base_url=google_params.get("userinfo_endpoint"),
            access_token_url=google_params.get("token_endpoint"),
        )

    def authorize(self):
        return redirect(
            self.service.get_authorize_url(
                scope="email", response_type="code", redirect_uri=self.get_callback_url()
            )
        )

    def callback(self) -> typing.Optional[UserData]:
        if "code" not in request.args:
            return None
        oauth_session = self.service.get_auth_session(
            data={
                "code": request.args["code"],
                "grant_type": "authorization_code",
                "redirect_uri": self.get_callback_url(),
            },
            decoder=json.loads,
        )
        me = oauth_session.get("").json()
        # The data in me dict includes information about the user, as described in
        # OpenID Connect Standard Claims(https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims) and the
        # claims_supported metadata value of the Discovery document(https://accounts.google.com/.well-known/openid-configuration)
        # So in the best case we have "aud", "email", "email_verified", "exp", "family_name", "given_name", "iat",
        # "iss", "locale", "name", "picture", "sub"
        # and in the worst case we only have "sub".
        # Note - in some places in the docs there is an indication that more fields exists.
        name = me.get("name")
        if not name:
            if me.get("given_name"):
                name = me.get("given_name")
            if me.get("family_name"):
                name = f"{name} {me.get('family_name')}" if name else me.get("family_name")

        data_of_user = UserData(name=name, email=me.get("email"), service_user_id=me["sub"],
                                service_user_domain=me.get("hd"), service_user_locale=me.get("locale"),
                                picture_url=me.get("picture"), user_profile_url=me.get("profile"))

        return data_of_user

