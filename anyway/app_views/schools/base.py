from flask import render_template, Response
from flask import request

from anyway.base import user_optional


@user_optional
def schools():
    if request.method == "GET":
        return render_template('schools_dashboard_react.html')
    else:
        return Response("Method Not Allowed", 405)


@user_optional
def schools_report():
    if request.method == "GET":
        return render_template('schools_dashboard_react.html')
    else:
        return Response("Method Not Allowed", 405)
