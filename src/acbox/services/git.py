from __future__ import annotations

import dataclasses as dc
import subprocess
import sys
from pathlib import Path
from typing import Sequence


@dc.dataclass
class GitBranch:
    name: str
    short: str


@dc.dataclass
class Git:
    worktree: Path
    gitdir: Path | None = None
    exe: str = "git"

    def __post_init__(self):
        if not self.gitdir:
            self.gitdir = self.worktree / ".git"

    def __repr__(self):
        return f"<{self.__class__.__name__} worktree={self.worktree}>"

    def _run(self, cmd: str | Sequence[str | Path], **kwargs) -> str:
        arguments = [self.exe, "--git-dir", self.gitdir, "--work-tree", self.worktree]
        arguments.extend([cmd] if isinstance(cmd, (Path, str)) else cmd)
        return subprocess.check_output([str(c) for c in arguments], encoding="utf-8")

    @classmethod
    def init(cls, path: Path) -> Git:
        path.mkdir(parents=True, exist_ok=True)
        subprocess.check_call([cls.exe, "init", str(path)])
        return cls(path)

    @classmethod
    def clone(cls, url: str, path: Path, branch: str = "", single: bool = False) -> Git:
        arguments: Sequence[str | Path] = [cls.exe, "clone", url]
        if branch:
            arguments = [*arguments, "--branch", branch]
        if single:
            arguments = [*arguments, "--single-branch"]
        arguments = [*arguments, path]
        subprocess.check_call([str(a) for a in arguments])
        return Git(path)

    def branch(self):
        return self._run(["branch", "--show-current"]).strip()


if __name__ == "__main__":
    git = Git(Path.cwd())
    print(git._run(sys.argv[1:]))
