import subprocess
import os
import re # For checking remote URL
import datetime # For example usage, can be removed if example is stripped

class GitHubHandler:
    def __init__(self, repo_url: str, local_dir: str, default_branch: str, default_commit_message: str):
        self.repo_url = repo_url
        self.local_dir = local_dir # This should be an absolute path
        self.default_branch = default_branch
        self.default_commit_message = default_commit_message
        # Ensure local_dir exists before trying to initialize a repo in it
        os.makedirs(self.local_dir, exist_ok=True)
        self._init_repo()

    def _run_command(self, command: list[str], cwd: str = None) -> tuple[bool, str, str]:
        """
        Runs a shell command using subprocess.
        Returns a tuple: (success_status, stdout, stderr).
        """
        effective_cwd = cwd if cwd is not None else self.local_dir
        
        try:
            process = subprocess.run(
                command,
                cwd=effective_cwd,
                text=True,
                capture_output=True,
                check=False 
            )
            success = process.returncode == 0
            # Basic logging for failed commands
            # if not success:
            #     print(f"Command failed: {' '.join(command)} in {effective_cwd}")
            #     print(f"Exit Code: {process.returncode}")
            #     if process.stdout: print(f"Stdout: {process.stdout.strip()}")
            #     if process.stderr: print(f"Stderr: {process.stderr.strip()}")
            return success, process.stdout.strip(), process.stderr.strip()
        except FileNotFoundError as e:
            return False, "", f"Command not found: {command[0]}. Ensure git is installed and in PATH. Error: {e}"
        except Exception as e:
            return False, "", f"An unexpected error occurred while running command: {' '.join(command)}. Error: {e}"

    def _init_repo(self):
        """
        Initializes the local directory as a git repository and configures the remote.
        """
        git_dir_path = os.path.join(self.local_dir, ".git")
        
        if not (os.path.exists(git_dir_path) and os.path.isdir(git_dir_path)):
            print(f"'{self.local_dir}' is not a git repository. Initializing...")
            success, stdout, stderr = self._run_command(["git", "init"])
            if not success:
                print(f"Failed to initialize git repository in '{self.local_dir}': {stderr}")
                return 

        success, remotes_out, stderr = self._run_command(["git", "remote", "-v"])
        if not success:
            print(f"Failed to get remotes for '{self.local_dir}': {stderr}")
            return

        origin_present = False
        correct_url_for_origin = False
        if self.repo_url: # Only proceed if repo_url is actually provided
            for line in remotes_out.splitlines():
                if line.startswith("origin\t") and self.repo_url in line:
                    correct_url_for_origin = True
                    origin_present = True # if correct_url_for_origin is true, origin must be present
                    break
                elif line.startswith("origin\t"): # origin exists but URL might be wrong
                    origin_present = True


        if origin_present:
            if not correct_url_for_origin and self.repo_url:
                print(f"Remote 'origin' exists but with incorrect URL. Updating to '{self.repo_url}'...")
                # Attempt to remove then add, or set-url. Set-url is cleaner.
                success_set_url, _, stderr_set_url = self._run_command(["git", "remote", "set-url", "origin", self.repo_url])
                if not success_set_url:
                    print(f"Failed to set remote URL for 'origin' to '{self.repo_url}': {stderr_set_url}")
            elif self.repo_url:
                 print(f"Remote 'origin' with correct URL ('{self.repo_url}') already configured.")
            # else: repo_url is empty, do nothing about remote
        elif self.repo_url: # Origin not present and repo_url is specified
            print(f"Remote 'origin' not found. Adding remote 'origin' with URL '{self.repo_url}'...")
            success_add, _, stderr_add = self._run_command(["git", "remote", "add", "origin", self.repo_url])
            if not success_add:
                print(f"Failed to add remote 'origin' with URL '{self.repo_url}': {stderr_add}")
        # If repo_url is not set, no remote operations are performed.
                
    def add_commit_push(self, article_filename: str = None, commit_message: str = None) -> tuple[bool, str]:
        """
        Adds, commits, and pushes changes to the remote repository.
        """
        if not self.repo_url:
            return False, "GitHub repository URL is not configured. Cannot push."

        # Git Add
        target_to_add = article_filename if article_filename else "."
        
        # Security check for article_filename if provided
        if article_filename:
            # Normalize to prevent path traversal, but allow simple subdirectories if local_dir is the root of articles
            # For simplicity, we assume article_filename is just a name, or a path relative to local_dir
            # os.path.join will correctly form the path relative to local_dir.
            # The main concern is 'git add' itself and what `article_filename` could be.
            # If article_filename is like "../../../etc/passwd", this is a problem.
            # For now, assume article_filename is a simple name or relative path within local_dir.
            # A better check might be to ensure it's relative and within the local_dir.
            if ".." in article_filename or os.path.isabs(article_filename):
                 return False, f"Invalid article filename format: '{article_filename}'. Must be a relative path within the articles directory."
            # If article_filename is just a name, it's fine. If it's "subdir/file.md", it's also fine.
            # `git add` will operate relative to `self.local_dir`.

        print(f"Adding '{target_to_add}' to git index in '{self.local_dir}'...")
        success_add, stdout_add, stderr_add = self._run_command(["git", "add", target_to_add])
        if not success_add:
            return False, f"Git add failed for '{target_to_add}': {stderr_add}"

        # Git Commit
        # Check for changes before committing
        success_status, stdout_status, stderr_status = self._run_command(["git", "status", "--porcelain"])
        if not success_status:
            return False, f"Git status check failed: {stderr_status}"
        if not stdout_status: 
            return True, "No changes staged for commit. Working tree clean or changes not added."

        # Determine commit message
        if commit_message: # Specific message provided
            final_commit_message = commit_message
        elif article_filename: # No specific message, but filename provided
            final_commit_message = f"feat: Add/update {os.path.basename(article_filename)} (via CLI)"
        else: # No specific message, no specific filename (e.g. git add .)
             final_commit_message = self.default_commit_message

        print(f"Committing with message: '{final_commit_message}'...")
        success_commit, stdout_commit, stderr_commit = self._run_command(["git", "commit", "-m", final_commit_message])
        if not success_commit:
            if "nothing to commit" in stderr_commit.lower() or "nothing to commit" in stdout_commit.lower():
                 return True, "No changes to commit." # Should have been caught by status, but as a fallback.
            return False, f"Git commit failed: {stderr_commit}"

        # Git Push
        # Try to get current branch name to see if it needs to be created on remote.
        # However, the command `HEAD:{self.default_branch}` handles this by pushing
        # the current local HEAD to the remote branch specified by `self.default_branch`,
        # creating it if it doesn't exist on the remote.
        
        print(f"Pushing current HEAD to remote branch '{self.default_branch}' at '{self.repo_url}'...")
        push_command = ["git", "push", "origin", f"HEAD:{self.default_branch}"]
        success_push, stdout_push, stderr_push = self._run_command(push_command)
        
        if not success_push:
            # Common errors: authentication failure, remote branch not existing (though HEAD:branch should create), non-fast-forward.
            return False, f"Git push failed: {stderr_push}\nStdout: {stdout_push}"
        
        return True, f"Successfully pushed changes to branch '{self.default_branch}'.\n{stdout_push}"

# Example Usage (commented out, for local testing if needed)
# if __name__ == '__main__':
#     # IMPORTANT: Set this environment variable to a test SSH repo URL
#     # export GITHUB_REPO_URL_TEST="git@github.com:yourusername/your-test-repo.git"
#     test_repo_url_env = os.getenv("GITHUB_REPO_URL_TEST")
#     if not test_repo_url_env:
#         print("Please set GITHUB_REPO_URL_TEST environment variable for testing.")
#         print("Example: export GITHUB_REPO_URL_TEST=\"git@github.com:yourusername/your-test-repo.git\"")
#     else:
#         local_articles_dir_test = os.path.join("tmp_test_articles_git") 
#         print(f"Testing GitHubHandler with repo: {test_repo_url_env} and local dir: {local_articles_dir_test}")
#         
#         # Clean up previous test run if any
#         if os.path.exists(local_articles_dir_test):
#             import shutil
#             # On Windows, .git files might be read-only, requiring special handling
#             def onerror(func, path, exc_info):
#                 """Error handler for `shutil.rmtree`."""
#                 import stat
#                 if not os.access(path, os.W_OK): # Is the error an access error ?
#                     os.chmod(path, stat.S_IWUSR)
#                     func(path)
#                 else:
#                     raise
#             shutil.rmtree(local_articles_dir_test, onerror=onerror if os.name == 'nt' else None)
#
#         os.makedirs(local_articles_dir_test, exist_ok=True)
#         handler = GitHubHandler(repo_url=test_repo_url_env, local_dir=local_articles_dir_test)
#     
#         # Create a dummy file to commit
#         dummy_article_name = "test_article_git.md"
#         dummy_article_path = os.path.join(local_articles_dir_test, dummy_article_name)
#         with open(dummy_article_path, "w") as f:
#             f.write(f"Test content for git push at {datetime.datetime.now().isoformat()}")
# 
#         success, msg = handler.add_commit_push(article_filename=dummy_article_name, commit_message="Test commit from GitHubHandler example")
#         print(f"Operation Result: {success}\nMessage: {msg}")
#
#         # Test pushing all (add another file)
#         # with open(os.path.join(local_articles_dir_test, "another_article.md"), "w") as f:
#         #    f.write(f"Another test file at {datetime.datetime.now().isoformat()}")
#         # success_all, msg_all = handler.add_commit_push(commit_message="Test commit all changes")
#         # print(f"Operation Result (all): {success_all}\nMessage: {msg_all}")
#
#         # Test no changes
#         # success_no, msg_no = handler.add_commit_push()
#         # print(f"Operation Result (no changes): {success_no}\nMessage: {msg_no}")
#
#         # Clean up (optional)
#         # print(f"To clean up, remove directory: {local_articles_dir_test}")
