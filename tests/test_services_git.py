from acbox.services.git import Git


def test_init(tmp_path):
    git = Git.init(tmp_path / "wow")
    assert git.worktree.exists() and git.worktree.is_dir()
    assert git.gitdir.exists() and git.gitdir.is_dir()
    assert git.gitdir == (git.worktree / ".git")


def test_clone(tmp_path):
    git = Git.clone("https://github.com/cav71/acbox.git", tmp_path / "wow1")

    assert git.worktree.exists() and git.worktree.is_dir()
    assert git.gitdir.exists() and git.gitdir.is_dir()
    assert git.gitdir == (git.worktree / ".git")
    assert (git.worktree / "support/builder.py").exists()
    assert git.branch() == "main"
