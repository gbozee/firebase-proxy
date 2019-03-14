import bottle
import json
import firebase_admin
from firebase_admin import credentials, auth
from bottle import abort

cred = credentials.Certificate("credentials.json")
default_app = firebase_admin.initialize_app(cred)

application = bottle.Bottle(autojson=True)


def get_agent_details(email_password):
    pass


def get_or_create_user_from_firebase(result, password):
    try:
        user = auth.get_user_by_email(result["email"])
    except firebase_admin.auth.AuthError:
        user = auth.create_user(
            email=result["email"],
            email_verified=True,
            phone_number=result["phone"],
            password=password,
            display_name=result["full_name"],
            disabled=False,
        )
    return user


@application.hook("after_request")
def enable_cors():
    """
    You need to add some headers to each request.
    Don't use the wildcard '*' for Access-Control-Allow-Origin in production.
    """
    bottle.response.headers["Access-Control-Allow-Origin"] = "*"
    bottle.response.headers["Access-Control-Allow-Methods"] = "PUT, GET, POST, DELETE, OPTIONS"
    bottle.response.headers[
        "Access-Control-Allow-Headers"
    ] = "Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token"


@application.error(400)
def error400(error):
    bottle.response.set_header("Content-Type", "application/json")

    return json.dumps({"error": error.body})


@application.post("/login")
def login_user():
    json_get = bottle.request.json
    email = json_get.get("email")
    password = json_get.get("password")
    validate_tuteria = json_get.get("validate_server")
    if email and password:
        if validate_tuteria:
            result = get_agent_details(email, password)
            if result:
                user = get_or_create_user_from_firebase(result, password)
            else:
                abort(400, "Not Authorized")
        else:
            try:
                user = auth.get_user_by_email(email)
            except firebase_admin.auth.AuthError:
                abort(400, "Not Authorized")
        token = auth.create_custom_token(user.uid).decode()
        return {
            "token": token,
            "details": {
                "display_name": user.display_name,
                "uid": user.uid,
                "email": user.email,
            },
        }
    abort(400, "The credentials passed are invalid")


@application.get("/error")
def sample_error():
    bottle.abort(400, {"Error Message"})


@application.get("/")
def index():
    return {"hello": "world"}


if __name__ == "__main__":
    bottle.run(application, port=8000, debug=True, reloader=True)
