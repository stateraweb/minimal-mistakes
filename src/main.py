import os 
import datetime 

# Textual imports
import asyncio # For potential sleep if needed, though run_worker handles threads
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem, Markdown # Added Markdown
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.worker import Worker, get_current_worker

# Keep existing imports for core logic - they will be called from TUI methods later
from .config import (
    get_drafts_dir, get_final_articles_dir, get_failed_validation_dir,
    get_gemini_api_key, get_chat_history_file_path, get_github_repo_url,
    get_git_default_branch, get_git_default_commit_message
)
from .article_generator import ArticleGenerator
from .article_utils import save_article, load_article, list_articles, validate_frontmatter
from .github_handler import GitHubHandler

class MainScreen(Screen):
    """Main screen for the application. Will host the main menu."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Welcome to Termux Article CLI - TUI Mode!", id="main_title", classes="title"),
            Button("Generate New Article", id="btn_generate", variant="primary"),
            Button("Review Articles", id="btn_review", variant="primary"),
            Button("Finalize Draft", id="btn_finalize", variant="primary"),
            Button("Push to GitHub", id="btn_push", variant="primary"),
            Button("Exit", id="btn_exit", variant="error"),
            id="main_container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button press events for the main menu."""
        if event.button.id == "btn_generate":
            self.app.push_screen(GenerateScreen()) 
        elif event.button.id == "btn_review":
            self.app.push_screen(ReviewMenuScreen()) 
        elif event.button.id == "btn_finalize":
            self.app.notify("Finalize Draft button pressed (placeholder)")
        elif event.button.id == "btn_push":
            self.app.notify("Push to GitHub button pressed (placeholder)")
        elif event.button.id == "btn_exit":
            self.app.push_screen(QuitScreen())

class QuitScreen(Screen):
    """A screen to confirm if the user wants to quit."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Are you sure you want to quit?", id="quit_question", classes="centered_text"),
            Horizontal(
                Button("Yes", variant="error", id="btn_quit_yes"),
                Button("No", variant="primary", id="btn_quit_no"),
                id="quit_buttons_container"
            ),
            id="quit_dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_quit_yes":
            self.app.exit()
        elif event.button.id == "btn_quit_no":
            self.app.pop_screen()

class GenerateScreen(Screen):
    """Screen for generating a new article."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Generate New Article", classes="title"),
            Static("Enter your article prompt below:"),
            Input(placeholder="e.g., The future of AI in mobile technology", id="prompt_input"),
            Button("Generate Article", variant="success", id="btn_do_generate"),
            Static("", id="generation_status_output"), # For status messages or output
            Button("Back to Main Menu", variant="default", id="btn_back_to_main"),
            id="generate_container"
        )
        yield Footer()

    def _perform_generation(self, prompt_text: str) -> tuple[bool, str, dict | None]:
        """
        Handles the actual article generation, validation, and saving.
        Returns a tuple: (success_status, message, frontmatter_data_or_none).
        This method is intended to be run in a worker thread.
        """
        try:
            worker = get_current_worker() 
            if worker.is_cancelled:
                return False, "Generation cancelled.", None

            self.query_one("#generation_status_output", Static).update("Initializing generator...")
            
            gemini_key = get_gemini_api_key()
            chat_history_path = get_chat_history_file_path()
            drafts_dir = get_drafts_dir()
            failed_dir = get_failed_validation_dir()

            if not gemini_key:
                return False, "Error: Gemini API key not configured.", None

            article_generator = ArticleGenerator(
                chat_history_file=chat_history_path,
                gemini_api_key=gemini_key
            )

            if worker.is_cancelled:
                return False, "Generation cancelled.", None
            self.query_one("#generation_status_output", Static).update(f"Generating article for prompt: '{prompt_text}'...")
            
            raw_ai_output = article_generator.generate_article(prompt_text)

            if worker.is_cancelled:
                return False, "Generation cancelled.", None

            if "Error:" in raw_ai_output[:30]: 
                error_filename = f"generation_error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                save_article(f"Prompt: {prompt_text}\n\nError: {raw_ai_output}", failed_dir, error_filename)
                return False, f"Generation Error: {raw_ai_output}", None

            self.query_one("#generation_status_output", Static).update("Validating frontmatter...")
            is_valid, frontmatter_data, error_message = validate_frontmatter(raw_ai_output)

            if is_valid:
                self.query_one("#generation_status_output", Static).update("Saving to drafts...")
                saved_path = save_article(raw_ai_output, drafts_dir)
                return True, f"Article draft generated, validated, and saved to: {saved_path}", frontmatter_data
            else:
                self.query_one("#generation_status_output", Static).update("Saving to failed validation directory...")
                saved_path = save_article(raw_ai_output, failed_dir) 
                return False, f"Frontmatter Validation Failed: {error_message}. Raw output saved to: {saved_path}", None
        except Exception as e:
            return False, f"An unexpected error occurred during generation: {str(e)}", None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_do_generate":
            prompt_input_widget = self.query_one("#prompt_input", Input)
            prompt_text = prompt_input_widget.value
            
            if not prompt_text:
                self.app.notify("Please enter a prompt.", severity="warning")
                return

            prompt_input_widget.disabled = True
            event.button.disabled = True
            self.query_one("#generation_status_output", Static).update("Starting generation process...")

            self.run_worker(
                self._perform_generation(prompt_text), 
                self._on_generation_complete, 
                exclusive=True 
            )
        elif event.button.id == "btn_back_to_main":
            self.app.pop_screen()

    def _on_generation_complete(self, result: tuple[bool, str, dict | None]) -> None:
        """Called when the generation worker finishes."""
        success, message, frontmatter_data = result

        self.query_one("#prompt_input", Input).disabled = False
        self.query_one("#btn_do_generate", Button).disabled = False
        
        self.query_one("#generation_status_output", Static).update(message) 
        
        if success:
            self.app.notify("Article generation successful!", severity="information")
        else:
            self.app.notify("Article generation failed.", severity="error")
        
        if frontmatter_data:
             title = frontmatter_data.get('title', 'N/A')
             date = frontmatter_data.get('date', 'N/A')
             current_output = self.query_one("#generation_status_output", Static).renderable
             self.query_one("#generation_status_output", Static).update(
                 f"{current_output}\nTitle: {title}\nDate: {date}"
             )

class ReviewMenuScreen(Screen):
    """Screen to choose which article category to review."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Review Articles", classes="title"),
            Button("View Drafts", id="btn_review_drafts", variant="primary"),
            Button("View Final Articles", id="btn_review_final", variant="primary"),
            Button("View Failed Validation Articles", id="btn_review_failed", variant="primary"),
            Button("Back to Main Menu", id="btn_review_back_to_main", variant="default"),
            id="review_menu_container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_review_drafts":
            self.app.push_screen(ArticleListScreen(directory_type="Drafts", directory_path=get_drafts_dir()))
        elif event.button.id == "btn_review_final":
            self.app.push_screen(ArticleListScreen(directory_type="Final Articles", directory_path=get_final_articles_dir()))
        elif event.button.id == "btn_review_failed":
            self.app.push_screen(ArticleListScreen(directory_type="Failed Validation", directory_path=get_failed_validation_dir()))
        elif event.button.id == "btn_review_back_to_main":
            self.app.pop_screen()

class ArticleListScreen(Screen):
    """Screen to display a list of articles from a directory."""

    def __init__(self, directory_type: str, directory_path: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.directory_type = directory_type
        self.directory_path = directory_path
        self.title = f"Articles in: {self.directory_type.title()}" 

    def compose(self) -> ComposeResult:
        yield Header() 
        yield Static(f"Listing: {self.directory_type.title()}", classes="title") 
        yield ListView(id="article_list_view")
        yield Button("Back to Review Menu", id="btn_back_to_review_menu", variant="default")
        yield Footer()

    async def on_mount(self) -> None: 
        """Called when the screen is mounted. Populates the article list."""
        try:
            article_filenames = list_articles(self.directory_path)
            list_view = self.query_one("#article_list_view", ListView)
            list_view.clear() 

            if not article_filenames:
                list_view.append(ListItem(Static("No articles found in this directory.")))
            else:
                for filename in article_filenames:
                    list_view.append(ListItem(Static(filename)))
        except Exception as e:
            list_view = self.query_one("#article_list_view", ListView)
            list_view.clear()
            list_view.append(ListItem(Static(f"Error listing articles: {e}")))
            self.app.notify(f"Error loading articles: {e}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_back_to_review_menu":
            self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_item = event.item
        if selected_item:
            try:
                static_widget = selected_item.query_one(Static)
                article_name_str = str(static_widget.renderable) 

                if "No articles found" in article_name_str or "Error listing articles" in article_name_str:
                    self.app.notify("This is an informational message, not an article.", severity="warning")
                    return

                full_article_path = os.path.join(self.directory_path, article_name_str)
                self.app.push_screen(ViewArticleScreen(article_path=full_article_path, article_name=article_name_str))
            except Exception as e:
                self.app.notify(f"Error processing selection for navigation: {e}", severity="error")

class ViewArticleScreen(Screen):
    """Screen to display the content of a selected article."""

    def __init__(self, article_path: str, article_name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.article_path = article_path
        self.article_name = article_name
        self.title = f"Viewing: {self.article_name}" 

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self.title, classes="title", id="article_view_title") 
        yield Markdown("", id="article_markdown_content") 
        yield Button("Back to Article List", id="btn_back_to_article_list", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_back_to_article_list":
            self.app.pop_screen()

    async def on_mount(self) -> None: 
        """Called when the screen is mounted. Loads and displays the article content."""
        try:
            article_content = load_article(self.article_path)
            markdown_widget = self.query_one("#article_markdown_content", Markdown)
            
            if article_content is not None:
                markdown_widget.update(article_content)
            else:
                markdown_widget.update(f"# Error\n\nCould not load article content from:\n{self.article_path}")
                self.app.notify(f"Error loading article: {self.article_name}", severity="error")
        except Exception as e:
            markdown_widget = self.query_one("#article_markdown_content", Markdown)
            markdown_widget.update(f"# Error\n\nAn unexpected error occurred while loading article:\n{e}")
            self.app.notify(f"Unexpected error loading article: {e}", severity="error")

class TermuxArticleApp(App):
    """The main Textual application class."""

    TITLE = "Termux Article CLI"
    # CSS_PATH = "styles.css" # Optional: Can add a CSS file later

    SCREENS = {
        "main_screen": MainScreen,
        "quit_screen": QuitScreen,
        "generate_screen": GenerateScreen,
        "review_menu_screen": ReviewMenuScreen,
        "article_list_screen": ArticleListScreen,
        "view_article_screen": ViewArticleScreen 
    }

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        self.push_screen("main_screen") 

if __name__ == "__main__":
    app = TermuxArticleApp()
    app.run()
