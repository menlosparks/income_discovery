import os
import time
import json
import asyncio
import requests
from pageindex import PageIndexClient
import pageindex.utils as utils
import openai
# from weasyprint import HTML

PAGEINDEX_API_KEY = os.environ.get("PAGEINDEX_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class PageIndexSearch:
    """
    """
    SYSTEM_INSTRUCTION = """
    You are a helpful financial advisor. Give concise answers to the user's questions. Limit
    the answers to 3 or 4 sentences. If the answer is not in the documents, say so. 
    You have access to the user_data in JSON format to retrieve information about the user's 
    spouse, income, and account balances. In every response include a reference to the relevant
    field in the  user data which is provided in the JSON object.
    Always make calculations based on the user data, be sure of the calculations and provide the answer in a clear and concise manner. 
    Do not exceed 100 words in your response. 
    """


    def __init__(self):
        """
        Args:
            files_list: List of files to search.
        """
        self.pi_client = PageIndexClient(api_key=os.environ.get("PAGEINDEX_API_KEY"))
        self.file_search_store = None

    async def call_llm(prompt: str, model: str = "gpt-4.1", temperature: float = 0.0) -> str:
        """
        Uses OpenAI's async client to create a chat completion.
        Adjust to your installed OpenAI SDK version if necessary.
        """
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()


    # def convert_html_to_pdf(self, file_name):
    #     """
    #     Converts a local HTML file to a PDF document.
    #     """
    #     try:
    #         # Generate the PDF from the local file path
    #         pdf_file_name = file_name.replace(".html", ".pdf")
    #         base_pdf_file_name = os.path.basename(pdf_file_name)
    #         HTML(filename=file_name).write_pdf(base_pdf_file_name)
    #         print(f"Successfully saved: {base_pdf_file_name}")
    #         return base_pdf_file_name
    #     except Exception as e:
    #         print(f"An error occurred: {e}")
            # return None

    # def save_html_file_to_pdf(self, file_name: str):
    #     """ Save the HTML content of a URL as a PDF file."""
    #     print("Saving HTML to PDF for url: ", file_name)
    #     try:
    #         with open(file_name, "r") as f:
    #             html_content = f.read()
    #         pdf_file_name =    file_name.replace(".html", ".pdf")
    #         with open(pdf_file_name, "w") as f:
    #             f.write(html_content)
    #         print("Saved HTML to PDF successfully")
    #         return pdf_file_name
    #     except Exception as e:
    #         print("Error saving HTML to PDF: ", e)
    #         return None



# Usage
# convert_html_to_pdf('my_report.html', 'final_output.pdf')
    def upload_to_page_index(self, file_name: str):
        """ Save the HTML content of a URL as a PDF file."""
        print("Uploading to Pageindex for url: ", file_name)
        print('Page index api   key: ', self.pi_client.api_key)
        try:
            # pdf_file_name = self.convert_html_to_pdf(file_name)
            # print(f"Saved HTML to PDF successfully as pdf file name ${pdf_file_name}")
            self.pi_client.submit_document(file_name)
            print("Uploaded to Pageindex successfully")
        except Exception as e:
            print("Error uploading to Pageindex: ", e)
        

    def upload_files(self, files_list: list[str], force_reindex=False):
        """ Read the contents of each file in files_list and upload to pinecone"""
        print(f"Uploading {len(files_list)} files to Pageindex...")
        for file in files_list:
            self.upload_to_page_index(file)
