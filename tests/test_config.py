import unittest
from unittest.mock import patch
import os
import sys

# Add src directory to sys.path to allow direct import of modules from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import APP_ROOT for constructing expected paths
from config import (
    get_openai_api_key, get_github_token, get_huggingface_api_key, get_gemini_api_key,
    get_drafts_dir, get_final_articles_dir, get_failed_validation_dir,
    get_chat_history_file_path, get_github_repo_url, APP_ROOT,
    get_git_default_branch, get_git_default_commit_message # Added
)

class TestConfig(unittest.TestCase):

    def common_path_test_logic(self, getter_func, env_var_name, default_relative_path, is_file_path=False):
        # --- Test with environment variable set ---
        custom_path_from_env = "my_custom_test_dir"
        if is_file_path:
            custom_path_from_env = "my_custom_test_dir/file.json"
        
        expected_resolved_custom_path = os.path.join(APP_ROOT, custom_path_from_env)
        if is_file_path:
            expected_makedirs_path = os.path.dirname(expected_resolved_custom_path)
        else:
            expected_makedirs_path = expected_resolved_custom_path

        with patch.dict(os.environ, {env_var_name: custom_path_from_env}, clear=True):
            with patch('os.makedirs') as mock_mkdirs:
                returned_path = getter_func()
                self.assertEqual(returned_path, expected_resolved_custom_path)
                mock_mkdirs.assert_called_once_with(expected_makedirs_path, exist_ok=True)

        # --- Test with environment variable set to an absolute path ---
        # On POSIX, /tmp is usually absolute. For Windows, C:\tmp or similar.
        # Using a known directory like /tmp for testing absolute paths.
        # We need to ensure this path is plausible for the test environment.
        # Let's use a path that starts with os.sep to make it absolute.
        abs_custom_path = os.path.join(os.sep, "abs_test_dir") 
        if is_file_path:
            abs_custom_path = os.path.join(os.sep, "abs_test_dir", "file.json")

        if is_file_path:
            expected_makedirs_path_abs = os.path.dirname(abs_custom_path)
        else:
            expected_makedirs_path_abs = abs_custom_path

        with patch.dict(os.environ, {env_var_name: abs_custom_path}, clear=True):
            with patch('os.makedirs') as mock_mkdirs_abs:
                # Mock os.path.isabs to correctly identify this path as absolute
                with patch('os.path.isabs', return_value=True) as mock_isabs:
                    returned_path_abs = getter_func()
                    mock_isabs.assert_called_with(abs_custom_path) # Verify isabs was checked
                    self.assertEqual(returned_path_abs, abs_custom_path)
                    mock_mkdirs_abs.assert_called_once_with(expected_makedirs_path_abs, exist_ok=True)
        
        # --- Test with default value (environment variable not set) ---
        expected_default_resolved_path = os.path.join(APP_ROOT, default_relative_path)
        if is_file_path:
            expected_default_makedirs_path = os.path.dirname(expected_default_resolved_path)
        else:
            expected_default_makedirs_path = expected_default_resolved_path

        with patch.dict(os.environ, {}, clear=True): # Ensure env var is not set
            with patch('os.makedirs') as mock_mkdirs_default:
                returned_path_default = getter_func()
                self.assertEqual(returned_path_default, expected_default_resolved_path)
                mock_mkdirs_default.assert_called_once_with(expected_default_makedirs_path, exist_ok=True)

    def test_get_drafts_dir(self):
        self.common_path_test_logic(get_drafts_dir, "DRAFTS_DIR", "data/drafts")

    def test_get_final_articles_dir(self):
        self.common_path_test_logic(get_final_articles_dir, "FINAL_ARTICLES_DIR", "data/final_articles")

    def test_get_failed_validation_dir(self):
        self.common_path_test_logic(get_failed_validation_dir, "FAILED_VALIDATION_DIR", "data/failed_validation")

    def test_get_chat_history_file_path(self):
        self.common_path_test_logic(get_chat_history_file_path, "CHAT_HISTORY_FILE", "data/chat_history.json", is_file_path=True)


    # --- Tests for API keys and GitHub URL (can remain similar) ---
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_openai_key",
        "GITHUB_TOKEN": "test_github_token",
        "HF_API_KEY": "test_hf_key",
        "GEMINI_API_KEY": "test_gemini_key",
        "GITHUB_REPO_URL": "custom_repo_url"
    })
    def test_get_api_and_url_values_from_env(self): # Renamed for clarity
        self.assertEqual(get_openai_api_key(), "test_openai_key")
        self.assertEqual(get_github_token(), "test_github_token")
        self.assertEqual(get_huggingface_api_key(), "test_hf_key")
        self.assertEqual(get_gemini_api_key(), "test_gemini_key")
        self.assertEqual(get_github_repo_url(), "custom_repo_url")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_default_api_and_url_values(self): # Renamed for clarity
        self.assertIsNone(get_openai_api_key()) 
        self.assertIsNone(get_github_token())
        self.assertIsNone(get_huggingface_api_key())
        self.assertIsNone(get_gemini_api_key())
        self.assertIsNone(get_github_repo_url())

    # Specific test for Gemini key (already good, can be kept)
    def test_get_gemini_api_key_specific(self): # Renamed for clarity
        with patch.dict(os.environ, {"GEMINI_API_KEY": "specific_gemini_key"}, clear=True):
            self.assertEqual(get_gemini_api_key(), "specific_gemini_key")
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(get_gemini_api_key())

    # Removed old test_get_empty_values_for_paths as it targeted old get_articles_dir
    # The new common_path_test_logic implicitly covers env var presence.
    # If specific tests for empty string env vars are needed for the new getters, they can be added.

    def test_get_git_default_branch(self):
        # Test with environment variable set
        with patch.dict(os.environ, {"GIT_DEFAULT_BRANCH": "feature-branch"}, clear=True):
            self.assertEqual(get_git_default_branch(), "feature-branch")
        
        # Test with environment variable not set (should return default)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_git_default_branch(), "main") # Default is "main"

    def test_get_git_default_commit_message(self):
        # Test with environment variable set
        custom_message = "chore: Automated article push"
        with patch.dict(os.environ, {"GIT_DEFAULT_COMMIT_MESSAGE": custom_message}, clear=True):
            self.assertEqual(get_git_default_commit_message(), custom_message)
        
        # Test with environment variable not set (should return default)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_git_default_commit_message(), "feat: Add/update articles via CLI") # Default


if __name__ == '__main__':
    unittest.main()
