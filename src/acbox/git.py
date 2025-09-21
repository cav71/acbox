from __future__ import annotations

import dataclasses as dc
from pathlib import Path

from .runner import Paths, Runner


@dc.dataclass
class Git:
    workdir: Path
    runc: Runner

    @classmethod
    def new(cls, workdir: Path, verbose: bool) -> Git:
        workdir = workdir.expanduser().absolute()
        return cls(workdir, runc=Runner(verbose=verbose, exe=["git", "--git-dir", f"{workdir}/.git"]))

    # @classmethod
    # def clone(cls, url: str, workdir: Path, args: Paths | None = None, verbose: bool = False) -> Git:
    #     runc = Runner(verbose=True)
    #     runc(["git", "clone", *(args or []), url, workdir])
    #     return cls.new(workdir, verbose)

    def __call__(self, args: Paths) -> str:
        out = self.runc(args, capture=True) or ""
        return (out.decode("utf-8") if isinstance(out, bytes) else out).strip()

    def branch(self, name: str = "HEAD") -> str:
        return self(["rev-parse", "--abbrev-ref", name])

    def commits_on_branch(self, main: str = "origin/main"):
        changes = self(["reflog", "show", "--no-abbrev", self.branch()])
        return len([n for n in changes.split("\n") if n.strip()])
        # parent = self(["merge-base", self.branch(), main]).strip()
        # return int(self(["rev-list", "--count", f"{parent}..{self.branch()}"]))
