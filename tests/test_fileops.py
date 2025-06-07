import sys
from pathlib import Path

from acbox import fileops


def test_which():
    exe = "cmd" if sys.platform == "win32" else "sh"

    path = fileops.which(exe)
    assert path
    assert isinstance(path, Path)

    paths = fileops.which_n(exe)
    assert isinstance(paths, list)
    assert paths[0] == fileops.which(exe)

    assert fileops.which_n("xwdwxEW") is None
