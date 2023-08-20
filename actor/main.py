import argparse
import json
from typing import Any
import subprocess
import sys
from pathlib import Path


def handle_codenames(payload: Any) -> None:
    if payload.get("ref", None) != "refs/heads/main":
        return
    subprocess.run(
        ["runuser", "-u", "maint", "--", "git", "pull"],
        cwd="/home/maint/docker-setup/codenames/codenames/codenames",
        check=True,
    )
    subprocess.run(
        ["docker", "compose", "up", "--build", "-d"],
        cwd="/home/maint/docker-setup/codenames/",
        check=True,
    )


def handle_apps(payload: Any) -> None:
    for x in Path("/home/maint/docker-setup/apps/apps-docker/apps-auto").iterdir():
        if not x.is_dir():
            return
        print(x, x.absolute())
        subprocess.run(
            ["runuser", "-u", "maint", "--", "git", "pull"],
            cwd=str(x),
            check=True,
        )
    subprocess.run(
        ["docker", "compose", "up", "--build", "-d"],
        cwd="/home/maint/docker-setup/apps",
        check=True,
    )


def handle_jeeves(payload: Any) -> None:
    subprocess.run(
        ["runuser", "-u", "maint", "--", "git", "pull"],
        cwd="/home/maint/docker-setup/jeeves/jeeves",
        check=True,
    )
    subprocess.run(
        [
            "cp",
            "jeeves/actor/jeeves_actor.service",
            "/etc/systemd/system/jeeves_actor.service",
        ],
        cwd="/home/maint/docker-setup/jeeves/",
        check=True,
    )
    subprocess.run(
        ["systemctl", "restart", "jeeves_actor"],
        check=True,
    )
    subprocess.run(
        ["systemctl", "daemon-reload"],
        check=True,
    )


def handle_hook(path: str, payload: Any) -> None:
    if path == "codenames":
        handle_codenames(payload)
    elif path.startswith("apps-"):
        handle_apps(payload)
    elif path == "jeeves":
        handle_jeeves(payload)
    else:
        print(f"Unknown path: {path}", file=sys.stderr)


def loop(path: str) -> None:
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
