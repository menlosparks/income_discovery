import requests
from bs4 import BeautifulSoup
import os
from typing import List
from google import genai
from google.genai import types
# from google.colab import userdata
# from IPython.display import HTML, display

SYSTEM_INSTRUCTION = """
You are a helpful financial advisor. Give concise answers to the user's questions. Limit
the answers to 3 or 4 sentences. If the answer is not in the documents, say so. Be very sure of
your calculations and provide the answer in a clear and concise manner. Do not
exceed 100 words in your response.
You have access to the user_data which has info about the user's
spouse, income, and account balances. Use it whenever a question requires specific user data.
Use any account balances to make calculations
"""

QUERY ="How are Required Minimum Distributions (RMDs) calculated for my various retirement accounts?"

user_data = """
{
                "date_of_birth_spouse_1": "1955-06-15",
                "date_of_birth_spouse_2": "1957-09-22",
                "end_of_year_401K_balance": 3345000.50,
                "end_of_year_traditional_ira_balance": 756000.50,
                "end_of_year_roth_ira_balance": 93000.50,
                "annual_pension_income_spouse_1": 78000,
                "annual_pension_income_spouse_2": 55000,
                "retirement_age_spouse_1": 65,
                "current_income_spouse_1": 780000,
                "retirement_age_spouse_2": 65,  # Included as requested
                "current_income_spouse_2": 550000,   # Included as requested
                "self_employed_spouse_1": True,
                "self_employed_spouse_2": False
            }
"""
# MODEL_NAME = 'gemma-3-4b-it'
MODEL_NAME = 'gemini-2.5-flash'
# MODEL_NAME = 'gemini-3.1-pro-preview'
CHUNK_SIZE_KB=40
CHUNK_OVERLAP_KB = 6
MAX_TOTAL_SIZE_KB = 50


class Chunker:
    """
    A class to download files from IRS URLs and save them to a specified directory.
    """

    def __init__(self, storage_dir: str):
        """
        Initialize the downloader with a target storage directory.
        """
        self.storage_dir = storage_dir
        # Ensure target directory exists
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    # def show_html_file(self, file_path):
    #     """Opens and displays the content of an HTML file in the notebook."""
    #     if not os.path.exists(file_path):
    #         print(f"Error: File {file_path} not found.")
    #         return
    #     with open(file_path, 'r', encoding='utf-8') as f:
    #         html_content = f.read()
    #     display(HTML(html_content))

    def remove_unwanted_tags(self, html_content):
        """Removes <strong> and <a> tags but keeps the text inside them."""
        temp_soup = BeautifulSoup(html_content, "html.parser")
        for tag in temp_soup.find_all(["strong", "a"]):
            tag.unwrap()
        return str(temp_soup)

    def chunk_text_with_overlap(self, text, chunk_size, overlap_size):
        """Breaks a string into chunks of chunk_size with overlap_size overlap (in bytes)."""
        encoded_text = text.encode('utf-8')
        chunks = []
        start = 0
        print(f'Chunking encoded text of len {len(encoded_text)}')
        while start < len(encoded_text):
            print(f'Starting chunk at index {start}')
            end = start + chunk_size
            chunk = encoded_text[start:end].decode('utf-8', errors='ignore')
            chunks.append(chunk)
            if end >= len(encoded_text):
                break
            start += (chunk_size - overlap_size)
        return chunks


    def _get_filename_from_url(self, url: str) -> str:
        """
        Extract a filename from the URL.
        """
        # Get the last part of the URL as the filename
        filename = url.rstrip('/').split('/')[-1]
        # Add .html if no extension is present (likely a page)
        if '.' not in filename:
            filename += '.html'
        return filename

    def download_and_process_html(
        self,
        url,
        max_total_size_kb=MAX_TOTAL_SIZE_KB,
        max_chunk_size_kb=CHUNK_SIZE_KB,
    ):
        """Downloads HTML, extracts content from a main container, and chunks it."""
        output_dir = self.storage_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = self._get_filename_from_url(url)


        print(f"Downloading HTML from: {url}")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {url}: {e}")
            return

        soup = BeautifulSoup(response.content, "html.parser")

        # Try to find the most relevant content container
        content_container = soup.find("article") or soup.find("main") or soup.find("div", {"id": "main-content"}) or soup.find("div", class_="field-item")

        if not content_container:
            content_container = soup.find("body")

        # Remove unwanted elements
        for unwanted in content_container.find_all(["script", "style", "img", "iframe", "link", "meta", "svg", "source", "noscript", "nav", "footer"]):
            unwanted.decompose()

        # Get inner HTML as the main string to process
        main_html_string = "".join([str(el) for el in content_container.contents])

        if not main_html_string:
            print("No content found in the container.")
            return

        main_html_string = self.remove_unwanted_tags(main_html_string)
        processed_soup = BeautifulSoup(main_html_string, "html.parser")
        main_html_size_bytes = len(main_html_string.encode("utf-8"))
        print(f"Processed content size: {main_html_size_bytes / 1024:.2f} KB")

        if main_html_size_bytes > (max_total_size_kb * 1024):
            print(f"Content exceeds {max_total_size_kb} KB. Chunking...")
            chunks = self.chunk_with_overlap(processed_soup, output_dir, filename, max_chunk_size_kb)
            # chunk_content(processed_soup, output_dir, max_chunk_size_kb)
            # self.prompt_model(chunks[0])
        else:
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(main_html_string)
            print(f"Saved content to: {filepath}")
            # self.prompt_model(main_html_string)

    # def prompt_model(self, main_html_string):
    #     print ('Prompt str length ' + str(len(main_html_string)))
    #     # query="Use this context to answer below question \n"+ "\
    #     query=SYSTEM_INSTRUCTION + "\n\
    #     Use this context to answer below question \n" + main_html_string + "\
    #             \n THis is the question: " + QUERY + "\
    #             \n Answer using the following user data: \n"+user_data

    #     # Get the API key from Colab secrets
    #     GEMINI_API_KEY = userdata.get('GOOGLE_API_KEY')
    #     client = genai.Client(api_key=GEMINI_API_KEY)

    #     # model_to_use = client.generative_models.get(MODEL_NAME)
    #     response = client.models.generate_content(
    #                 model=MODEL_NAME,
    #                 contents=query)
    #                 # config=types.GenerateContentConfig(
    #                 #     system_instruction=SYSTEM_INSTRUCTION))
    #     usage = response.usage_metadata
    #     print(f"Prompt tokens: {usage.prompt_token_count} \
    #     Candidates tokens: {usage.candidates_token_count} \
    #     Total tokens: {usage.total_token_count}")
    #     print(f"\nAnswer:\n{response.text}")

    def chunk_with_overlap(self, soup_obj, output_dir, filename, max_chunk_size_kb):


        chunks = self.chunk_text_with_overlap(soup_obj, max_chunk_size_kb * 1024, CHUNK_OVERLAP_KB *1024)

        print(f'Breaking into {len(chunks)} chunks')

        for i, chunk in enumerate(chunks):
            chunk_filename = os.path.join(output_dir, f"{i:03d}_{filename}")
            with open(chunk_filename, "w", encoding="utf-8") as f:
                f.write(chunk)
        return chunks

    def chunk_content(self, soup_obj, output_dir, max_chunk_size_kb):
        current_chunk_elements = []
        current_chunk_size_bytes = 0
        chunk_count = 0
        max_chunk_size_bytes = max_chunk_size_kb * 1024

        for element in soup_obj.children:
            if element.name is None: continue
            element_html = str(element)
            element_size = len(element_html.encode("utf-8"))
            is_heading = element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

            if (current_chunk_elements and current_chunk_size_bytes + element_size > max_chunk_size_bytes) or (current_chunk_elements and is_heading):
                chunk_count += 1
                chunk_filename = os.path.join(output_dir, f"chunk_{chunk_count:03d}.html")
                with open(chunk_filename, "w", encoding="utf-8") as f:
                    f.write("".join(map(str, current_chunk_elements)))
                current_chunk_elements = [element]
                current_chunk_size_bytes = element_size
            else:
                current_chunk_elements.append(element)
                current_chunk_size_bytes += element_size

        if current_chunk_elements:
            chunk_count += 1
            chunk_filename = os.path.join(output_dir, f"chunk_{chunk_count:03d}.html")
            with open(chunk_filename, "w", encoding="utf-8") as f:
                f.write("".join(map(str, current_chunk_elements)))


    def download_multiple(self, urls: List[str]) -> List[str]:
        """
        Download multiple URLs.
        """
        saved_paths = []
        for url in urls:
            path = self.download_and_process_html(url)
            if path:
                saved_paths.append(path)
        return saved_paths

# Run usage
# html_url = "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-required-minimum-distributions-rmds"
# html_url = "https://www.irs.gov/publications/p590b"
# download_and_process_html(html_url)
# show_html_file("html_chunks/chunk_000.html")