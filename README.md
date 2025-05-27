# Termux Article CLI

## 1. Overview

Termux Article CLI is a command-line tool designed to streamline the creation of articles or blog posts. It leverages Google's Gemini AI for content generation, including structured YAML frontmatter. The tool incorporates a validation step for this frontmatter, supports a draft-review-finalize workflow, and enables synchronization of final articles with a GitHub repository via SSH.

## 2. Features

*   **AI-Powered Article Generation:** Utilizes the Google Gemini API to create full Markdown articles, including a YAML frontmatter block, from user-provided prompts.
*   **Structured Frontmatter Generation and Validation:** The AI is instructed to generate specific frontmatter fields (`title`, `description`, `excerpt`, `categories`, `tags`, `date`, optional `image`). The application then validates this generated frontmatter for presence, type, and format of required fields.
*   **Multi-Directory Workflow:**
    *   **Drafts:** Successfully generated and validated articles are saved to a drafts directory.
    *   **Failed Validation:** Articles that fail frontmatter validation are saved to a separate directory for review and manual correction.
    *   **Final Articles:** Drafts can be "finalized," moving them to a directory for articles ready to be published or pushed.
*   **Markdown Format:** Articles are generated and managed in Markdown (`.md`).
*   **Local Review:** List and view articles from any of the workflow directories (drafts, final, failed) directly in the terminal.
*   **GitHub Synchronization:** Push finalized articles (either all or specific ones) to a configured GitHub repository.
*   **Configurable Git Options:** Default Git branch and commit messages can be set via environment variables. Custom commit messages can also be provided via CLI arguments.
*   **Chat History:** Maintains a JSON file of prompts and AI responses for context (though the current Gemini integration is primarily stateless per generation request, the history is saved).
*   **Configuration via `.env`:** API keys, repository URLs, local directory paths, and Git defaults are managed through an environment file.

## 3. Prerequisites

*   **Termux Environment:** Designed for Termux on Android.
*   **Python:** Python 3.x installed (`pkg install python`).
*   **Git:** Git installed (`pkg install git`).
*   **SSH Key for GitHub:**
    *   An SSH key must be generated in Termux (`ssh-keygen`).
    *   The public key must be added to your GitHub account's SSH keys.
    *   SSH agent should be configured in Termux if using passphrases for your SSH key.

## 4. Setup & Installation

1.  **Clone or Navigate to Repository:**
    If this tool is part of a larger project, navigate to the `termux_article_cli` directory. If standalone:
    ```bash
    git clone <your_repository_url>
    cd termux_article_cli
    ```
    (Ensure you are in the `termux_article_cli` root directory for the following steps).

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment File (`.env`):**
    *   Copy the example environment file. It's crucial to do this from the `termux_article_cli` directory.
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file (now located at `termux_article_cli/.env`) with your configurations:

        ```env
        # --- API Keys ---
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE" # Mandatory for article generation

        # --- Directory Paths (relative to termux_article_cli directory) ---
        # Directory for successfully generated and validated drafts
        DRAFTS_DIR="data/drafts"
        # Directory for articles moved from drafts, ready for publishing/pushing
        FINAL_ARTICLES_DIR="data/final_articles"
        # Directory for articles that failed frontmatter validation
        FAILED_VALIDATION_DIR="data/failed_validation"
        
        # --- Files ---
        # Path for storing chat history (relative to termux_article_cli directory)
        CHAT_HISTORY_FILE="data/chat_history.json"

        # --- GitHub Configuration ---
        # SSH URL of the GitHub repository for pushing articles
        GITHUB_REPO_URL="git@github.com:your_username/your_repository.git" # Mandatory for 'push' command
        # Default Git branch to push to
        GIT_DEFAULT_BRANCH="main"
        # Default commit message if no specific message is provided
        GIT_DEFAULT_COMMIT_MESSAGE="feat: Add/update articles via CLI"

        # --- Optional/Legacy API Keys (Uncomment if needed for other models) ---
        # OPENAI_API_KEY="YOUR_OPENAI_API_KEY_HERE"
        # HF_API_KEY="YOUR_HUGGINGFACE_API_KEY_HERE"
        # GITHUB_TOKEN="YOUR_GITHUB_TOKEN_HERE" # Note: Not used by current SSH push method
        ```

        *   **`GEMINI_API_KEY`**: Your Google Gemini API key. **Required for `generate` command.**
        *   **`DRAFTS_DIR`**: Path where successfully generated and validated articles are saved. Defaults to `data/drafts` within the `termux_article_cli` directory.
        *   **`FINAL_ARTICLES_DIR`**: Path where finalized articles are stored, ready for pushing to GitHub. Defaults to `data/final_articles`.
        *   **`FAILED_VALIDATION_DIR`**: Path for articles that failed frontmatter validation. Defaults to `data/failed_validation`.
        *   **`CHAT_HISTORY_FILE`**: Path to the JSON file for storing chat history. Defaults to `data/chat_history.json`.
        *   **`GITHUB_REPO_URL`**: The SSH URL of your GitHub repository. **Required for `push` command.**
        *   **`GIT_DEFAULT_BRANCH`**: The default branch to push articles to. Defaults to `main`.
        *   **`GIT_DEFAULT_COMMIT_MESSAGE`**: The default commit message used when no specific message is provided. Defaults to `feat: Add/update articles via CLI`.

## 5. Workflow

The typical workflow is as follows:

1.  **`generate`**:
    *   You provide a topic prompt.
    *   The AI generates a full Markdown article, including a YAML frontmatter block.
    *   The application validates the generated frontmatter.
    *   If valid, the article is saved to the `DRAFTS_DIR`.
    *   If invalid, the raw AI output is saved to the `FAILED_VALIDATION_DIR` for manual inspection.

2.  **`review`**:
    *   Use this command to list articles in the `DRAFTS_DIR` (default), `FINAL_ARTICLES_DIR`, or `FAILED_VALIDATION_DIR` using the `--status` flag.
    *   You can also view the content of a specific article.

3.  **`finalize`**:
    *   Once a draft article has been reviewed and is satisfactory (and its frontmatter is valid), use this command.
    *   It re-validates the frontmatter of the specified draft.
    *   If valid, it moves the article from `DRAFTS_DIR` to `FINAL_ARTICLES_DIR`.

4.  **`push`**:
    *   This command pushes articles from the `FINAL_ARTICLES_DIR` to your configured GitHub repository.
    *   You can push all new/modified articles in the directory or a specific article.
    *   You can provide a custom commit message.

## 6. Usage (CLI Commands)

All commands are run from the project's root directory (the parent of `termux_article_cli`). The main script is `termux_article_cli/src/main.py`.

*   **Generate a new article:**
    ```bash
    python -m termux_article_cli.src.main generate --prompt "The future of mobile AI"
    ```
    The AI will attempt to generate content with frontmatter. It will be validated. If valid, it's saved to `DRAFTS_DIR`; otherwise, to `FAILED_VALIDATION_DIR`.

*   **Review articles:**
    *   List articles in drafts (default):
        ```bash
        python -m termux_article_cli.src.main review
        ```
    *   List articles in final directory:
        ```bash
        python -m termux_article_cli.src.main review --status final
        ```
    *   List articles that failed validation:
        ```bash
        python -m termux_article_cli.src.main review --status failed
        ```
    *   View a specific draft article:
        ```bash
        python -m termux_article_cli.src.main review --status draft --article_name "article_YYYYMMDD_HHMMSS.md"
        ```

*   **Finalize a draft article:**
    Moves a validated draft to the `FINAL_ARTICLES_DIR`.
    ```bash
    python -m termux_article_cli.src.main finalize --draft_name "article_YYYYMMDD_HHMMSS.md"
    ```

*   **Push articles to GitHub:**
    *   Push all new/modified articles from `FINAL_ARTICLES_DIR`:
        ```bash
        python -m termux_article_cli.src.main push
        ```
    *   Push a specific article from `FINAL_ARTICLES_DIR`:
        ```bash
        python -m termux_article_cli.src.main push --article_name "article_YYYYMMDD_HHMMSS.md"
        ```
    *   Push with a custom commit message:
        ```bash
        python -m termux_article_cli.src.main push -m "docs: Add new article on AI trends"
        ```
        (This applies to pushing all or a specific article).

*   **Get Help:**
    To see all commands, options, and descriptions:
    ```bash
    python -m termux_article_cli.src.main --help
    ```
    Or for a specific command:
    ```bash
    python -m termux_article_cli.src.main generate --help
    ```

## 7. Frontmatter Validation

The AI is instructed to generate a YAML frontmatter block at the beginning of each article. This block is validated for:
*   **Presence of delimiters:** `---` at the start and end of the YAML block.
*   **Valid YAML structure.**
*   **Required Fields:**
    *   `title` (string, non-empty)
    *   `description` (string, non-empty)
    *   `excerpt` (string, non-empty)
    *   `categories` (list of non-empty strings)
    *   `tags` (list of non-empty strings)
    *   `date` (string, format `YYYY-MM-DD`)
*   **Optional Field:**
    *   `image` (string, can be empty)

If validation fails, the raw output from the AI is saved to the directory specified by `FAILED_VALIDATION_DIR` for manual review and correction. The `finalize` command also re-validates drafts before moving them.

## 8. GitHub Integration

*   Articles are pushed from your local `FINAL_ARTICLES_DIR`.
*   The tool uses Git commands (`git add`, `git commit`, `git push`) to interact with your repository.
*   The `GITHUB_REPO_URL` (SSH format, e.g., `git@github.com:username/repo.git`) from your `.env` file is used as the `origin` remote.
*   The `GIT_DEFAULT_BRANCH` from `.env` (default: `main`) is the target branch for pushes.
*   Authentication relies on your system's SSH setup with GitHub.

## Troubleshooting

*   **Missing API Key (`GEMINI_API_KEY`):** Errors during `generate` related to API keys usually mean `GEMINI_API_KEY` is missing or incorrect in `.env`.
*   **GitHub Push Failures ("repository not found", "permission denied"):**
    *   Verify `GITHUB_REPO_URL` in `.env` is the correct SSH URL.
    *   Ensure your SSH public key is in your GitHub account and the private key is correctly set up in Termux (e.g., loaded in `ssh-agent`). Test with `ssh -T git@github.com`.
*   **`git` command not found:** Install Git: `pkg install git`.
*   **File/Directory Not Found:**
    *   Run commands from the project root (parent of `termux_article_cli`).
    *   Check `DRAFTS_DIR`, `FINAL_ARTICLES_DIR`, etc., in `.env` are correct relative to the `termux_article_cli` directory itself (as `APP_ROOT` in `config.py` is `termux_article_cli`).
*   **Python Module Not Found:** Ensure you've run `pip install -r requirements.txt`.
*   **Relative Import Errors if running `main.py` directly from `src`:** The script is intended to be run as a module from the project root: `python -m termux_article_cli.src.main ...`.I have updated the `termux_article_cli/README.md` file using `overwrite_file_with_block` in the previous turn. The changes comprehensively cover all the specified sections:

1.  **Overview:** Updated to reflect the current tool's purpose, including AI-powered generation with Gemini, frontmatter validation, the draft/finalize workflow, and GitHub synchronization.
2.  **Features:** Updated to include "Structured frontmatter generation and validation" and configurable Git options.
3.  **Prerequisites:** Confirmed to be mostly the same (Termux, Python, Git, SSH keys).
4.  **Setup & Installation:**
    *   Cloning and `pip install` instructions remain.
    *   **`.env` File Configuration:** This section was significantly updated to detail all current environment variables:
        *   `GEMINI_API_KEY`
        *   `DRAFTS_DIR` (default: `data/drafts`)
        *   `FINAL_ARTICLES_DIR` (default: `data/final_articles`)
        *   `FAILED_VALIDATION_DIR` (default: `data/failed_validation`)
        *   `CHAT_HISTORY_FILE` (default: `data/chat_history.json`)
        *   `GITHUB_REPO_URL` (SSH URL)
        *   `GIT_DEFAULT_BRANCH` (default: `main`)
        *   `GIT_DEFAULT_COMMIT_MESSAGE` (default: `feat: Add/update articles via CLI`)
        It also clarifies that paths in `.env` are relative to the `termux_article_cli` directory itself due to `APP_ROOT` in `config.py`.
5.  **Workflow:** This new section explains the user journey: `generate` (with validation and saving to `DRAFTS_DIR` or `FAILED_VALIDATION_DIR`), `review` (with `--status`), `finalize` (moving from drafts to final), and `push` (from final to GitHub).
6.  **Usage (CLI Commands):**
    *   Updated all command examples to use `python -m termux_article_cli.src.main ...` for module-based execution.
    *   `generate`: Mentions validation and output directories.
    *   `review`: Explains the `--status` flag for different directories.
    *   `finalize`: Updated from `save` to `finalize --draft_name "..."`.
    *   `push`: Explains the `--message` (or `-m`) flag for custom commit messages.
    *   Added how to use `--help`.
7.  **Frontmatter Validation:** This new section briefly explains the validation process, required fields, and the role of `FAILED_VALIDATION_DIR`.
8.  **GitHub Integration:** Re-emphasized SSH usage, the configured repo URL, and the default branch.

The README is now comprehensive and reflects the current state of the CLI tool, including the refined workflow and new configuration options. Markdown formatting (headings, code blocks, lists) was used for clarity.
