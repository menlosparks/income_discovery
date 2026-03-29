import os
import re
from google import genai
from google.genai import types
import time


class FileSearcher:
    """
    """


    def __init__(self, files_list: list[str]):
        """
        Args:
            files_list: List of files to search.
        """
        self.files_list = files_list
        self.file_search_store = None
        self.client = genai.Client()

    def upload_files(self):
        """Upload files to the server."""
        self.file_search_store = self.client.file_search_stores.create(config={'display_name': 'irs-files-store'})

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
            model="gemini-3-flash-preview",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[self.file_search_store.name]
                        )
                    )
                ]
            )
        )

        return response