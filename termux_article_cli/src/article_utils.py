import os
import datetime
import yaml # Added for PyYAML

# Keep existing save_article, load_article, list_articles as they are.
# Their functionality regarding which directory they use will be determined by the
# 'articles_dir' argument passed to them, which in main.py will come from
# the new config functions (e.g., get_drafts_dir()).

def save_article(article_content: str, articles_dir: str, filename: str = None) -> str:
    """
    Saves the article_content to a file in articles_dir.
    If filename is not provided, generate one using a timestamp (e.g., article_YYYYMMDD_HHMMSS.md).
    Ensures articles_dir is created if it doesn't exist.
    Returns the full path of the saved article.
    """
    os.makedirs(articles_dir, exist_ok=True)
    
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"article_{timestamp}.md"
    
    article_path = os.path.join(articles_dir, filename)
    
    with open(article_path, 'w') as f:
        f.write(article_content)
        
    return article_path

def load_article(article_path: str) -> str | None:
    """
    Loads and returns the content of the article from article_path.
    Returns None if the file is not found.
    """
    try:
        with open(article_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

def list_articles(articles_dir: str) -> list[str]:
    """
    Lists all .md files in articles_dir.
    Returns a list of filenames.
    """
    if not os.path.isdir(articles_dir):
        return []
        
    articles = []
    for item in os.listdir(articles_dir):
        if item.endswith(".md") and os.path.isfile(os.path.join(articles_dir, item)):
            articles.append(item)
    return articles

def validate_frontmatter(generated_text: str) -> tuple[bool, dict | None, str | None]:
    errors = []
    frontmatter_dict = None

    try:
        # Ensure generated_text is a string
        if not isinstance(generated_text, str):
            return False, None, "Invalid input: generated_text must be a string."

        parts = generated_text.split('---', 2)
        if len(parts) < 3: # Must have at least three parts: before, frontmatter, after
            return False, None, "Frontmatter delimiters '---' not found or incomplete. Expected structure: ---YAML---MarkdownContent"
        
        frontmatter_str = parts[1].strip()
        if not frontmatter_str: # Check if the captured frontmatter string is empty
            return False, None, "Frontmatter block is empty."

        frontmatter_dict = yaml.safe_load(frontmatter_str)
        
        # Check if parsing resulted in a dictionary
        if not isinstance(frontmatter_dict, dict):
            # If frontmatter_dict is None (e.g. due to empty but valid YAML like "---"), or not a dict
            return False, None, "Failed to parse frontmatter as a dictionary. Frontmatter might be empty or malformed."

    except yaml.YAMLError as e:
        return False, None, f"YAML parsing error: {str(e)}"
    except Exception as e: # Catch any other unexpected error during parsing section
        return False, None, f"Unexpected error during frontmatter extraction: {str(e)}"

    required_fields = {
        "title": str,
        "description": str,
        "excerpt": str,
        "categories": list,
        "tags": list,
        "date": str, # Specific format 'YYYY-MM-DD' validated below
    }

    # Check for presence and type of required fields
    for field, expected_type in required_fields.items():
        if field not in frontmatter_dict:
            errors.append(f"Missing required field: '{field}'.")
            continue # Skip further checks for this field if missing
        
        value = frontmatter_dict[field]
        if not isinstance(value, expected_type):
            errors.append(f"Field '{field}' has incorrect type. Expected {expected_type.__name__}, got {type(value).__name__}.")
            continue # Skip content checks if type is wrong

        # Content checks for specific types
        if expected_type == str and not value.strip(): # For title, description, excerpt, date (before format check)
            errors.append(f"Field '{field}' cannot be empty or just whitespace.")
        
        if field == "date": # Already confirmed value is a string (or type error was logged)
            try:
                datetime.datetime.strptime(str(value), '%Y-%m-%d')
            except ValueError:
                errors.append(f"Field 'date' ('{value}') is not in YYYY-MM-DD format.")
        
        if field in ["categories", "tags"]: # Already confirmed value is a list
            if not value: # Check if list is empty, which is allowed by prompt but could be a point of refinement
                # errors.append(f"Field '{field}' list cannot be empty.") # Uncomment if empty lists are not allowed
                pass
            elif not all(isinstance(item, str) and item.strip() for item in value):
                errors.append(f"Not all items in '{field}' are non-empty strings.")


    # Optional field: image (presence is optional, but if present, must be a string)
    if "image" in frontmatter_dict:
        if not isinstance(frontmatter_dict["image"], str):
            errors.append(f"Optional field 'image' has incorrect type. Expected str, got {type(frontmatter_dict['image']).__name__}.")
        # Allow empty string for image if present, as per "can be empty"
        # else: # image is present and is a string
        #     if not frontmatter_dict["image"].strip():
        #         errors.append(f"Optional field 'image', if present, should not be an empty string unless that's intended.")


    if errors:
        return False, None, "Validation errors: " + "; ".join(errors)
    
    # If all checks pass, return the parsed dictionary
    return True, frontmatter_dict, None
