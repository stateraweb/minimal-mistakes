import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import argparse # For creating mock args objects easily

# Add parent directory of 'src' (i.e., 'termux_article_cli') to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import main_cli

class TestMainCLIWorkflow(unittest.TestCase):

    # Common patches for most CLI command tests
    # These mocks are passed as arguments to each test method decorated with this.
    @patch('src.main.get_drafts_dir', return_value="mock/drafts")
    @patch('src.main.get_final_articles_dir', return_value="mock/final")
    @patch('src.main.get_failed_validation_dir', return_value="mock/failed")
    @patch('src.main.get_gemini_api_key', return_value="mock_gemini_key")
    @patch('src.main.get_chat_history_file_path', return_value="mock/chat_history.json")
    @patch('src.main.get_github_repo_url', return_value="mock_git_url")
    @patch('src.main.ArticleGenerator')
    @patch('src.main.validate_frontmatter')
    @patch('src.main.save_article')
    @patch('src.main.load_article')
    @patch('src.main.list_articles')
    @patch('src.main.GitHubHandler')
    @patch('os.path.exists') 
    @patch('os.rename')   
    @patch('src.main.datetime') 
    def run_cli_command(self, command_args_list, mock_datetime, mock_os_rename, mock_os_path_exists,
                        mock_GitHubHandler, mock_list_articles, mock_load_article,
                        mock_save_article, mock_validate_frontmatter, mock_ArticleGenerator,
                        *mock_config_getters): # Collects all config getter mocks
        """
        Helper to run main_cli with specified arguments and return all mocks.
        Mocks for config getters are collected in mock_config_getters.
        Specific behaviors for other mocks should be set by the calling test method.
        """
        # Ensure datetime.datetime.now() is properly mocked if used in main.py
        # src.main now imports 'import datetime' at the top.
        mock_datetime.datetime.now.return_value = MagicMock(strftime=MagicMock(return_value="YYYYMMDD_HHMMSS_mock"))

        with patch.object(sys, 'argv', ['main.py'] + command_args_list):
            main_cli()
        
        # Return all mocks so test methods can assert calls on them
        return {
            "mock_datetime": mock_datetime, "mock_os_rename": mock_os_rename, 
            "mock_os_path_exists": mock_os_path_exists, "mock_GitHubHandler": mock_GitHubHandler,
            "mock_list_articles": mock_list_articles, "mock_load_article": mock_load_article,
            "mock_save_article": mock_save_article, "mock_validate_frontmatter": mock_validate_frontmatter, 
            "mock_ArticleGenerator": mock_ArticleGenerator,
            "mock_config_getters": mock_config_getters 
        }

    def test_generate_command_valid_frontmatter(self):
        mock_article_generator_instance = MagicMock()
        mock_article_generator_instance.generate_article.return_value = "---valid_fm---content"
        
        # Configure mocks before calling run_cli_command
        # The run_cli_command method itself is decorated, so its mock arguments are passed.
        # We need to access these mocks to set their specific behaviors for this test.
        # This is done by having run_cli_command return them.
        
        # This test will call self.run_cli_command, which in turn receives all the patched mocks.
        # We need a way to configure these mocks *before* main_cli() is run by run_cli_command.
        # This means the @patch decorators should be on the test methods themselves.

        # Re-thinking: Apply decorators directly to test methods.
        # No, the current structure with run_cli_command being decorated is fine,
        # but individual tests need to configure the mocks that run_cli_command receives.
        # This means run_cli_command must be called within the scope of further, specific patches
        # or by passing configuration for the mocks.
        # The simplest is to configure the mocks that are passed to run_cli_command by its own decorators.

        # The mocks passed to this test method are NOT the same as those passed to run_cli_command.
        # This test structure is flawed. Let's simplify.
        # Each test method will be decorated with the necessary patches.
        pass # Placeholder for now, will rewrite tests below.


# Simpler structure: Decorate each test method with the mocks it needs.
class TestMainCLICommands(unittest.TestCase):

    @patch('src.main.get_gemini_api_key', return_value="mock_gemini_key")
    @patch('src.main.get_chat_history_file_path', return_value="mock/chat_history.json")
    @patch('src.main.get_drafts_dir', return_value="mock/drafts_dir")
    @patch('src.main.get_failed_validation_dir', return_value="mock/failed_dir")
    @patch('src.main.ArticleGenerator')
    @patch('src.main.validate_frontmatter')
    @patch('src.main.save_article')
    @patch('src.main.datetime') # For filename generation in main.handle_generate
    def test_generate_valid_frontmatter(self, mock_datetime, mock_save_article, mock_validate_frontmatter, 
                                       mock_ArticleGenerator, mock_failed_dir, mock_drafts_dir, 
                                       mock_chat_hist_path, mock_gemini_key):
        mock_datetime.datetime.now.return_value.strftime.return_value = "YYYYMMDD_HHMMSS_mock"
        mock_generator_instance = MagicMock()
        mock_generator_instance.generate_article.return_value = "---valid_fm---content"
        mock_ArticleGenerator.return_value = mock_generator_instance
        mock_validate_frontmatter.return_value = (True, {"title": "Valid Title", "date": "2023-01-01"}, None)

        with patch.object(sys, 'argv', ['main.py', 'generate', '--prompt', 'Test prompt']):
            main_cli()

        mock_ArticleGenerator.assert_called_once_with(chat_history_file="mock/chat_history.json", gemini_api_key="mock_gemini_key")
        mock_generator_instance.generate_article.assert_called_once_with('Test prompt')
        mock_validate_frontmatter.assert_called_once_with("---valid_fm---content")
        mock_save_article.assert_called_once_with("---valid_fm---content", "mock/drafts_dir")

    @patch('src.main.get_gemini_api_key', return_value="mock_gemini_key")
    @patch('src.main.get_chat_history_file_path', return_value="mock/chat_history.json")
    @patch('src.main.get_failed_validation_dir', return_value="mock/failed_dir")
    @patch('src.main.ArticleGenerator')
    @patch('src.main.validate_frontmatter')
    @patch('src.main.save_article')
    @patch('src.main.datetime')
    def test_generate_invalid_frontmatter(self, mock_datetime, mock_save_article, mock_validate_frontmatter, 
                                          mock_ArticleGenerator, mock_failed_dir, 
                                          mock_chat_hist_path, mock_gemini_key):
        mock_datetime.datetime.now.return_value.strftime.return_value = "YYYYMMDD_HHMMSS_mock"
        mock_generator_instance = MagicMock()
        mock_generator_instance.generate_article.return_value = "---invalid_fm---content"
        mock_ArticleGenerator.return_value = mock_generator_instance
        mock_validate_frontmatter.return_value = (False, None, "Validation Error")

        with patch.object(sys, 'argv', ['main.py', 'generate', '--prompt', 'Test prompt invalid']):
            main_cli()
        
        mock_validate_frontmatter.assert_called_once_with("---invalid_fm---content")
        mock_save_article.assert_called_once_with("---invalid_fm---content", "mock/failed_dir")

    @patch('src.main.get_gemini_api_key', return_value="mock_gemini_key")
    @patch('src.main.get_chat_history_file_path', return_value="mock/chat_history.json")
    @patch('src.main.get_failed_validation_dir', return_value="mock/failed_dir")
    @patch('src.main.ArticleGenerator')
    @patch('src.main.validate_frontmatter') # Still need to patch it, though not called
    @patch('src.main.save_article')
    @patch('src.main.datetime')
    def test_generate_api_error(self, mock_datetime, mock_save_article, mock_validate_frontmatter,
                                mock_ArticleGenerator, mock_failed_dir,
                                mock_chat_hist_path, mock_gemini_key):
        mock_datetime.datetime.now.return_value.strftime.return_value = "YYYYMMDD_HHMMSS_mock"
        mock_generator_instance = MagicMock()
        mock_generator_instance.generate_article.return_value = "Error: API limit reached" # AI error
        mock_ArticleGenerator.return_value = mock_generator_instance

        with patch.object(sys, 'argv', ['main.py', 'generate', '--prompt', 'API error prompt']):
            main_cli()

        mock_validate_frontmatter.assert_not_called()
        # Check that save_article was called to save the error details to failed_dir
        saved_content_arg = mock_save_article.call_args[0][0]
        saved_dir_arg = mock_save_article.call_args[0][1]
        self.assertIn("Error: API limit reached", saved_content_arg)
        self.assertIn("API error prompt", saved_content_arg)
        self.assertEqual(saved_dir_arg, "mock/failed_dir")


    @patch('src.main.get_drafts_dir', return_value="mock/drafts_dir")
    @patch('src.main.list_articles')
    @patch('os.path.exists', return_value=True) # Assume directory exists
    def test_review_drafts_list(self, mock_os_exists, mock_list_articles, mock_drafts_dir):
        with patch.object(sys, 'argv', ['main.py', 'review', '--status', 'draft']):
            main_cli()
        mock_list_articles.assert_called_once_with("mock/drafts_dir")

    @patch('src.main.get_final_articles_dir', return_value="mock/final_dir")
    @patch('src.main.load_article')
    @patch('os.path.exists', return_value=True)
    def test_review_final_specific(self, mock_os_exists, mock_load_article, mock_final_dir):
        with patch.object(sys, 'argv', ['main.py', 'review', '--status', 'final', '--article_name', 'final.md']):
            main_cli()
        mock_load_article.assert_called_once_with(os.path.join("mock/final_dir", 'final.md'))


    @patch('src.main.get_drafts_dir', return_value="mock/drafts_dir")
    @patch('src.main.get_final_articles_dir', return_value="mock/final_dir")
    @patch('src.main.load_article')
    @patch('src.main.validate_frontmatter')
    @patch('os.path.exists') # This mock will be configured specifically
    @patch('os.rename')
    def test_finalize_success(self, mock_os_rename, mock_os_exists, mock_validate_frontmatter, 
                              mock_load_article, mock_final_dir, mock_drafts_dir):
        
        draft_name = "to_finalize.md"
        draft_path = os.path.join("mock/drafts_dir", draft_name)
        final_path = os.path.join("mock/final_dir", draft_name)

        # Configure os.path.exists mock specifically for the paths we expect
        # and provide a default for any other calls (e.g., from gettext/argparse)
        def os_path_exists_side_effect(path):
            if path == draft_path:
                return True  # Draft exists
            if path == final_path:
                return False # Final does not exist (initially)
            return True # Default for any other path (e.g. locale files)
        mock_os_exists.side_effect = os_path_exists_side_effect
        
        mock_load_article.return_value = "draft content"
        mock_validate_frontmatter.return_value = (True, {"title": "Finalized"}, None)
        
        with patch.object(sys, 'argv', ['main.py', 'finalize', '--draft_name', draft_name]):
            main_cli()
        
        mock_os_exists.assert_any_call(draft_path)
        mock_os_exists.assert_any_call(final_path)
        mock_load_article.assert_called_once_with(draft_path)
        mock_validate_frontmatter.assert_called_once_with("draft content")
        mock_os_rename.assert_called_once_with(draft_path, final_path)

    @patch('src.main.get_github_repo_url', return_value="mock_git_url")
    @patch('src.main.get_final_articles_dir', return_value="mock/final_dir")
    @patch('src.main.get_git_default_branch', return_value="test-branch") # Added
    @patch('src.main.get_git_default_commit_message', return_value="Test default commit from config") # Added
    @patch('src.main.GitHubHandler')
    @patch('os.path.exists', return_value=True) 
    def test_push_all_final_no_message_arg(self, mock_os_exists, mock_GitHubHandler, 
                                            mock_git_def_commit_msg, mock_git_def_branch, # Added
                                            mock_final_dir, mock_git_url):
        mock_gh_instance = MagicMock()
        mock_gh_instance.add_commit_push.return_value = (True, "Pushed all with default config message")
        mock_GitHubHandler.return_value = mock_gh_instance

        with patch.object(sys, 'argv', ['main.py', 'push']): # No --message argument
            main_cli()
        
        mock_GitHubHandler.assert_called_once_with(
            repo_url="mock_git_url", 
            local_dir="mock/final_dir",
            default_branch="test-branch",
            default_commit_message="Test default commit from config"
        )
        # args.message is None, so GitHubHandler will use its default_commit_message logic
        mock_gh_instance.add_commit_push.assert_called_once_with(commit_message=None)


    @patch('src.main.get_github_repo_url', return_value="mock_git_url")
    @patch('src.main.get_final_articles_dir', return_value="mock/final_dir")
    @patch('src.main.get_git_default_branch', return_value="test-branch")
    @patch('src.main.get_git_default_commit_message', return_value="Test default commit from config")
    @patch('src.main.GitHubHandler')
    @patch('os.path.exists') 
    def test_push_specific_article_with_message_arg(self, mock_os_exists, mock_GitHubHandler,
                                                     mock_git_def_commit_msg, mock_git_def_branch, # Mocks from config
                                                     mock_final_dir_getter, mock_git_url_getter): # Mocks from config (actual getter names)
        article_name = "my_article.md"
        custom_commit_message = "docs: Update my_article.md with new sections"
        
        final_articles_dir_path = "mock/final_dir" # This is the return_value of the mocked getter
        article_full_path = os.path.join(final_articles_dir_path, article_name)

        def os_path_exists_side_effect(path):
            if path == final_articles_dir_path:
                return True # final_articles_directory exists
            if path == article_full_path:
                return True # specific article exists
            return False # Default for any other path (e.g. locale files from gettext)
        mock_os_exists.side_effect = os_path_exists_side_effect
        
        mock_gh_instance = MagicMock()
        mock_gh_instance.add_commit_push.return_value = (True, "Pushed specific with custom message")
        mock_GitHubHandler.return_value = mock_gh_instance

        with patch.object(sys, 'argv', ['main.py', 'push', '--article_name', article_name, '-m', custom_commit_message]):
            main_cli()
        
        mock_GitHubHandler.assert_called_once_with(
            repo_url="mock_git_url", 
            local_dir="mock/final_dir",
            default_branch="test-branch",
            default_commit_message="Test default commit from config"
        )
        mock_gh_instance.add_commit_push.assert_called_once_with(
            article_filename=article_name, 
            commit_message=custom_commit_message
        )


    # Argparse error tests
    def test_no_command_provided_exits(self):
        with patch.object(sys, 'argv', ['main.py']):
            with self.assertRaises(SystemExit):
                main_cli()

    def test_generate_missing_prompt_exits(self):
        with patch.object(sys, 'argv', ['main.py', 'generate']):
            with self.assertRaises(SystemExit):
                main_cli()

if __name__ == '__main__':
    unittest.main()
