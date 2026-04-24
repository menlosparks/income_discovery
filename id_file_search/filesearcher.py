import os
import re
import json
from google import genai
from google.genai import types
import time
from pydantic import BaseModel



class FileSearcher:
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

    FILE_SEARCH_STORE_NAME = 'id-irs-files-store'
    FILE_SEARCH_STORE_NAME_FILE = 'file-search-store-name.dat'
    MODEL_NAME = 'gemini-2.5-flash'
    # MODEL_NAME = "gemma-3-27b-it"

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



    def upload_files(self, files_list: list[str], force_reindex=False):
        """Upload files to the server."""
        self.file_search_store = self.get_or_create_file_search_store()
        if not self.file_search_store:
            print("No file search store found.")
            return []
        documents_in_store = []
        if self.file_search_store:
            documents_in_store = self.client.file_search_stores.documents.list(parent=self.file_search_store.name)
            print(f"Found {len(documents_in_store)} files in the store {self.file_search_store.name}.")
            for document_in_store in documents_in_store:
                print(document_in_store.display_name)

        # if documents_in_store and len(documents_in_store) > 0:
        #     print("Files already in store. Skipping upload.")
        #     return self.file_search_store



        document_display_names = [doc.display_name for doc in documents_in_store]
        operations = []
        for file in files_list:
            if os.path.basename(file) in document_display_names:
                print(f"File {file} already in store. Skipping upload.")
                continue

            print(f"Uploading to store {self.file_search_store.name} the file {file}...")
            operation = self.client.file_search_stores.upload_to_file_search_store(
                file=file,
                file_search_store_name=self.file_search_store.name,
                config={
                    'display_name' : os.path.basename(file),
                }
            )
            operations.append(operation)

        for operation in operations:
            print(f"Waiting for operation {operation.name} to complete...")
            while not operation.done:
                time.sleep(1)
                operation = self.client.operations.get(operation)
            print(f"Operation {operation.name} completed.")


        return self.file_search_store



    def search_files(self, query: str, user_data: str):
        """Search files in the store."""

        # user_data=self.get_dummy_user_data(client_id)
        query=query+"\n Answer using the following user data: \n"+user_data
        while True:
            try:
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
                # Accessing the tokens
                usage = response.usage_metadata
                print(f"Prompt tokens: {usage.prompt_token_count}")
                print(f"Candidates tokens: {usage.candidates_token_count}")
                print(f"Total tokens: {usage.total_token_count}")
                return response, None
            except genai.errors.ServerError as e:
                print(f"Server busy error: {e}")
                print("Retrying in 10 seconds... Hit Ctrl-C to exit")
                time.sleep(10)
                continue
            except Exception as e:
                print(f"Error: {e}")
                raise e

    def get_dummy_user_data(self, client_id: str) -> str:
        """Returns a dummy JSON string with user financial information."""

        user_data_map = {
            "client_1": {
                "date_of_birth_spouse_1": "1985-06-15",
                "date_of_birth_spouse_2": "1987-09-22",
                "end_of_year_account_balance": 245000.50,
                "marital_status": "Married Filing Jointly",
                "retirement_age_spouse_1": 65,
                "current_income_spouse_1": 120000,
                "retirement_age_spouse_1_repeat": 65,  # Included as requested
                "current_income_spouse_1_repeat": 120000   # Included as requested
            },
            "client_2": {
                "date_of_birth_spouse_1": "1985-06-15",
                "date_of_birth_spouse_2": "1987-09-22",
                "end_of_year_account_balance": 245000.50,
                "marital_status": "Married Filing Jointly",
                "retirement_age_spouse_1": 65,
                "current_income_spouse_1": 120000,
                "retirement_age_spouse_1_repeat": 65,  # Included as requested
                "current_income_spouse_1_repeat": 120000   # Included as requested
            }
        }   
        user_data = {
            "date_of_birth_spouse_1": "1985-06-15",
            "date_of_birth_spouse_2": "1987-09-22",
            "end_of_year_account_balance": 245000.50,
            "marital_status": "Married Filing Jointly",
            "retirement_age_spouse_1": 65,
            "current_income_spouse_1": 120000,
            "retirement_age_spouse_1_repeat": 65,  # Included as requested
            "current_income_spouse_1_repeat": 120000   # Included as requested
        }
        return json.dumps(user_data, indent=4)

        