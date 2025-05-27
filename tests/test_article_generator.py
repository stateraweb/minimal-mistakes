import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json 
import sys
import tempfile # For managing temp files for chat history
import datetime # Added for checking date in prompt

# Add src directory to sys.path to allow direct import of modules from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from article_generator import ArticleGenerator

class TestArticleGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_chat_file_obj = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json")
        self.temp_chat_file_path = self.temp_chat_file_obj.name
        self.temp_chat_file_obj.close()

    def tearDown(self):
        if os.path.exists(self.temp_chat_file_path):
            os.remove(self.temp_chat_file_path)

    @patch('article_generator.genai') 
    def test_init_with_api_key_success(self, mock_genai_module):
        """Test __init__ when Gemini API key is provided and configuration succeeds."""
        mock_model_instance = MagicMock()
        mock_genai_module.GenerativeModel.return_value = mock_model_instance

        generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key="test_key")
        
        mock_genai_module.configure.assert_called_once_with(api_key="test_key")
        mock_genai_module.GenerativeModel.assert_called_once_with('gemini-1.5-flash-latest')
        self.assertEqual(generator.model, mock_model_instance)
        self.assertEqual(generator.gemini_api_key, "test_key")

    @patch('article_generator.genai')
    def test_init_configure_api_failure(self, mock_genai_module):
        """Test __init__ when genai.configure raises an exception."""
        mock_genai_module.configure.side_effect = Exception("Config Error")
        with patch('builtins.print') as mock_print:
            generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key="test_key_fail_config")
        
        mock_genai_module.configure.assert_called_once_with(api_key="test_key_fail_config")
        mock_genai_module.GenerativeModel.assert_not_called()
        self.assertIsNone(generator.model)
        mock_print.assert_any_call("Error configuring Gemini API or initializing model: Config Error")

    def test_init_no_api_key(self):
        """Test __init__ when no Gemini API key is provided."""
        with patch('builtins.print') as mock_print:
            generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key=None)
        
        self.assertIsNone(generator.model)
        self.assertIsNone(generator.gemini_api_key)
        mock_print.assert_any_call("Warning: Gemini API key not provided. Article generation will be disabled.")

    @patch('article_generator.genai')
    def test_generate_article_success(self, mock_genai_module):
        """Test successful article generation."""
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Mocked Gemini Response with Frontmatter"
        mock_response.parts = [MagicMock(text=mock_response.text)]
        mock_model_instance.generate_content.return_value = mock_response
        mock_genai_module.GenerativeModel.return_value = mock_model_instance

        generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key="test_key")
        topic_prompt = "Tell me a joke"
        result = generator.generate_article(topic_prompt)

        self.assertEqual(result, "Mocked Gemini Response with Frontmatter")
        
        args, _ = mock_model_instance.generate_content.call_args
        generated_prompt_str = args[0]
        
        self.assertIn(f'topic: "{topic_prompt}"', generated_prompt_str)
        self.assertIn("YAML frontmatter block", generated_prompt_str)
        current_date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        self.assertIn(f"date: Set this to {current_date_str}", generated_prompt_str)

        self.assertEqual(len(generator.chat_history), 1)
        self.assertEqual(generator.chat_history[0], {"user": topic_prompt, "ai": "Mocked Gemini Response with Frontmatter"})
        
        with open(self.temp_chat_file_path, 'r') as f:
            saved_history = json.load(f)
        self.assertEqual(saved_history, [{"user": topic_prompt, "ai": "Mocked Gemini Response with Frontmatter"}])

    @patch('article_generator.genai')
    def test_generate_article_success_with_parts(self, mock_genai_module):
        """Test successful article generation when response.text is not available but response.parts is."""
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        type(mock_response).text = None 
        part1, part2 = MagicMock(), MagicMock()
        part1.text, part2.text = "Part 1. ", "Part 2."
        mock_response.parts = [part1, part2]
        mock_model_instance.generate_content.return_value = mock_response
        mock_genai_module.GenerativeModel.return_value = mock_model_instance

        generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key="test_key_parts")
        topic_prompt = "Summarize this"
        result = generator.generate_article(topic_prompt)

        self.assertEqual(result, "Part 1. Part 2.")
        args, _ = mock_model_instance.generate_content.call_args
        generated_prompt_str = args[0]
        self.assertIn(f'topic: "{topic_prompt}"', generated_prompt_str)
        current_date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        self.assertIn(f"date: Set this to {current_date_str}", generated_prompt_str)
        self.assertEqual(generator.chat_history[-1], {"user": topic_prompt, "ai": "Part 1. Part 2."})

    @patch('article_generator.genai')
    def test_generate_article_api_error(self, mock_genai_module):
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = Exception("Simulated API Error")
        mock_genai_module.GenerativeModel.return_value = mock_model_instance
        generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key="test_key_api_error")
        prompt = "Another prompt"
        result = generator.generate_article(prompt)
        self.assertTrue("Error generating article using Gemini API: Simulated API Error" in result)
        self.assertEqual(generator.chat_history[-1]['user'], prompt)
        self.assertEqual(generator.chat_history[-1]['ai'], result)

    def test_generate_article_model_not_initialized(self):
        generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key=None)
        prompt = "A prompt that won't be sent"
        result = generator.generate_article(prompt)
        expected_error_msg = "Error: Gemini API key not configured or model not initialized."
        self.assertEqual(result, expected_error_msg)
        self.assertEqual(len(generator.chat_history), 1)
        self.assertEqual(generator.chat_history[0], {"user": prompt, "ai": expected_error_msg})

    def test_load_chat_history_non_existent(self):
        if os.path.exists(self.temp_chat_file_path): os.remove(self.temp_chat_file_path)
        generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key=None)
        self.assertEqual(generator.chat_history, [])

    def test_load_chat_history_empty_file(self):
        with open(self.temp_chat_file_path, 'w') as f: pass
        generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key=None)
        self.assertEqual(generator.chat_history, [])

    def test_load_chat_history_invalid_json(self):
        with open(self.temp_chat_file_path, 'w') as f: f.write("this is not json {")
        generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key=None)
        self.assertEqual(generator.chat_history, [])

    def test_save_and_load_chat_history(self):
        generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key=None) 
        sample_history = [{"user": "p1", "ai": "r1"}, {"user": "p2", "ai": "r2"}]
        generator.chat_history = sample_history
        generator.save_chat_history()
        new_generator = ArticleGenerator(chat_history_file=self.temp_chat_file_path, gemini_api_key=None)
        self.assertEqual(new_generator.chat_history, sample_history)

if __name__ == '__main__':
    unittest.main()
