# /// script
# dependencies = [
# "rich",
# "click",
# "acbox",
# ]
# ///

import click
import rich

import acbox


def main():
    print("CLICK", click)
    print("RICH", rich)
    print("ACBOX", acbox)


if __name__ == "__main__":
    main()
