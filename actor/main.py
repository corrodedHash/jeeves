import subprocess
import logging
from pathlib import Path
import argparse

MODULE_LOGGER = logging.getLogger("jeeves")


def handle_file_creation(filename: Path, script_dir: Path):
    MODULE_LOGGER.info("Received event [%s]", filename.stem)
    n = filename.stem

    chosen_scriptname = None
    if n.startswith("codenames-"):
        chosen_scriptname = "codenames"
    elif n.startswith("apps-"):
        chosen_scriptname = "apps"
    elif n.startswith("jeeves-"):
        chosen_scriptname = "jeeves"
    else:
        MODULE_LOGGER.warning("Unknown handle: %s", n)
        raise RuntimeError("Unknown handle")

    subprocess.run([script_dir / chosen_scriptname, filename], check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Run scripts when payloads are received"
    )

    parser.add_argument(
        "--watchdir", type=str, required=True, help="Path to the file to watch."
    )

    # Parse the arguments
    args = parser.parse_args()

    directory_to_watch = Path(args.watchdir)
    script_dir = Path("scripts/")
    while True:
        subprocess.run(
            [
                "inotifywait",
                "-e",
                "create",
                directory_to_watch,
            ],
            check=True,
        )

        for f in directory_to_watch.iterdir():
            if not f.is_file():
                continue
            try:
                handle_file_creation(f, script_dir)
            except:
                pass
            finally:
                f.unlink()


if __name__ == "__main__":
    main()
