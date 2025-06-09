import os
import sys

if __name__ == "__main__":
    print(f"HELLO={os.environ.get('HELLO', 'N/A')}")
    for i in range(10):
        if not (i % 3):
            print(f"line (err) {i}", file=sys.stderr)
        else:
            print(f"line (out) {i}", file=sys.stdout)
