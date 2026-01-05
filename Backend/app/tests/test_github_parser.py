import os
import sys
import pytest

# Ensure the repository's Backend folder is on sys.path so `app` is importable in tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.github import parser


def test_basic_repo_url():
    got = parser.extract_github_info("https://github.com/owner/repo")
    assert got == {
        "owner": "owner",
        "repo": "repo",
        "branch": None,
        "path": None,
        "host": "github.com",
    }


def test_repo_git_suffix():
    got = parser.extract_github_info("https://github.com/owner/repo.git")
    assert got["repo"] == "repo"


def test_tree_with_branch_and_path():
    got = parser.extract_github_info("https://github.com/owner/repo/tree/main/path/to/dir")
    assert got["owner"] == "owner"
    assert got["repo"] == "repo"
    assert got["branch"] == "main"
    assert got["path"] == "path/to/dir"


def test_blob_file():
    got = parser.extract_github_info("https://github.com/owner/repo/blob/main/file.py")
    assert got["branch"] == "main"
    assert got["path"] == "file.py"


def test_ssh_url():
    got = parser.extract_github_info("git@github.com:owner/repo.git")
    assert got["owner"] == "owner"
    assert got["repo"] == "repo"


def test_raw_githubusercontent():
    got = parser.extract_github_info("https://raw.githubusercontent.com/owner/repo/main/path/to/file.txt")
    assert got["owner"] == "owner"
    assert got["repo"] == "repo"
    assert got["branch"] == "main"
    assert got["path"] == "path/to/file.txt"


def test_invalid_url_returns_none():
    assert parser.extract_github_info("not a url") is None
