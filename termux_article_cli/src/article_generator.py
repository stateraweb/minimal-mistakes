import json
import os
import google.generativeai as genai
import datetime # Added for generating current date
class ArticleGenerator:
    def __init__(self, chat_history_file: str, gemini_api_key: str, openai_api_key: str = None, hf_api_key: str = None):
        self.gemini_api_key = gemini_api_key
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                # Initialize the model here or in generate_article.
                # Let's initialize it here if the API key is present.
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest') # Or 'gemini-pro'
            except Exception as e:
                print(f"Error configuring Gemini API or initializing model: {e}")
                self.model = None
        else:
            self.model = None
            print("Warning: Gemini API key not provided. Article generation will be disabled.")

        # self.openai_api_key = openai_api_key # Kept if needed for other funcs
        # self.hf_api_key = hf_api_key       # Kept if needed for other funcs
        self.chat_history_file = chat_history_file
        self.chat_history = self.load_chat_history()


    def generate_article(self, topic_prompt: str) -> str: # Renamed 'prompt' to 'topic_prompt' for clarity
        if not self.model:
            response_text = "Error: Gemini API key not configured or model not initialized."
            if not hasattr(self, 'chat_history'): self.chat_history = []
            self.chat_history.append({"user": topic_prompt, "ai": response_text}) # Use topic_prompt for history
            self.save_chat_history()
            return response_text

        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        detailed_internal_prompt = f"""Please generate a complete Markdown article based on the following topic: "{topic_prompt}"

The article must start with a YAML frontmatter block, enclosed by '---' delimiters.
The frontmatter must include the following fields:
- title: A suitable title for the article.
- description: A concise description (1-2 sentences).
- excerpt: A short excerpt, similar to the description or perhaps slightly longer.
- categories: A YAML list of 1-3 relevant categories (e.g., ['Tech Basics', 'Web Concepts']).
- tags: A YAML list of 2-5 relevant tags (e.g., ['beginner', 'conceptual', 'ai']).
- date: Set this to {current_date}.
- image: (Optional) A relevant image URL or path, or leave blank.

Following the frontmatter, provide the main article content in well-structured Markdown.
Ensure the Markdown is clean and adheres to common standards.
The article content should be comprehensive and informative based on the topic: "{topic_prompt}".
"""
        try:
            # Using the detailed_internal_prompt to generate content
            response = self.model.generate_content(detailed_internal_prompt)
            
            # Accessing the text content. For Gemini, response.text is typical.
            # If response.parts is used, it's often for more complex content (e.g. multimodal)
            # or when specific parts of a streamed response are handled.
            # Based on common usage, response.text should be the primary way for simple text generation.
            if hasattr(response, 'text') and response.text is not None: # Check if text is not None
                response_text = response.text
            elif hasattr(response, 'parts') and response.parts: # Check if parts exist and is not empty
                 response_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            else: # If neither .text nor .parts with text is found.
                response_text = "Error: Could not extract text from Gemini response. The response object did not contain .text (with content) or .parts with text."
                # print(f"DEBUG: Unexpected Gemini response structure: {response}")


        except Exception as e: 
            response_text = f"Error generating article using Gemini API: {str(e)}"
        
        # Store the original user topic_prompt and the full AI response in chat history
        self.chat_history.append({"user": topic_prompt, "ai": response_text})
        self.save_chat_history()
        return response_text # This is the raw_response_text

    def load_chat_history(self) -> list:
        try:
            if os.path.exists(self.chat_history_file):
                with open(self.chat_history_file, 'r') as f:
                    # Check if file is empty to prevent JSONDecodeError
                    if os.path.getsize(self.chat_history_file) == 0:
                        return []
                    return json.load(f)
            return []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_chat_history(self):
        # Ensure the directory exists
        # os.path.dirname() will return an empty string if chat_history_file is just a filename
        # so we ensure that data directory is created if the path is like 'data/chat_history.json'
        dir_name = os.path.dirname(self.chat_history_file)
        if dir_name: # Only create if dirname is not empty
            os.makedirs(dir_name, exist_ok=True)
        
        with open(self.chat_history_file, 'w') as f:
            json.dump(self.chat_history, f, indent=4)

# Example usage (primarily for testing, actual use will be in main.py)
# if __name__ == '__main__':
#     # This assumes a config.py that can provide these values
#     # from config import get_chat_history_file, get_openai_api_key
#     # chat_file = get_chat_history_file() 
#     # temp_chat_file = "data/temp_chat_history.json" 
#     # generator = ArticleGenerator(chat_history_file=temp_chat_file, openai_api_key="dummy_openai_key")
#     # print(generator.generate_article("Tell me about Termux"))
#     # print(generator.generate_article("What are its benefits?"))
#     # print(f"Chat history ({len(generator.chat_history)} entries) saved to {temp_chat_file}")
#     # print("\nLoading history again to verify:")
#     # generator2 = ArticleGenerator(chat_history_file=temp_chat_file)
#     # print(f"History loaded with {len(generator2.chat_history)} entries.")
#     # for entry in generator2.chat_history:
#     #     print(entry)
#
#     # Test with a file in the current directory
#     # temp_chat_file_nodir = "temp_chat_history_nodir.json"
#     # generator_nodir = ArticleGenerator(chat_history_file=temp_chat_file_nodir)
#     # print(generator_nodir.generate_article("Test prompt for no directory"))
#     # print(f"Chat history saved to {temp_chat_file_nodir}")
#     # if os.path.exists(temp_chat_file_nodir):
#     #     os.remove(temp_chat_file_nodir) # Clean up test file
#
#     # Test loading from a non-existent file
#     # non_existent_file = "non_existent_chat.json"
#     # generator_non_existent = ArticleGenerator(chat_history_file=non_existent_file)
#     # print(f"Chat history for non-existent file: {generator_non_existent.chat_history}")
