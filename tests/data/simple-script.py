# call this:
#   simple-script.py - writes simple messages to stdout/stderr
#   VALUE=123 simple-script.py - same as above, but writes VALUE message too
#   WAIT=2 VALUE=123 simple-script.py - same as above, but wait 2s before printing last message
#   ABORT=12 simple-script.py - same as above, but abort the script with error code 12
import os
import sys
import time
from typing import TextIO


def hello(index: int, msg: str, file: TextIO = sys.stdout) -> None:
    print(f"{index}, got '{msg}' ({file.name})", file=file)


def main() -> None:
    hello(1, "first message")
    hello(2, "second message", sys.stderr)

    index = 3
    if value := os.environ.get("VALUE"):
        hello(index, f"received [{value}]")
        hello(index + 1, f"received [{value}]", sys.stderr)
        index += 2

    if wait := os.environ.get("WAIT"):
        hello(index, f"waiting {wait}s ..")
        hello(index + 1, f"waiting {wait}s ..", sys.stderr)
        index += 2
        time.sleep(float(wait))
        hello(index, f"done waiting {wait}s")
        hello(index + 1, f"done waiting {wait}s", sys.stderr)
        index += 2

    if abort := os.environ.get("ABORT"):
        hello(index, f"aborting with {abort}")
        hello(index + 1, f"aborting with {abort}", sys.stderr)
        index += 2
        sys.exit(int(abort))


if __name__ == "__main__":
    main()
