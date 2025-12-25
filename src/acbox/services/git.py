from __future__ import annotations

import dataclasses as dc
from pathlib import Path

from ..runner import Paths, Runner


@dc.dataclass
class GitBranch:
    name: str
    short: str


@dc.dataclass
class Git:
    worktree: Path
    runner: Runner
    gitdir: Path | None = None
    exe: str | Path = "git"

    def __post_init__(self):
        if not self.gitdir:
            self.gitdir = self.worktree / ".git"

    def __repr__(self):
        return f"<{self.__class__.__name__} worktree={self.worktree}>"

    @classmethod
    def new(cls, worktree: Path, verbose: bool = False) -> Git:
        worktree = worktree.expanduser().absolute()
        runner = Runner(verbose=verbose, exe=["git", "--git-dir", f"{worktree}/.git"])
        return cls(worktree, runner=runner)

    @classmethod
    def clone(cls, url: str, worktree: Path | None = None, verbose: bool = False, *args) -> Git:
        git = cls.new(worktree or Path.cwd(), verbose=verbose)
        git.worktree.parent.mkdir(parents=True, exist_ok=True)
        git.runner(["clone", *(args or []), url, git.worktree])
        return git

    def __call__(self, args: Paths) -> str:
        out = self.runner(args, capture=True) or ""
        return (out.decode("utf-8") if isinstance(out, bytes) else out).strip()

    def branch(self, name: str = "HEAD") -> str:
        return self(["rev-parse", "--abbrev-ref", name])

    def commits_on_branch(self, main: str = "origin/main") -> int:
        return int(self(["rev-list", "--count", main]))
