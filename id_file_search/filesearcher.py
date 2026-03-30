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
    the answers to 3 or 4 sentences. If the answer is not in the documents, say so. Be very sure of 
    your calculations and provide the answer in a clear and concise manner. Do not 
    exceed 100 words in your response. 
    You have access to the `get_dummy_user_data` tool to retrieve information about the user's 
    spouse, income, and account balances. Use it whenever a question requires specific user data.
    """

    FILE_SEARCH_STORE_NAME = 'id-irs-files-store'
    MODEL_NAME = 'gemini-2.0-flash'
    files_in_store = []

    def __init__(self, files_list: list[str]):
        """
        Args:
            files_list: List of files to search.
        """
        self.files_list = files_list
        self.file_search_store = None
        self.client = genai.Client()

    def get_files_in_store(self):
        """Get files in the store."""
        my_file_search_store = self.client.file_search_stores.get(name='fileSearchStores/' + self.FILE_SEARCH_STORE_NAME)

        if my_file_search_store and my_file_search_store.files:
            print(f"Found {len(my_file_search_store.files)} files in the store {self.file_search_store.name}.")
            for file in my_file_search_store.files:
                print(f"File: {file.display_name}")
            self.file_search_store = my_file_search_store
            self.files_in_store = my_file_search_store.files
        else:
            print("No files found in the store.")
            self.files_in_store = []
        return self.files_in_store

    def upload_files(self):
        """Upload files to the server."""
        self.file_search_store = self.client.file_search_stores.create(config={'display_name': self.FILE_SEARCH_STORE_NAME})

        operations = []
        for file in self.files_list:
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


            # # Use the actual file path from the loop and set a valid display name
            # sample_file = client.files.upload(
            #     file=file, 
            #     config={'display_name': os.path.basename(file)}
            # )

            # # Create a file search store using the same client
            # file_search_store = client.file_search_stores.create(
            #     config={'display_name': os.path.basename(file) + '-store'}
            # )

        return self.file_search_store



    def search_files(self, query: str):
        """Search files in the store."""

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
                    types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(
                                name='get_dummy_user_data',
                                description='Returns a dummy JSON string with user financial information.',
                                parameters=types.Schema(
                                    type='OBJECT',
                                    properties={}
                                )
                            )
                        ]
                    )
                ]
            )
        )

        return response

    def get_dummy_user_data(self) -> str:
        """Returns a dummy JSON string with user financial information."""
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

        