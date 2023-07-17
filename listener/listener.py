import hashlib
import hmac
import json

import werkzeug.exceptions
from flask import Flask, request

app = Flask(__name__)

COMMUNICATION_PATH = "/comm/fifo"
GITHUB_SECRET_PATH = "/comm/github_secrets.json"


def verify_signature(payload_body: bytes, hookname: str, signature_header: str | None):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """

    with open(GITHUB_SECRET_PATH, "r", encoding="utf-8") as secretfile:
        secrets = json.load(secretfile)
        if hookname not in secrets:
            return
        secret_token = secrets[hookname]

    if not signature_header:
        raise werkzeug.exceptions.Forbidden("x-hub-signature-256 header is missing!")
    hash_object = hmac.new(
        secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise werkzeug.exceptions.Forbidden("Request signatures didn't match!")


@app.route("/github/<webhook>", methods=["POST"])
def hello_world(webhook: str):
    content = request.json
    if content is None:
        raise werkzeug.exceptions.UnsupportedMediaType("Content body not json")
    verify_signature(
        request.get_data(), webhook, request.headers.get("x-hub-signature-256", None)
    )
    with open(COMMUNICATION_PATH, "w", encoding="utf-8") as commfile:
        json.dump({"hook": webhook, "source": "GITHUB", "content": content}, commfile)
    return "Done", 200
