from flask import Flask, request
import json

app = Flask(__name__)

COMMUNICATION_PATH = "/comm/fifo"


@app.route("/<webhook>", methods=["POST"])
def hello_world(webhook: str):
    content = request.json
    if content is None:
        return "Content body not json", 415
    with open(COMMUNICATION_PATH, "w", encoding="utf-8") as commfile:
        commfile.write(json.dumps({"hook": webhook, "content": content}))
    return "Done", 200
