from acbox.services.git import Git


def test_new(tmp_path):
    git = Git.new(tmp_path / "wow")
    assert git.gitdir == (git.worktree / ".git")
    assert not git.worktree.exists()
    assert not git.worktree.exists()


def test_clone(tmp_path):
    git = Git.clone("https://github.com/cav71/acbox.git", tmp_path / "wow1")

    assert git.worktree.exists() and git.worktree.is_dir()
    assert git.gitdir.exists() and git.gitdir.is_dir()
    assert git.gitdir.relative_to(tmp_path)
    assert git.gitdir == (git.worktree / ".git")
    assert (git.worktree / "support/builder.py").exists()
    assert git.branch() == "main"
