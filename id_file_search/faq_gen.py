import os
import re
import json
from dotenv import load_dotenv

from google import genai
from google.genai import types
import time
from pydantic import BaseModel


load_dotenv()

class FaqGen:
    """
    """
    SYSTEM_INSTRUCTION = """
    
    You are a financial advisor. Generate questions on retirement planning based on the file store data.
    The questions will be related to a user in context.
    """

    QUESTION_PROMPT = """
    Generate questions on retirement planning based on the file store data.
    Pretend that there is a user who is in context of the file store data.
    The questions will be related to a user in context. The questions will also be related 
    to the documents in the FileSearch store that is provided. The 
    E.g. questions could be like:
    How is RMD be calculated ?
    How can taxes be minimized ?
    How much will my beneficiaries receive after my death ?
    What is the best way to withdraw money from my retirement accounts ?

    Generate 15 such questions. Provide the output as a numbered list.
    """

    FILE_SEARCH_STORE_NAME = 'id-irs-files-store'
    FILE_SEARCH_STORE_NAME_FILE = 'file-search-store-name.dat'
    MODEL_NAME = 'gemini-2.5-flash'

    files_in_store = []

    def __init__(self):
        """
        Args:
            files_list: List of files to search.
        """
        self.file_search_store = None
        self.client = genai.Client()

    def get_or_create_file_search_store(self):
        """Get or create a file search store."""
        try:
            file_search_store_name = None
            file_search_store = None
            if os.path.exists(self.FILE_SEARCH_STORE_NAME_FILE):
                with open(self.FILE_SEARCH_STORE_NAME_FILE, 'r') as f:
                    file_search_store_name = f.read()
                print("Found file search store name: ", file_search_store_name)
                self.file_search_store = self.client.file_search_stores.get(name=file_search_store_name)
                return self.file_search_store

            if not self.file_search_store:
                print("No file search store found. Creating a new one...")
                self.file_search_store = self.client.file_search_stores.create(config={'display_name': self.FILE_SEARCH_STORE_NAME})
                print("Created file search store name  : ", self.file_search_store.name)
                with open(self.FILE_SEARCH_STORE_NAME_FILE, 'w') as f:
                    f.write(self.file_search_store.name)

            if self.file_search_store:
                print("Verifying retrieval from store")
                my_file_search_store = self.client.file_search_stores.get(name=self.file_search_store.name)
                print("Fetched from store name: ", my_file_search_store.name)
                self.file_search_store = my_file_search_store
                return self.file_search_store
            print("No file search store found.")
            return None
        except Exception as e:
            print(f"Exception type: {type(e).__name__}, message: {e}")
            raise e

    # def get_files_in_store(self):
    #     """Get or create a file search store."""

    #     file_search_store = self.get_or_create_file_search_store()
    #     if not file_search_store:
    #         print("No file search store found.")
    #         return []
    #     if file_search_store:
    #         documents_in_store = self.client.file_search_stores.documents.list(parent=file_search_store.name)
    #         print(f"Found {len(documents_in_store)} files in the store {file_search_store.name}.")
    #         for document_in_store in documents_in_store:
    #             print(document_in_store)
    #         return documents_in_store
    #     else:
    #         print("No files found in the store.")
    #         self.files_in_store = []
    #     return self.files_in_store



    # def upload_files(self, files_list: list[str]):
    #     """Upload files to the server."""
    #     self.file_search_store = self.get_or_create_file_search_store()
    #     if not self.file_search_store:
    #         print("No file search store found.")
    #         return []
    #     documents_in_store = []
    #     if self.file_search_store:
    #         documents_in_store = self.client.file_search_stores.documents.list(parent=self.file_search_store.name)
    #         print(f"Found {len(documents_in_store)} files in the store {self.file_search_store.name}.")
    #         for document_in_store in documents_in_store:
    #             print(document_in_store.display_name)

    #     # if documents_in_store and len(documents_in_store) > 0:
    #     #     print("Files already in store. Skipping upload.")
    #     #     return self.file_search_store



    #     document_display_names = [doc.display_name for doc in documents_in_store]
    #     operations = []
    #     for file in files_list:
    #         if os.path.basename(file) in document_display_names:
    #             print(f"File {file} already in store. Skipping upload.")
    #             continue

    #         print(f"Uploading to store {self.file_search_store.name} the file {file}...")
    #         operation = self.client.file_search_stores.upload_to_file_search_store(
    #             file=file,
    #             file_search_store_name=self.file_search_store.name,
    #             config={
    #                 'display_name' : os.path.basename(file),
    #             }
    #         )
    #         operations.append(operation)

    #     for operation in operations:
    #         print(f"Waiting for operation {operation.name} to complete...")
    #         while not operation.done:
    #             time.sleep(1)
    #             operation = self.client.operations.get(operation)
    #         print(f"Operation {operation.name} completed.")


    #     return self.file_search_store



    def generate_faqs(self):
        """Search files in the store."""

        file_search_store = self.get_or_create_file_search_store()
        if not file_search_store:
            print("No file search store found.")
            return []

        # user_data=self.get_dummy_user_data(client_id)
        query=self.QUESTION_PROMPT
        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=self.SYSTEM_INSTRUCTION,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[self.file_search_store.name]
                        )
                    ),
                ]
            )
        )

        return response


faq_generator = FaqGen()
response = faq_generator.generate_faqs()
print(response.text)