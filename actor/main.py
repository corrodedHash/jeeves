import argparse
import json
from typing import Any
import subprocess


def handle_hook(path: str, payload: Any):
    if path == "codenames":
        if payload.get("ref", None) != "refs/heads/main":
            return
        subprocess.run(
            ["git", "pull"],
            cwd="/home/maint/docker-setup/codenames/codenames/codenames",
            check=True,
        )
        subprocess.run(
            "docker compose up --build -d",
            cwd="/home/maint/docker-setup/codenames/codenames/codenames",
            check=True,
        )


def loop(path: str):
    while True:
        with open(path, "r", encoding="utf-8") as commfile:
            request = json.loads(commfile.read())
            hookname = request["hook"]
            hookcontent = request["content"]
            print(f"Handling hook '{hookname}'")
            handle_hook(hookname, hookcontent)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Actor",
        description="Actor receiving commands over a fifo pipe",
    )
    parser.add_argument("--commfile", "-c")

    args = parser.parse_args()
    loop(args.commfile)


if __name__ == "__main__":
    main()
