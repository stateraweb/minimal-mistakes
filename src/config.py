import os
from dotenv import load_dotenv

# Path to the root of the termux_article_cli package/app
# Assuming config.py is in termux_article_cli/src/
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Load .env from the APP_ROOT (e.g., termux_article_cli/.env)
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path=dotenv_path)

def _get_and_ensure_dir(env_var: str, default_relative_path: str) -> str:
    """
    Gets a directory path from an environment variable or uses a default.
    The path (from env or default) is treated as relative to APP_ROOT if not absolute.
    Ensures the directory exists.
    """
    path_from_env = os.getenv(env_var)
    
    if path_from_env: # If variable is set
        path_to_check = path_from_env
    else: # Variable not set, use default
        path_to_check = default_relative_path

    # Resolve path: if not absolute, assume it's relative to APP_ROOT
    if not os.path.isabs(path_to_check):
        resolved_path = os.path.join(APP_ROOT, path_to_check)
    else:
        resolved_path = path_to_check
    
    # Ensure the directory exists
    os.makedirs(resolved_path, exist_ok=True)
    return resolved_path

def get_drafts_dir() -> str:
    """Gets the path to the drafts directory, ensuring it exists."""
    return _get_and_ensure_dir("DRAFTS_DIR", "data/drafts")

def get_final_articles_dir() -> str:
    """Gets the path to the final articles directory, ensuring it exists."""
    return _get_and_ensure_dir("FINAL_ARTICLES_DIR", "data/final_articles")

def get_failed_validation_dir() -> str:
    """Gets the path to the failed validation directory, ensuring it exists."""
    return _get_and_ensure_dir("FAILED_VALIDATION_DIR", "data/failed_validation")

def get_chat_history_file_path() -> str: # Renamed from get_chat_history_file
    """
    Gets the path to the chat history JSON file.
    The path (from env or default) is treated as relative to APP_ROOT if not absolute.
    Ensures the directory for the file exists.
    """
    path_from_env = os.getenv("CHAT_HISTORY_FILE")
    default_relative_path = "data/chat_history.json" # Default relative to APP_ROOT

    if path_from_env:
        path_to_check = path_from_env
    else:
        path_to_check = default_relative_path
        
    if not os.path.isabs(path_to_check):
        resolved_path = os.path.join(APP_ROOT, path_to_check)
    else:
        resolved_path = path_to_check
        
    # Ensure the directory for the file exists
    os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
    return resolved_path

# --- Keeping other existing API key and URL getters ---

def get_gemini_api_key():
    return os.getenv("GEMINI_API_KEY")

def get_github_repo_url():
    return os.getenv("GITHUB_REPO_URL")

def get_git_default_branch() -> str:
    return os.getenv("GIT_DEFAULT_BRANCH", "main")

def get_git_default_commit_message() -> str:
    return os.getenv("GIT_DEFAULT_COMMIT_MESSAGE", "feat: Add/update articles via CLI")

# --- Removing or commenting out old get_articles_dir ---
# def get_articles_dir():
#     # Path relative to the project root, pointing inside termux_article_cli
#     default_path = os.path.join("termux_article_cli", "data", "articles") # This was old logic
#     # The new logic uses APP_ROOT and _get_and_ensure_dir for DRAFTS_DIR etc.
#     return os.getenv("ARTICLES_DIR", default_path)
