"""Main function for jeeves actor"""

import argparse
import json
from typing import Any
import subprocess
import sys
from pathlib import Path
import logging

MODULE_LOGGER = logging.getLogger("jeeves")

MODULE_LOGGER.setLevel(logging.DEBUG)


def handle_codenames(payload: Any) -> None:
    """Handle updates from codenames repository"""
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


def handle_apps(_payload: Any) -> None:
    """Handle updates for repositories hosted on apps.thasky.one"""
    function_logger = MODULE_LOGGER.getChild("apps")
    for x in Path("/home/maint/docker-setup/apps/apps-docker/apps-auto").iterdir():
        if not x.is_dir():
            return
        function_logger.debug("Updating app %s at %s", str(x), str(x.absolute()))
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


def handle_jeeves(_payload: Any) -> None:
    """Handle updates for jeeves itself"""
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
    """Manage hooks"""
    MODULE_LOGGER.info("Received event from %s", path)
    if path == "codenames":
        handle_codenames(payload)
    elif path.startswith("apps-"):
        handle_apps(payload)
    elif path == "jeeves":
        handle_jeeves(payload)
    else:
        MODULE_LOGGER.warning("Unknown path: %s", path)


def loop(path: str) -> None:
    """Receive events"""
    MODULE_LOGGER.info("Starting loop")

    while True:
        with open(path, "r", encoding="utf-8") as commfile:
            request = json.loads(commfile.read())
            hookname = request["hook"]
            hookcontent = request["content"]
            MODULE_LOGGER.info("Handling hook '%s'", hookname)
            handle_hook(hookname, hookcontent)


def main() -> None:
    """Main function"""
    parser = argparse.ArgumentParser(
        prog="Actor",
        description="Actor receiving commands over a fifo pipe",
    )
    parser.add_argument("--commfile", "-c", required=True)

    args = parser.parse_args()
    loop(args.commfile)


if __name__ == "__main__":
    logging.basicConfig()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    main()
