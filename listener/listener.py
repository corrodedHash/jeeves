import hashlib
import hmac
import json
import datetime
import random
import string
from pathlib import Path

import werkzeug.exceptions
from flask import Flask, request

app = Flask(__name__)

COMMUNICATION_PATH = Path("/comm/payloads/")
SECRET_PATH = Path("/comm") / "secrets.json"


def verify_github_signature(
    payload_body: bytes,
    secrets: dict[str, str],
    hookname: str,
    signature_header: str | None,
):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """

    if hookname not in secrets:
        raise werkzeug.exceptions.Forbidden("Unknown webhook")
    secret_token = secrets[hookname]

    if not signature_header:
        raise werkzeug.exceptions.Forbidden("x-hub-signature-256 header is missing!")
    hash_object = hmac.new(
        secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise werkzeug.exceptions.Forbidden("Request signatures didn't match!")


def generate_random_id(length=5):
    """Generate a random ID of specified length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


@app.route("/github/<webhook>", methods=["POST"])
def github_hook(webhook: str):
    content = request.data
    if content is None:
        raise werkzeug.exceptions.UnsupportedMediaType("Content body not json")

    with open(SECRET_PATH, "r", encoding="utf-8") as secretfile:
        secrets = json.load(secretfile)
    verify_github_signature(
        request.get_data(),
        secrets,
        webhook,
        request.headers.get("x-hub-signature-256", None),
    )
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = COMMUNICATION_PATH / f"{webhook}-{timestamp}-{generate_random_id(7)}"
    with open(output_name, "wb+") as commfile:
        commfile.write(content)
    return "Done", 200


@app.route("/skygitea/<webhook>", methods=["POST"])
def skygitea_hook(webhook: str):

    with open(SECRET_PATH, "r", encoding="utf-8") as secretfile:
        secrets = json.load(secretfile)
    verify_github_signature(
        request.get_data(),
        secrets,
        webhook,
        request.headers.get("x-hub-signature-256", None),
    )
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = COMMUNICATION_PATH / f"{webhook}-{timestamp}-{generate_random_id(7)}"
    with open(output_name, "wb+") as commfile:
        commfile.write(content)
    return "Done", 200
