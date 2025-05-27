import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Add src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from github_handler import GitHubHandler

class TestGitHubHandler(unittest.TestCase):

    def setUp(self):
        self.test_local_dir = "test_repo_dir" 
        self.test_repo_url = "git@github.com:user/repo.git"
        self.default_branch = "custom-main"
        self.default_commit_message = "Default test commit message"

    @patch('os.makedirs')
    @patch('os.path.isdir')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_init_repo_new_repo(self, mock_subprocess_run, mock_path_exists, mock_path_isdir, mock_makedirs):
        mock_path_exists.return_value = False
        mock_path_isdir.return_value = False 
        
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout="Initialized...", stderr=""), # git init
            MagicMock(returncode=0, stdout="", stderr=""), # git remote -v
            MagicMock(returncode=0, stdout="", stderr=""), # git remote add
        ]

        handler = GitHubHandler(
            repo_url=self.test_repo_url, 
            local_dir=self.test_local_dir,
            default_branch=self.default_branch,
            default_commit_message=self.default_commit_message
        )
        
        mock_makedirs.assert_called_once_with(self.test_local_dir, exist_ok=True)
        git_dir_path = os.path.join(self.test_local_dir, ".git")
        mock_path_exists.assert_called_once_with(git_dir_path)
        # mock_path_isdir might not be called if mock_path_exists is False for the first part of AND
        # self.assertTrue(mock_path_isdir.called) # Or assert specific call if path_exists was true
        
        expected_calls_subprocess = [
            call(['git', 'init'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'remote', '-v'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'remote', 'add', 'origin', self.test_repo_url], cwd=self.test_local_dir, text=True, capture_output=True, check=False)
        ]
        mock_subprocess_run.assert_has_calls(expected_calls_subprocess)
        self.assertEqual(mock_subprocess_run.call_count, 3)

    @patch('os.makedirs')
    @patch('os.path.isdir')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_init_repo_existing_repo_correct_remote(self, mock_subprocess_run, mock_path_exists, mock_path_isdir, mock_makedirs):
        mock_path_exists.return_value = True
        mock_path_isdir.return_value = True 
        
        remote_v_output = f"origin\t{self.test_repo_url} (fetch)\norigin\t{self.test_repo_url} (push)"
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout=remote_v_output, stderr="")

        handler = GitHubHandler(
            repo_url=self.test_repo_url, 
            local_dir=self.test_local_dir,
            default_branch=self.default_branch,
            default_commit_message=self.default_commit_message
        )
        
        git_dir_path = os.path.join(self.test_local_dir, ".git")
        mock_path_exists.assert_called_once_with(git_dir_path)
        mock_path_isdir.assert_called_once_with(git_dir_path)
        mock_subprocess_run.assert_called_once_with(
            ['git', 'remote', '-v'], cwd=self.test_local_dir, text=True, capture_output=True, check=False
        )

    @patch('os.makedirs')
    @patch('os.path.isdir')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_init_repo_existing_repo_incorrect_remote(self, mock_subprocess_run, mock_path_exists, mock_path_isdir, mock_makedirs):
        mock_path_exists.return_value = True
        mock_path_isdir.return_value = True 
        
        remote_v_output = "origin\tgit@github.com:other/other.git (fetch)\norigin\tgit@github.com:other/other.git (push)"
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout=remote_v_output, stderr=""), # git remote -v
            MagicMock(returncode=0, stdout="", stderr="")  # git remote set-url
        ]

        handler = GitHubHandler(
            repo_url=self.test_repo_url, 
            local_dir=self.test_local_dir,
            default_branch=self.default_branch,
            default_commit_message=self.default_commit_message
        )
        
        expected_calls_subprocess = [
            call(['git', 'remote', '-v'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'remote', 'set-url', 'origin', self.test_repo_url], cwd=self.test_local_dir, text=True, capture_output=True, check=False)
        ]
        mock_subprocess_run.assert_has_calls(expected_calls_subprocess)
        self.assertEqual(mock_subprocess_run.call_count, 2)

    @patch('os.makedirs') 
    @patch('os.path.isdir') 
    @patch('os.path.exists') 
    @patch('subprocess.run')
    def test_add_commit_push_specific_file(self, mock_subprocess_run, mock_path_exists_init, mock_path_isdir_init, mock_makedirs_init):
        mock_path_exists_init.return_value = True 
        mock_path_isdir_init.return_value = True  
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout=f"origin\t{self.test_repo_url} (fetch)\norigin\t{self.test_repo_url} (push)", stderr=""), 
            MagicMock(returncode=0, stdout="", stderr=""),  # git add
            MagicMock(returncode=0, stdout=" M file.txt", stderr=""), # git status
            MagicMock(returncode=0, stdout="", stderr=""),  # git commit
            MagicMock(returncode=0, stdout="Pushed...", stderr=""), # git push
        ]

        handler = GitHubHandler(
            repo_url=self.test_repo_url, 
            local_dir=self.test_local_dir,
            default_branch=self.default_branch,
            default_commit_message=self.default_commit_message
        )
        article_filename = "specific_article.md"
        expected_commit_msg = f"feat: Add/update {os.path.basename(article_filename)} (via CLI)"
        
        success, message = handler.add_commit_push(article_filename=article_filename)

        self.assertTrue(success, f"add_commit_push failed, message: {message}")
        self.assertIn(f"Successfully pushed changes to branch '{self.default_branch}'", message)
        
        expected_calls_subprocess = [
            call(['git', 'remote', '-v'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'add', article_filename], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'status', '--porcelain'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'commit', '-m', expected_commit_msg], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'push', 'origin', f"HEAD:{self.default_branch}"], cwd=self.test_local_dir, text=True, capture_output=True, check=False)
        ]
        mock_subprocess_run.assert_has_calls(expected_calls_subprocess, any_order=False)
        self.assertEqual(mock_subprocess_run.call_count, 5)

    @patch('os.makedirs')
    @patch('os.path.isdir') 
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_add_commit_push_all_uses_default_message(self, mock_subprocess_run, mock_path_exists_init, mock_path_isdir_init, mock_makedirs_init):
        mock_path_exists_init.return_value = True 
        mock_path_isdir_init.return_value = True
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout=f"origin\t{self.test_repo_url} (fetch)\norigin\t{self.test_repo_url} (push)", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),  # git add .
            MagicMock(returncode=0, stdout=" M file.md", stderr=""), 
            MagicMock(returncode=0, stdout="", stderr=""),  # git commit
            MagicMock(returncode=0, stdout="Pushed...", stderr=""), 
        ]

        handler = GitHubHandler(
            repo_url=self.test_repo_url, 
            local_dir=self.test_local_dir,
            default_branch=self.default_branch,
            default_commit_message=self.default_commit_message
        )
        success, message = handler.add_commit_push() # No article_filename, no commit_message

        self.assertTrue(success, f"add_commit_push failed, message: {message}")
        self.assertIn(f"Successfully pushed changes to branch '{self.default_branch}'", message)
        
        expected_calls_subprocess = [
            call(['git', 'remote', '-v'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'add', '.'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'status', '--porcelain'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'commit', '-m', self.default_commit_message], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'push', 'origin', f"HEAD:{self.default_branch}"], cwd=self.test_local_dir, text=True, capture_output=True, check=False)
        ]
        mock_subprocess_run.assert_has_calls(expected_calls_subprocess, any_order=False)
        self.assertEqual(mock_subprocess_run.call_count, 5)

    @patch('os.makedirs')
    @patch('os.path.isdir') 
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_add_commit_push_custom_message_overrides_all(self, mock_subprocess_run, mock_path_exists_init, mock_path_isdir_init, mock_makedirs_init):
        mock_path_exists_init.return_value = True 
        mock_path_isdir_init.return_value = True
        custom_user_message = "docs: Update documentation with new CLI features"
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout=f"origin\t{self.test_repo_url} (fetch)\norigin\t{self.test_repo_url} (push)", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),  # git add
            MagicMock(returncode=0, stdout=" M file.md", stderr=""), 
            MagicMock(returncode=0, stdout="", stderr=""),  # git commit
            MagicMock(returncode=0, stdout="Pushed...", stderr=""), 
        ]

        handler = GitHubHandler(
            repo_url=self.test_repo_url, 
            local_dir=self.test_local_dir,
            default_branch=self.default_branch,
            default_commit_message="This should be overridden by custom_user_message" 
        )
        success, message = handler.add_commit_push(article_filename="some_article.md", commit_message=custom_user_message) 

        self.assertTrue(success, f"add_commit_push failed, message: {message}")
        
        expected_calls_subprocess = [
            call(['git', 'remote', '-v'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'add', "some_article.md"], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'status', '--porcelain'], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'commit', '-m', custom_user_message], cwd=self.test_local_dir, text=True, capture_output=True, check=False),
            call(['git', 'push', 'origin', f"HEAD:{self.default_branch}"], cwd=self.test_local_dir, text=True, capture_output=True, check=False)
        ]
        mock_subprocess_run.assert_has_calls(expected_calls_subprocess, any_order=False)
        self.assertEqual(mock_subprocess_run.call_count, 5)

    @patch('os.makedirs')
    @patch('os.path.isdir')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_add_commit_push_no_changes(self, mock_subprocess_run, mock_path_exists_init, mock_path_isdir_init, mock_makedirs_init):
        mock_path_exists_init.return_value = True
        mock_path_isdir_init.return_value = True
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout=f"origin\t{self.test_repo_url} (fetch)\norigin\t{self.test_repo_url} (push)", stderr=""), 
            MagicMock(returncode=0, stdout="", stderr=""),  # git add .
            MagicMock(returncode=0, stdout="", stderr=""),  # git status --porcelain (no changes)
        ]
        handler = GitHubHandler(
            repo_url=self.test_repo_url, 
            local_dir=self.test_local_dir,
            default_branch=self.default_branch,
            default_commit_message=self.default_commit_message
        )
        success, message = handler.add_commit_push()
        self.assertTrue(success, f"add_commit_push failed, message: {message}")
        self.assertIn("No changes staged for commit", message)
        self.assertEqual(mock_subprocess_run.call_count, 3)


if __name__ == '__main__':
    unittest.main()
