from __future__ import annotations

import copy
import os
import subprocess
from pathlib import Path


# acbox/src/acbox/misc.py
def runc(cmd: list[str | Path], overrdides: dict[str, str] | None = None, **kwargs) -> tuple[str, str]:
    env = copy.deepcopy(kwargs.pop("env")) if "env" in kwargs else copy.deepcopy(os.environ)
    env.update(overrdides or {})

    args = [str(c) for c in cmd]
    p = subprocess.Popen(args, env=env, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    out, err = p.communicate()
    return out, err
