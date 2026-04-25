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
    pageindex_initial_prompt = """
    You are given a question and a tree structure of a document.
    Each node contains a node id, node title, and a corresponding summary.
    Your task is to find all nodes that are likely to contain the answer to the question.
    Question: {query}
    Document tree structure:
    {json.dumps(tree_without_text, indent=2)}
    Please reply in the following JSON format:
    {{
        "thinking": "<Your thinking process on which nodes are relevant to the question>",
        "node_list": ["node_id_1", "node_id_2"]
    }}
    Directly return the final JSON structure. Do not output anything else.
    """

    doc_id_to_file_name = {}


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
            result = self.pi_client.submit_document(file_name)
            doc_id = result["doc_id"]   
            print(f"Uploaded {file_name} to Pageindex successfully with doc_id: {doc_id}")
            return doc_id
        except Exception as e:
            print("Error uploading to Pageindex: ", e)
            return None


    def verify_upload_to_page_index(self, doc_id: str):
        """ Verify the upload to Pageindex."""
        try:
            ## Loop thru the keys of the tree_result and print the keys
            for doc_id in self.doc_id_to_file_name.keys()[:1]:
                tree_result = self.pi_client.get_tree(doc_id)["result"]
                print(f"Verified {doc_id} uploaded to Pageindex successfully")
        except Exception as e:
            print("Error verifying upload to Pageindex: ", e)
            return None

    def delete_document(self, doc_id: str):
        """ Delete all documents in the store."""
        try:
            api_key=os.environ.get("PAGEINDEX_API_KEY")
            response = requests.delete(
                f"https://api.pageindex.ai/doc/{doc_id}/",
                headers={"api_key": api_key},
            )            
            print("Deleted all documents from Pageindex successfully")
        except Exception as e:
            print("Error deleting documents from Pageindex: ", e)
            return None

    def clear_all_documents(self):
        """ List all documents in the store."""
        api_key=os.environ.get("PAGEINDEX_API_KEY")
        response = requests.get(
            "https://api.pageindex.ai/docs",
            headers={"api_key": api_key},
            params={"limit": 100, "offset": 0}
        )
        json_map = response.json()
        
        print(f'Clearing Docs stored count {json_map['total']}')
        for doc in json_map['documents']:
            print(f"Deleting document {doc['id']} name {doc['name']}")
            self.delete_document(doc['id'])

    def list_documents(self):
        """ List all documents in the store."""
        api_key=os.environ.get("PAGEINDEX_API_KEY")
        response = requests.get(
            "https://api.pageindex.ai/docs",
            headers={"api_key": api_key},
            params={"limit": 100, "offset": 0}
        )
        print(f"Documents in Pageindex: {str(response.json())} is of type {type(response.json())}")
        json_map = response.json()
        
        print(f'Docs stored are {json_map['total']}')
        for doc in json_map['documents']:
            print(f"Doc ID: {doc['id']}, Page num: {doc['pageNum']}, Name: {doc['name']}, Description: {doc['description']}, Created At: {doc['createdAt']}")
        
        return  json_map['documents']


    def check_tree_ready(self):
        """ Check if all documents are ready."""
        ready_docs = []
        all_docs_ids = self.doc_id_to_file_name.keys()
        
        while len(ready_docs) < len(all_docs_ids):
            for doc_id in all_docs_ids:
                ready = self.pi_client.is_retrieval_ready(doc_id)
                if ready:
                    print(f"Tree ready for doc_id: {doc_id} ")
                    ready_docs.append(doc_id)
            if len(ready_docs) < len(all_docs_ids):
                remaining_docIds =  len(all_docs_ids) - len(ready_docs)
                print(f"Tree not ready for doc_id: {remaining_docIds}. Sleeping 5 ")
                time.sleep(10)
            

    def upload_files(self, files_list: list[str], force_reindex=False):
        """ Read the contents of each file in files_list and upload to pinecone"""
        document_names = []
        if not force_reindex:
            documents = self.list_documents()
            document_names = [doc['name'] for doc in documents]
        else:
            self.clear_all_documents()
            # return document_names
        print(f"Documents already in Pageindex: {document_names}")
        print(f"Uploading {len(files_list)} files to Pageindex...")
        for file in files_list:
            base_name = os.path.basename(file)
            if (base_name in document_names):
                print(f"File {base_name} already exists in Pageindex. Skipping...")
                continue
            doc_id = self.upload_to_page_index(file)
            self.doc_id_to_file_name[doc_id] = file
        print("doc_id_to_file_name uploaded to Pageindex: ", self.doc_id_to_file_name)
        self.check_tree_ready()
        return self.doc_id_to_file_name

    def get_document_tree(self, doc_id: str):
        """ Get the document tree."""
        try:
            tree_result = self.pi_client.get_tree(doc_id)["result"]
            print(f"Verified {doc_id} uploaded to Pageindex successfully")
            return tree_result
        except Exception as e:
            print("Error getting document tree from Pageindex: ", e)
            return None

    def search_files(self, query: str, user_data: str):
        """Search files in the store."""
        print("Search not implemented yet")
        documents = self.list_documents()
        document_names = [doc['name'] for doc in documents]
        document_ids = [doc['id'] for doc in documents]
        print(f"Document names: {document_names}")
        print(f"Document IDs: {document_ids}")
        for doc_id in document_ids[:1]:
            tree_result = self.get_document_tree(doc_id)
            tree_without_text = utils.remove_fields(tree_result.copy(), fields=["text"])
            print(f"Verified {doc_id} uploaded to Pageindex successfully has tree: {tree_result}")
            
        
        
        # pageindex_initial_prompt
        
        
        
        return None, None
        
        
