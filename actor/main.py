import argparse
import json
from typing import Any


def handle_hook(path: str, payload: Any):
    print(path, "\n", payload)


def loop(path: str):
    while True:
        with open(path, "r", encoding="utf-8") as commfile:
            request = json.loads(commfile.read())
            handle_hook(request["hook"], request["content"])


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
