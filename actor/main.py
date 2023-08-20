import argparse
import json
from typing import Any
import subprocess

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


def handle_hook(path: str, payload: Any) -> None:
    if path == "codenames":
        handle_codenames(payload)
        return
    if path.startswith("apps-"):
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
