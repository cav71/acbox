from __future__ import annotations

from collections.abc import Iterable, MutableMapping
from typing import Any

DELETE = object()


def dictupdate(data: MutableMapping[str, Any], updates: Iterable[tuple[str, Any]]) -> list[tuple[str, Any]]:
    undo = []
    for path, value in updates:
        cur = data
        loc = path.split(".")
        for i in range(len(loc) - 1):
            if loc[i] not in cur:
                cur[loc[i]] = dict()
                undo.append((".".join(loc[: i + 1]), DELETE))
            cur = cur[loc[i]]

        orig = cur.get(loc[-1], DELETE)
        undo.append((path, orig))
        if value is DELETE:
            del cur[loc[-1]]
        else:
            cur[loc[-1]] = value

    return undo


def dictrollback(data: MutableMapping[str, Any], undo: list[tuple[str, Any]]) -> None:
    for path, value in reversed(undo):
        cur = data
        loc = path.split(".")
        for c in loc[:-1]:
            cur = cur[c]
        if value is DELETE:
            del cur[loc[-1]]
        else:
            cur[loc[-1]] = value
