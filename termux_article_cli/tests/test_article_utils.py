import unittest
import os
import sys
import tempfile
import shutil
import datetime

import yaml # For TestValidateFrontmatter

# Add src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from article_utils import save_article, load_article, list_articles, validate_frontmatter

class TestArticleUtils(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test articles
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the temporary directory after tests
        shutil.rmtree(self.test_dir)

    def test_save_article_with_filename(self):
        content = "This is a test article."
        filename = "test_article.md"
        saved_path = save_article(content, self.test_dir, filename)
        
        self.assertEqual(saved_path, os.path.join(self.test_dir, filename))
        self.assertTrue(os.path.exists(saved_path))
        
        with open(saved_path, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_save_article_auto_filename(self):
        content = "Another test article for auto filename."
        saved_path = save_article(content, self.test_dir) # No filename provided
        
        self.assertTrue(os.path.exists(saved_path))
        # Check if filename starts with "article_" and ends with ".md"
        filename = os.path.basename(saved_path)
        self.assertTrue(filename.startswith("article_"))
        self.assertTrue(filename.endswith(".md"))
        
        # Check if timestamp is roughly correct (very basic check)
        # Example: article_20231027_123456.md
        timestamp_str = filename.replace("article_", "").replace(".md", "")
        try:
            datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            is_timestamp_valid = True
        except ValueError:
            is_timestamp_valid = False
        self.assertTrue(is_timestamp_valid, f"Filename timestamp '{timestamp_str}' is not in expected format.")

        with open(saved_path, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_load_article_success(self):
        content = "Content to be loaded."
        filename = "load_me.md"
        file_path = os.path.join(self.test_dir, filename)
        
        with open(file_path, 'w') as f:
            f.write(content)
            
        loaded_content = load_article(file_path)
        self.assertEqual(loaded_content, content)

    def test_load_article_not_found(self):
        non_existent_path = os.path.join(self.test_dir, "non_existent_article.md")
        loaded_content = load_article(non_existent_path)
        self.assertIsNone(loaded_content)

    def test_list_articles(self):
        # Create some mock .md files and a non-md file
        article_files = ["article1.md", "article2.md", "another.md"]
        for fname in article_files:
            with open(os.path.join(self.test_dir, fname), 'w') as f:
                f.write("dummy content")
        
        with open(os.path.join(self.test_dir, "notes.txt"), 'w') as f:
            f.write("not an article")
            
        # Create a subdirectory, should not be listed by list_articles
        os.makedirs(os.path.join(self.test_dir, "subdir"), exist_ok=True)
        with open(os.path.join(self.test_dir, "subdir", "article_in_subdir.md"), 'w') as f:
            f.write("dummy content")

        listed = list_articles(self.test_dir)
        
        self.assertEqual(len(listed), len(article_files))
        for fname in article_files:
            self.assertIn(fname, listed)
        self.assertNotIn("notes.txt", listed)
        self.assertNotIn("article_in_subdir.md", listed) # Should not list from subdirs

    def test_list_articles_empty_dir(self):
        empty_dir = os.path.join(self.test_dir, "empty_subdir")
        os.makedirs(empty_dir, exist_ok=True)
        listed = list_articles(empty_dir)
        self.assertEqual(len(listed), 0)

    def test_list_articles_non_existent_dir(self):
        non_existent_dir = os.path.join(self.test_dir, "does_not_exist")
        listed = list_articles(non_existent_dir)
        self.assertEqual(len(listed), 0)


class TestValidateFrontmatter(unittest.TestCase):
    def test_valid_frontmatter(self):
        valid_text = """---
title: "My Awesome Title"
description: "A great description."
excerpt: "A short excerpt."
categories: ["Tech", "Tutorials"]
tags: ["python", "cli", "automation"]
date: "2023-10-27"
image: "path/to/my/image.jpg"
---
# Main Content Header
This is the actual article content.
"""
        is_valid, data, error = validate_frontmatter(valid_text)
        self.assertTrue(is_valid, f"Validation failed unexpectedly: {error}")
        self.assertIsNotNone(data)
        self.assertIsNone(error)
        self.assertEqual(data.get("title"), "My Awesome Title")
        self.assertEqual(data.get("date"), "2023-10-27") # Stored as string
        self.assertEqual(data.get("categories"), ["Tech", "Tutorials"])
        self.assertEqual(data.get("image"), "path/to/my/image.jpg")

    def test_valid_frontmatter_no_image(self):
        valid_text_no_image = """---
title: "Title Without Image"
description: "Desc."
excerpt: "Exc."
categories: ["Demo"]
tags: ["test"]
date: "2024-01-01"
---
Content here.
"""
        is_valid, data, error = validate_frontmatter(valid_text_no_image)
        self.assertTrue(is_valid, f"Validation failed unexpectedly: {error}")
        self.assertIsNotNone(data)
        self.assertNotIn("image", data) # Image should not be present in data if not in YAML

    def test_valid_frontmatter_empty_image(self):
        valid_text_empty_image = """---
title: "Title With Empty Image"
description: "Desc."
excerpt: "Exc."
categories: ["Demo"]
tags: ["test"]
date: "2024-01-01"
image: ""
---
Content here.
"""
        is_valid, data, error = validate_frontmatter(valid_text_empty_image)
        self.assertTrue(is_valid, f"Validation failed unexpectedly: {error}")
        self.assertIsNotNone(data)
        self.assertEqual(data.get("image"), "")


    def test_missing_required_field_title(self):
        invalid_text = """---
description: "A great description."
excerpt: "A short excerpt."
categories: ["Tech"]
tags: ["python"]
date: "2023-10-27"
---
Content
"""
        is_valid, data, error = validate_frontmatter(invalid_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertIn("Missing required field: 'title'", error)

    def test_missing_required_field_date(self):
        invalid_text = """---
title: "My Title"
description: "A great description."
excerpt: "A short excerpt."
categories: ["Tech"]
tags: ["python"]
---
Content
"""
        is_valid, data, error = validate_frontmatter(invalid_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertIn("Missing required field: 'date'", error)

    def test_incorrect_data_type_categories(self):
        invalid_text = """---
title: "My Title"
description: "Desc."
excerpt: "Exc."
categories: "NotAList" 
tags: ["python"]
date: "2023-10-27"
---
Content
"""
        is_valid, data, error = validate_frontmatter(invalid_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertIn("Field 'categories' has incorrect type. Expected list, got str", error)

    def test_incorrect_data_type_tags_not_list_of_strings(self):
        invalid_text = """---
title: "My Title"
description: "Desc."
excerpt: "Exc."
categories: ["Tech"]
tags: ["python", 123] # 123 is not a string
date: "2023-10-27"
---
Content
"""
        is_valid, data, error = validate_frontmatter(invalid_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertIn("Not all items in 'tags' are non-empty strings", error)

    def test_invalid_date_format(self):
        invalid_text = """---
title: "My Title"
description: "Desc."
excerpt: "Exc."
categories: ["Tech"]
tags: ["python"]
date: "27-10-2023" # Wrong format
---
Content
"""
        is_valid, data, error = validate_frontmatter(invalid_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertIn("Field 'date' ('27-10-2023') is not in YYYY-MM-DD format", error)

    def test_malformed_yaml(self):
        # Example: Colon missing after a key
        malformed_text = """---
title "My Malformed Title" 
description: "Desc."
excerpt: "Exc."
categories: ["Tech"]
tags: ["python"]
date: "2023-10-27"
---
Content
"""
        is_valid, data, error = validate_frontmatter(malformed_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertIn("YAML parsing error", error) # Error message from PyYAML

    def test_empty_frontmatter_block(self):
        empty_block_text = """---
---
Content here.
"""
        is_valid, data, error = validate_frontmatter(empty_block_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertEqual(error, "Frontmatter block is empty.")

    def test_no_frontmatter_delimiters(self):
        no_delimiters_text = """
title: "My Title"
description: "Desc."
date: "2023-10-27"
Content here.
"""
        is_valid, data, error = validate_frontmatter(no_delimiters_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertEqual(error, "Frontmatter delimiters '---' not found or incomplete. Expected structure: ---YAML---MarkdownContent")

    def test_incomplete_frontmatter_delimiters(self):
        incomplete_delimiters_text = """---
title: "My Title"
description: "Desc."
date: "2023-10-27"
Content here.
""" # Missing closing ---
        is_valid, data, error = validate_frontmatter(incomplete_delimiters_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertEqual(error, "Frontmatter delimiters '---' not found or incomplete. Expected structure: ---YAML---MarkdownContent")

    def test_non_string_input(self):
        is_valid, data, error = validate_frontmatter(12345)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertEqual(error, "Invalid input: generated_text must be a string.")
        
    def test_empty_string_field_value(self):
        invalid_text = """---
title: "" # Empty title
description: "A great description."
excerpt: "A short excerpt."
categories: ["Tech", "Tutorials"]
tags: ["python", "cli", "automation"]
date: "2023-10-27"
---
Content
"""
        is_valid, data, error = validate_frontmatter(invalid_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertIn("Field 'title' cannot be empty or just whitespace.", error)

    def test_whitespace_string_field_value(self):
        invalid_text = """---
title: "  " # Whitespace title
description: "A great description."
excerpt: "A short excerpt."
categories: ["Tech", "Tutorials"]
tags: ["python", "cli", "automation"]
date: "2023-10-27"
---
Content
"""
        is_valid, data, error = validate_frontmatter(invalid_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertIn("Field 'title' cannot be empty or just whitespace.", error)
        
    def test_empty_list_item_in_tags(self):
        invalid_text = """---
title: "My Title"
description: "Desc."
excerpt: "Exc."
categories: ["Tech"]
tags: ["python", ""] # Empty string in list
date: "2023-10-27"
---
Content
"""
        is_valid, data, error = validate_frontmatter(invalid_text)
        self.assertFalse(is_valid)
        self.assertIsNone(data)
        self.assertIn("Not all items in 'tags' are non-empty strings", error)


if __name__ == '__main__':
    unittest.main()
