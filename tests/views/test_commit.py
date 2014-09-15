from stat import S_IFDIR

import pytest
from mock import MagicMock, patch

from fuse import FuseOSError
from gitfs.views.commit import CommitView


class TestCommitView(object):
    def test_readdir_without_tree_name(self):
        mocked_repo = MagicMock()
        mocked_commit = MagicMock()
        mocked_entry = MagicMock()

        mocked_entry.name = "entry"
        mocked_commit.tree = [mocked_entry]
        mocked_repo.revparse_single.return_value = mocked_commit

        view = CommitView(repo=mocked_repo, commit_sha1="sha1")
        with patch('gitfs.views.commit.os') as mocked_os:
            mocked_os.path.split.return_value = [None, None]

            dirs = [entry for entry in view.readdir("/path", 0)]
            assert dirs == [".", "..", "entry"]

            mocked_os.path.split.assert_called_once_with("/path")

    def test_readdir_with_tree_name(self):
        mocked_repo = MagicMock()
        mocked_commit = MagicMock()
        mocked_entry = MagicMock()

        mocked_entry.name = "entry"
        mocked_commit.tree = "tree"
        mocked_repo.revparse_single.return_value = mocked_commit
        mocked_repo.get_git_object.return_value = [mocked_entry]

        view = CommitView(repo=mocked_repo, commit_sha1="sha1")
        with patch('gitfs.views.commit.os') as mocked_os:
            mocked_os.path.split.return_value = [None, True]

            dirs = [entry for entry in view.readdir("/path", 0)]
            assert dirs == [".", "..", "entry"]

            mocked_os.path.split.assert_called_once_with("/path")
            mocked_repo.get_git_object.assert_called_once_with("tree", "/path")

    def test_access_with_missing_relative_path(self):
        mocked_repo = MagicMock()
        mocked_commit = MagicMock()

        mocked_repo.revparse_single.return_value = mocked_commit

        view = CommitView(repo=mocked_repo, commit_sha1="sha1")

        assert view.access("path", "mode") == 0

    def test_access_with_invalid_relative_path(self):
        mocked_repo = MagicMock()
        mocked_commit = MagicMock()

        mocked_repo.revparse_single.return_value = mocked_commit

        view = CommitView(repo=mocked_repo, commit_sha1="sha1")
        view.relative_path = "/"

        assert view.access("path", "mode") == 0

    def test_access_with_invalid_path(self):
        mocked_repo = MagicMock()
        mocked_validation = MagicMock()
        mocked_commit = MagicMock()

        mocked_commit.tree = "tree"
        mocked_repo.revparse_single.return_value = mocked_commit
        mocked_validation.return_value = False

        with patch("gitfs.views.commit.split_path_into_components") as split:
            split.return_value = "elements"

            view = CommitView(repo=mocked_repo, commit_sha1="sha1")
            view._validate_commit_path = mocked_validation
            view.relative_path = "relative_path"

            with pytest.raises(FuseOSError):
                view.access("path", "mode")

            split.assert_called_once_with("relative_path")
            mocked_validation.assert_called_once_with("tree", "elements")

    def test_getattr_with_no_path(self):
        mocked_repo = MagicMock()
        mocked_commit = MagicMock()

        mocked_commit.tree = "tree"
        mocked_repo.revparse_single.return_value = mocked_commit

        view = CommitView(repo=mocked_repo, commit_sha1="sha1")
        assert view.getattr(False, 1) is None

    def test_getattr_with_simple_path(self):
        mocked_repo = MagicMock()
        mocked_commit = MagicMock()

        mocked_commit.tree = "tree"
        mocked_commit.commit_time = "now+1"
        mocked_repo.revparse_single.return_value = mocked_commit

        view = CommitView(repo=mocked_repo, commit_sha1="sha1",
                          mount_time="now", uid=1, gid=1)
        result = view.getattr("/", 1)
        asserted_result = {
            'st_uid': 1,
            'st_gid': 1,
            'st_mtime': "now+1",
            'st_ctime': "now+1",
            'st_mode': S_IFDIR | 0555,
            'st_nlink': 2
        }
        assert result == asserted_result

    def test_getattr_with_invalid_object_type(self):
        mocked_repo = MagicMock()
        mocked_commit = MagicMock()

        mocked_commit.tree = "tree"
        mocked_commit.commit_time = "now+1"
        mocked_repo.revparse_single.return_value = mocked_commit
        mocked_repo.get_git_object_type.return_value = None

        view = CommitView(repo=mocked_repo, commit_sha1="sha1",
                          mount_time="now", uid=1, gid=1)

        with pytest.raises(FuseOSError):
            view.getattr("/path", 1)

        mocked_repo.get_git_object_type.assert_called_once_with("tree",
                                                                "/path")