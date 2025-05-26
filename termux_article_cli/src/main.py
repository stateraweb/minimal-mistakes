import argparse
import os
import datetime # Moved to top level

# Using relative imports as src is intended to be a package
from .config import (
    get_drafts_dir, get_final_articles_dir, get_failed_validation_dir,
    get_gemini_api_key, get_chat_history_file_path, get_github_repo_url,
    get_git_default_branch, get_git_default_commit_message # Added
)
from .article_generator import ArticleGenerator
from .article_utils import save_article, load_article, list_articles, validate_frontmatter
from .github_handler import GitHubHandler


def handle_generate(args):
    """Handles the 'generate' command to create a new article."""
    print(f"Attempting to generate article with prompt: '{args.prompt}'...")

    gemini_key = get_gemini_api_key()
    chat_history_path = get_chat_history_file_path()

    if not gemini_key:
        print("ERROR: Gemini API key (GEMINI_API_KEY) is not configured in your .env file.")
        return
    if not chat_history_path: # Should be handled by config itself if default is used
        print("ERROR: Chat history file path (CHAT_HISTORY_FILE) is not configured.")
        return

    try:
        article_generator = ArticleGenerator(
            chat_history_file=chat_history_path,
            gemini_api_key=gemini_key
        )
        
        raw_ai_output = article_generator.generate_article(args.prompt)
        
        if "Error:" in raw_ai_output[:20]: # Basic check if generation itself failed
            print(f"\nERROR during article generation: {raw_ai_output}")
            # Optionally save this error output to failed_dir as well
            failed_dir = get_failed_validation_dir()
            error_filename = f"generation_error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            saved_error_path = save_article(f"Prompt: {args.prompt}\n\nError: {raw_ai_output}", failed_dir, error_filename)
            print(f"Generation error details saved to: {saved_error_path}")
            return

        is_valid, frontmatter_data, error_message = validate_frontmatter(raw_ai_output)

        if is_valid:
            drafts_dir = get_drafts_dir()
            saved_path = save_article(raw_ai_output, drafts_dir) # Auto-generates filename
            print(f"\nSUCCESS: Article draft generated, validated, and saved to: {saved_path}")
            if frontmatter_data: # Should be true if is_valid
                 print(f"  Title: {frontmatter_data.get('title', 'N/A')}")
                 print(f"  Date: {frontmatter_data.get('date', 'N/A')}")
        else:
            failed_dir = get_failed_validation_dir()
            # Save with a filename that indicates it's a validation failure, perhaps including original prompt hint
            # For now, just use the standard timestamped name.
            saved_path = save_article(raw_ai_output, failed_dir) # Auto-generates filename
            print(f"\nERROR: Article generation failed frontmatter validation: {error_message}")
            print(f"Raw output saved to: {saved_path}")

    except Exception as e:
        print(f"\nUNEXPECTED ERROR during article generation or validation: {e}")
        # Consider saving raw_ai_output to failed_dir here too if available


def handle_review(args):
    """Handles the 'review' command to list or view articles based on status."""
    status_map = {
        "draft": get_drafts_dir,
        "final": get_final_articles_dir,
        "failed": get_failed_validation_dir,
    }
    
    if args.status not in status_map:
        print(f"ERROR: Invalid status '{args.status}'. Choose from {', '.join(status_map.keys())}.")
        return
        
    articles_dir_func = status_map[args.status]
    articles_directory = articles_dir_func() # Call the appropriate getter

    print(f"Reviewing articles with status '{args.status}' in directory: '{articles_directory}'")

    if not os.path.exists(articles_directory): # Check if directory exists (config should create it)
        print(f"INFO: Directory '{articles_directory}' for status '{args.status}' not found or is empty. No articles to review.")
        return

    if args.article_name:
        if ".." in args.article_name or os.path.sep in args.article_name or (os.path.altsep and os.path.altsep in args.article_name):
            print(f"ERROR: Invalid article name '{args.article_name}'. Please provide a plain filename.")
            return

        print(f"Attempting to review article: {args.article_name}...")
        article_path = os.path.join(articles_directory, args.article_name)
        
        try:
            article_content = load_article(article_path)
            if article_content is not None:
                print(f"\n--- Article: {args.article_name} ({args.status}) ---")
                print(article_content)
                print(f"--- End of Article: {args.article_name} ---")
            else:
                print(f"INFO: Article '{args.article_name}' not found in '{articles_directory}'.")
                articles = list_articles(articles_directory)
                if articles:
                    print("\nAvailable articles in this directory:")
                    for article_filename in articles: print(f"- {article_filename}")
                else: print(f"No articles found in '{articles_directory}'.")
        except Exception as e:
            print(f"ERROR loading article '{args.article_name}': {e}")
    else:
        print(f"Listing all articles in '{articles_directory}'...")
        try:
            articles = list_articles(articles_directory)
            if articles:
                print("\nAvailable articles:")
                for article_filename in articles: print(f"- {article_filename}")
            else: print(f"INFO: No articles found in '{articles_directory}' for status '{args.status}'.")
        except Exception as e:
            print(f"ERROR listing articles: {e}")


def handle_finalize(args): # Renamed from handle_save
    """Handles the 'finalize' command to move a draft article to the final directory."""
    drafts_dir = get_drafts_dir()
    final_dir = get_final_articles_dir()
    
    if ".." in args.draft_name or os.path.sep in args.draft_name or \
       (os.path.altsep and os.path.altsep in args.draft_name):
        print(f"ERROR: Invalid draft name '{args.draft_name}'. Must be a plain filename.")
        return

    draft_path = os.path.join(drafts_dir, args.draft_name)
    final_path = os.path.join(final_dir, args.draft_name)

    print(f"Attempting to finalize article '{args.draft_name}'...")

    if not os.path.exists(draft_path):
        print(f"ERROR: Draft article '{args.draft_name}' not found in '{drafts_dir}'.")
        return

    if os.path.exists(final_path):
        print(f"WARNING: Article '{args.draft_name}' already exists in the final directory '{final_dir}'. Overwriting.")
        # Or, you could choose to prevent overwrite:
        # print(f"ERROR: Article '{args.draft_name}' already exists in final directory. Resolve manually."); return

    try:
        # Optional: Re-validate before finalizing
        print(f"Re-validating frontmatter for '{args.draft_name}'...")
        draft_content = load_article(draft_path)
        if draft_content is None: # Should not happen if path exists, but good check
            print(f"ERROR: Could not read content of draft article '{draft_path}'.")
            return
            
        is_valid, _, error_message = validate_frontmatter(draft_content)
        if not is_valid:
            print(f"ERROR: Frontmatter validation failed for '{args.draft_name}': {error_message}")
            # Consider moving to failed_validation_dir instead, or just leaving it.
            # For now, just error out and don't move.
            # failed_dir = get_failed_validation_dir()
            # os.rename(draft_path, os.path.join(failed_dir, args.draft_name))
            # print(f"Draft '{args.draft_name}' moved to '{failed_dir}' due to validation failure.")
            return

        print(f"Validation successful. Moving '{args.draft_name}' to final articles directory...")
        os.rename(draft_path, final_path)
        print(f"SUCCESS: Article '{args.draft_name}' finalized and moved to '{final_path}'.")
    except Exception as e:
        print(f"ERROR during finalization of '{args.draft_name}': {e}")


def handle_push(args):
    """Handles the 'push' command to push articles from FINAL_ARTICLES_DIR to GitHub."""
    repo_url = get_github_repo_url()
    final_articles_directory = get_final_articles_dir()
    default_branch = get_git_default_branch()
    default_commit_msg_from_config = get_git_default_commit_message() # Renamed to avoid clash

    if not repo_url:
        print("ERROR: GitHub repository URL (GITHUB_REPO_URL) is not configured. Cannot push.")
        return
    if not final_articles_directory: 
        print("ERROR: Final articles directory path is not configured.")
        return
    if not default_branch: # Should have a default from config, but good practice
        print("ERROR: Default Git branch is not configured.")
        return
    if not default_commit_msg_from_config: # Should have a default
        print("ERROR: Default Git commit message is not configured.")
        return

    print(f"Attempting to push FINAL articles from '{final_articles_directory}' to remote '{repo_url}' on branch '{default_branch}'...")

    if not os.path.exists(final_articles_directory):
        print(f"INFO: Final articles directory '{final_articles_directory}' does not exist. Nothing to push.")
        return
        
    try:
        print(f"Initializing GitHub handler for local directory: '{final_articles_directory}', remote: '{repo_url}', branch: '{default_branch}'")
        handler = GitHubHandler(
            repo_url=repo_url, 
            local_dir=final_articles_directory,
            default_branch=default_branch,
            default_commit_message=default_commit_msg_from_config # Pass the one from config
        )

        # Use args.message if provided by user, otherwise GitHubHandler will use its default.
        user_commit_message = args.message if hasattr(args, 'message') and args.message else None

        if args.article_name:
            if ".." in args.article_name or os.path.sep in args.article_name or \
               (os.path.altsep and os.path.altsep in args.article_name):
                print(f"ERROR: Invalid article name format '{args.article_name}'. Provide a plain filename.")
                return
            
            article_path_to_check = os.path.join(final_articles_directory, args.article_name)
            if not os.path.exists(article_path_to_check):
                print(f"ERROR: Article '{args.article_name}' not found in '{final_articles_directory}'. Cannot push specific file.")
                return
            
            print(f"Attempting to push specific article: {args.article_name} from final articles...")
            # If user_commit_message is None, GitHubHandler will construct one or use its default.
            # If user_commit_message is provided, it will be used.
            success, message = handler.add_commit_push(
                article_filename=args.article_name, 
                commit_message=user_commit_message 
            )
        else:
            print("Attempting to push all new/modified articles in the final articles directory...")
            # If user_commit_message is None, GitHubHandler uses its default_commit_message.
            success, message = handler.add_commit_push(
                commit_message=user_commit_message
            )

        print(f"\nPush operation summary:")
        print(f"Success: {success}")
        print(f"Message: {message}")
    except Exception as e:
        print(f"ERROR during GitHub push operation: {e}")


def main_cli():
    parser = argparse.ArgumentParser(
        description="CLI Tool for Article Automation. Uses AI to generate articles, validates them, and manages them via Git.",
        epilog="Ensure your .env file is configured with API keys, paths (DRAFTS_DIR, etc.), and GitHub SSH URL."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True, metavar="COMMAND")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", 
        help="Generate a new article, validate frontmatter, and save to drafts or failed.",
        description="Takes a prompt, uses Gemini AI to generate a Markdown article with frontmatter, validates it, and saves to the appropriate directory."
    )
    generate_parser.add_argument("--prompt", type=str, required=True, help="Prompt for article generation")
    generate_parser.set_defaults(func=handle_generate)

    # Review command
    review_parser = subparsers.add_parser(
        "review", 
        help="Review articles from drafts, final, or failed directories.",
        description="Lists articles or displays content of a specific article from one of the status directories."
    )
    review_parser.add_argument(
        "--status", 
        type=str, 
        choices=['draft', 'final', 'failed'], 
        default='draft', 
        help="Status of articles to review (default: draft)."
    )
    review_parser.add_argument("--article_name", type=str, metavar="FILENAME", help="Filename of the article to review.")
    review_parser.set_defaults(func=handle_review)

    # Finalize command (replaces save)
    finalize_parser = subparsers.add_parser(
        "finalize", 
        help="Finalize a draft article by moving it to the final articles directory after validation.",
        description="Moves a validated draft article to the final articles directory. Re-validates before moving."
    )
    finalize_parser.add_argument("--draft_name", type=str, metavar="FILENAME", required=True, help="Filename of the draft article to finalize.")
    finalize_parser.set_defaults(func=handle_finalize)

    # Push command
    push_parser = subparsers.add_parser(
        "push", 
        help="Push articles from the final articles directory to GitHub.",
        description="Commits and pushes articles from the final articles directory to the configured GitHub repository."
    )
    push_parser.add_argument("--article_name", type=str, metavar="FILENAME", help="Specific article filename to push (optional; if omitted, pushes all changes in final dir).")
    push_parser.add_argument("--message", "-m", type=str, help="Custom commit message (optional). Overrides default and auto-generated messages.")
    push_parser.set_defaults(func=handle_push)

    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    # This structure assumes main.py might be in a subdirectory (like src) 
    # and config.py, etc., are in the same directory or a way that Python can find them.
    # If running as `python -m termux_article_cli.src.main`, relative imports work.
    # If running as `python src/main.py` from project root, Python adds `src` to `sys.path` sometimes,
    # but explicit sys.path manipulation or running as a module is more robust.
    # The test files use sys.path.insert for their imports.
    # For direct execution of main.py from the src directory, the relative imports `from .config` should work.
    try:
        # datetime is now imported at the top level
        main_cli()
    except Exception as e:
        print(f"\nAn UNEXPECTED TOP-LEVEL error occurred: {e}")
        import traceback
        traceback.print_exc()
