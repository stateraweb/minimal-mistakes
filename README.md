# Termux Article TUI

## 1. Overview

Termux Article TUI is a Text User Interface (TUI) application, built with [Textual](https://textual.textualize.io/), designed to streamline the creation and management of articles or blog posts, especially within the Termux environment. It leverages Google's Gemini AI for content generation (including structured YAML frontmatter), incorporates frontmatter validation, supports a draft-review-finalize workflow, and enables synchronization of final articles with a GitHub repository via SSH.

## 2. Features

*   **AI-Powered Article Generation:** Utilizes the Google Gemini API (via direct HTTP requests) to create full Markdown articles, including YAML frontmatter, from user prompts within an interactive TUI.
*   **Structured Frontmatter Generation and Validation:** The AI is instructed to generate specific frontmatter fields. The application then validates this frontmatter and displays the results in the TUI.
*   **Interactive Workflow Management:**
    *   **Generate:** Create new articles via a dedicated screen with input fields and status displays.
    *   **Review:** Browse articles in `drafts`, `final_articles`, or `failed_validation` directories using interactive lists and view their content directly within the TUI.
    *   **Finalize (Planned):** A TUI screen to select and move validated drafts to the final articles directory.
    *   **Push to GitHub (Planned):** A TUI screen to push finalized articles to your GitHub repository.
*   **Markdown Format:** Articles are generated and managed in Markdown (`.md`).
*   **Chat History:** Maintains a JSON file of prompts and AI responses for context.
*   **Configuration via `.env`:** API keys, repository URLs, local directory paths, and Git defaults are managed through an environment file.

## 3. Prerequisites

*   **Termux Environment (Recommended):** While it may run in other Python environments, it's designed with Termux in mind.
*   **Python:** Python 3.x installed (`pkg install python` in Termux).
*   **Git:** Git installed (`pkg install git` in Termux).
*   **SSH Key for GitHub:**
    *   An SSH key must be generated (`ssh-keygen`).
    *   The public key must be added to your GitHub account's SSH keys.
    *   SSH agent should be configured if using passphrases.
*   **Internet Connection:** For AI article generation and pushing to GitHub.

## 4. Setup & Installation

1.  **Clone Repository:**
    ```bash
    git clone <your_repository_url>
    cd termux_article_cli # Or your repository name, ensure this matches the actual repo dir
    ```
    (Ensure you are in the project's root directory for the following steps).

2.  **Install Dependencies:**
    This project uses Python packages listed in `requirements.txt`, including `textual` for the TUI.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment File (`.env`):**
    *   Copy the example environment file (usually from the project root):
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file with your configurations:
        ```env
        # --- API Keys ---
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE" # Mandatory for article generation

        # --- Directory Paths (relative to the application's root 'termux_article_cli' directory) ---
        DRAFTS_DIR="data/drafts"
        FINAL_ARTICLES_DIR="data/final_articles"
        FAILED_VALIDATION_DIR="data/failed_validation"
        CHAT_HISTORY_FILE="data/chat_history.json"
        # Note: The system prompt is now loaded from termux_article_cli/data/sys_prompt.md

        # --- GitHub Configuration ---
        GITHUB_REPO_URL="git@github.com:your_username/your_repository.git" # Mandatory for 'push'
        GIT_DEFAULT_BRANCH="main"
        GIT_DEFAULT_COMMIT_MESSAGE="feat: Add/update articles via TUI"
        ```
        *   **`GEMINI_API_KEY`**: Your Google Gemini API key.
        *   Directory paths (`DRAFTS_DIR`, etc.) are relative to the `termux_article_cli` app root directory.
        *   GitHub settings are for the 'Push to GitHub' feature.

## 5. Running the Application

To run the Termux Article TUI (ensure you are in the project's root directory, one level above `termux_article_cli`):
```bash
python -m termux_article_cli.src.main
```
This will launch the Textual interface in your terminal.

## 6. Usage / Workflow

The application provides a menu-driven interface:

1.  **Main Menu:**
    *   Navigate using Tab, Shift+Tab, arrow keys, or by clicking. Press Enter or click to activate a button.
    *   Select an option:
        *   **Generate New Article:** Opens a screen to input a prompt and generate an article.
        *   **Review Articles:** Opens a sub-menu to choose between viewing Drafts, Final Articles, or Failed Validation articles.
        *   **Finalize Draft (Planned):** Will open a screen to select and finalize drafts.
        *   **Push to GitHub (Planned):** Will open a screen to manage pushing articles.
        *   **Exit:** Opens a confirmation dialog before quitting the application.

2.  **Generate New Article Screen:**
    *   Type your article prompt into the input field.
    *   Press the "Generate Article" button.
    *   Status messages will appear, indicating progress (generation, validation, saving).
    *   The result (success with path, or error message) will be displayed.

3.  **Review Articles Workflow:**
    *   From the "Review Articles" menu, select the category you wish to view.
    *   An **Article List Screen** will display articles in that category.
    *   Select an article from the list.
    *   The **View Article Screen** will open, displaying the content of the selected article.
    *   Use the "Back" buttons to navigate to previous screens.

## 7. Frontmatter Validation

The application still performs frontmatter validation as described previously, but results are shown within the TUI. If generation fails validation, the raw AI output is saved to the `FAILED_VALIDATION_DIR`.

## 8. GitHub Integration (Planned TUI Feature)

The underlying GitHub synchronization logic (using SSH) remains. The TUI will provide an interface to trigger pushes from the `FINAL_ARTICLES_DIR` when this feature is implemented.

## 9. Troubleshooting

*   **Missing API Key (`GEMINI_API_KEY`):** Errors during generation related to API keys usually mean `GEMINI_API_KEY` is missing or incorrect in `.env`. The TUI should display an error.
*   **GitHub Push Failures (When Implemented):**
    *   Verify `GITHUB_REPO_URL` in `.env`.
    *   Ensure SSH setup is correct.
*   **Display Issues:** If the TUI doesn't look right, ensure your terminal supports modern features or try a different terminal emulator. Textual works best in terminals with good Unicode and color support.
*   **Module Not Found / Import Errors:**
    *   Ensure you've run `pip install -r requirements.txt` in your project's virtual environment (if you use one).
    *   Run the application as a module: `python -m termux_article_cli.src.main` from the project root directory (the one containing `termux_article_cli` and `README.md`).
```
