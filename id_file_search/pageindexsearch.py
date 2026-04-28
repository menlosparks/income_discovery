import os
import time
import json
import asyncio
from google import genai

import requests
from pageindex import PageIndexClient
import pageindex.utils as utils
import openai
# from weasyprint import HTML
from common import SYSTEM_INSTRUCTION, MODEL_NAME, call_shared_llm

PAGEINDEX_API_KEY = os.environ.get("PAGEINDEX_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
NUMBER_OF_NODES_FOR_QUERY_MATCH = 2

class PageIndexSearch:
    """
    """
    # SYSTEM_INSTRUCTION = """
    # You are a helpful financial advisor. Give concise answers to the user's questions. Limit
    # the answers to 3 or 4 sentences. If the answer is not in the documents, say so. 
    # You have access to the user_data in JSON format to retrieve information about the user's 
    # spouse, income, and account balances. In every response include a reference to the relevant
    # field in the  user data which is provided in the JSON object.
    # Always make calculations based on the user data, be sure of the calculations and provide the answer in a clear and concise manner. 
    # Do not exceed 100 words in your response. 
    # """
    original_initial_search_prompt = """
        You are given a question and a tree structure of a document.
        Each node contains a node id, node title, and a corresponding summary.
        Your task is to find all nodes that are likely to contain the answer to the question.
        Question: {{query}}
        Document tree structure:
        {{json.dumps(tree_without_text, indent=2)}}
        Please reply in the following JSON format:
        {{
            "thinking": "<Your thinking process on which nodes are relevant to the question>",
            "node_list": ["node_id_1", "node_id_2"]
        }}
        Directly return the final JSON structure. Do not output anything else.
        Do not include any backticks or code formatting in the response.
        Your response should be only the JSON object.
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
    # MODEL_NAME = 'gemini-2.5-flash'

    doc_id_to_file_name = {}


    def __init__(self):
        """
        Args:
            files_list: List of files to search.
        """
        self.pi_client = PageIndexClient(api_key=os.environ.get("PAGEINDEX_API_KEY"))
        self.file_search_store = None
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    def call_llm(self, prompt: str) -> str:
        response, usage = call_shared_llm(prompt, self.client)
        return response.text, usage
        # """
        # Uses OpenAI's async client to create a chat completion.
        # Adjust to your installed OpenAI SDK version if necessary.
        # """
        # response = self.client.models.generate_content(
        #     model=MODEL_NAME,
        #     contents=prompt);
        # usage = response.usage_metadata
        # print(f"Prompt tokens: {usage.prompt_token_count} Candidates tokens: {usage.candidates_token_count} Total tokens: {usage.total_token_count}")

        return response.text, usage
        # client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        # response = client.chat.completions.create(
        #     model=model,
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=temperature
        # )
        # return response.choices[0].message.content.strip()


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


    # def verify_upload_to_page_index(self, doc_id: str):
    #     """ Verify the upload to Pageindex."""
    #     try:
    #         ## Loop thru the keys of the tree_result and print the keys
    #         for doc_id in self.doc_id_to_file_name.keys()[:1]:
    #             tree_result = self.pi_client.get_tree(doc_id)["result"]
    #             print(f"Verified {doc_id} uploaded to Pageindex successfully")
    #     except Exception as e:
    #         print("Error verifying upload to Pageindex: ", e)
    #         return None

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
            print (f"Tree for document {doc_id}: ")
            utils.print_tree(tree_result)
            return tree_result
        except Exception as e:
            print("Error getting document tree from Pageindex: ", e)
            return None

    def get_doc_context(self, tree_search_result, matching_nodes, node_map) -> str:
        """ Get node text for a document."""
        try:
            retrieved_texts = []
            for nid in matching_nodes:
                node = node_map.get(nid)
                print(f"Retrieving context for matching node {nid} title: {node['title'][:100]}")
                if not node:
                    continue
                # node['text'] might be a list of page-level strings or a string
                node_text = node.get("text") or ""
                if isinstance(node_text, list):
                    node_text = "\n\n".join(node_text)
                retrieved_texts.append(f"--- Node {nid}: {node.get('title')} ---\n{node_text}")
            combined_context = "\n\n".join(retrieved_texts) or "No context retrieved."
            return combined_context
        except Exception as e:
            print("Error getting node text from Pageindex: ", e)
            raise e

    def get_matching_context_for_doc(self, doc_id: str, query: str):
        """ Get matching context for a document."""
        try:
            tree_result = self.get_document_tree(doc_id)
            # Build a node map for easy lookup
            node_map = utils.create_node_mapping(tree_result)
            tree_without_text = utils.remove_fields(tree_result.copy(), fields=["text"])
            search_prompt = f"""
        You are given a question and a tree structure of a document.
        Each node contains a node id, node title, and a corresponding summary.
        Your task is to find all nodes that are likely to contain the answer to the question.
        Question: {query}
        Document tree structure:
        {json.dumps(tree_without_text, indent=2)}
        Rank the nodes in order of relevance 
        Match the question to the most relevant {NUMBER_OF_NODES_FOR_QUERY_MATCH} nodes.
        Discard less relevant nodes and return only the node ids of the {NUMBER_OF_NODES_FOR_QUERY_MATCH} most relevant nodes.
        Please reply in the following JSON format:
        {{
            "node_list": ["node_id_1", "node_id_2"]
        }}
        Directly return the final JSON structure. Do not output anything else.
        Do not include any backticks or code formatting in the response.
        Your response should be only the JSON object. No backticks and no other text.
        """
            print("Asking LLM to search the tree for relevant nodes. Search Prompt ===: ", search_prompt)
            tree_search_result_text, usage = self.call_llm(search_prompt)
            print(f"\n=== LLM response ===\n{tree_search_result_text}\n=== LLM usage ===\n{usage}")
            tree_search_result = json.loads(tree_search_result_text)
            matching_nodes=tree_search_result.get("node_list")
            print("Node IDs returned:", matching_nodes)
            # Get actual node texts and combine
            combined_context_for_doc = self.get_doc_context(tree_search_result, matching_nodes, node_map)
            return combined_context_for_doc, usage

        except Exception as e:
            print("Error getting matching context for document from Pageindex: ", e)
            raise e

    def print_debug_doc(self, doc_id: str):
        tree_result = self.get_document_tree(doc_id)
        node_map = utils.create_node_mapping(tree_result)
        # utils.print_tree(node_map)
        print("Node Map: ", json.dumps(node_map))

    def get_answer_from_combined_contexts(self, combined_contexts: str, query: str, user_data: str):
        """Get answer from combined contexts."""
        try:
            prompt= SYSTEM_INSTRUCTION + "\n\
                Use this context to answer the query: \n\
                    " + "\n".join(combined_contexts) + "\n\
                        And use the following user data in JSON format to answer the query: \n\
                            " + user_data + "\n\
                                Answer the following query: \n\
                                    " + query + "\n\
                                        Perform needed calculations using the provided user data"

            print('Querying shared LLM with prompt: ' + prompt[:100])
            response, usage = call_shared_llm(prompt, self.client)
            return response, usage
        except Exception as e:
            print("Error getting answer from combined contexts from Pageindex: ", e)
            raise e 
        
    def calculate_usage(self, usage_list):
        tot_prompt_tokens = 0
        tot_candidate_tokens = 0
        tot_total_tokens = 0
        for usage in usage_list:
            tot_prompt_tokens += usage.prompt_token_count
            tot_candidate_tokens += usage.candidates_token_count
            tot_total_tokens += usage.total_token_count
        return tot_prompt_tokens, tot_candidate_tokens, tot_total_tokens

        
    def search_files(self, query: str, user_data: str):
        """Search files in the store."""
        documents = self.list_documents()
        document_names = [doc['name'] for doc in documents]
        document_ids = [doc['id'] for doc in documents]
        print(f"Document names: {document_names} ,\n Document IDs: {document_ids}")
        contexts_for_docs = []
        usage_list = []
        for doc_id in document_ids:
            # self.print_debug_doc(doc_id)
            
            retrieved_texts, usage = self.get_matching_context_for_doc(doc_id, query)
            contexts_for_docs.append(retrieved_texts)
            usage_list.append(usage)
            print("Contexts:")
            print(retrieved_texts[:500])

        combined_contexts = "\n\n".join(contexts_for_docs)
        response, usage = self.get_answer_from_combined_contexts(combined_contexts, query, user_data)
        usage_list.append(usage)
        tot_prompt_tokens, tot_candidate_tokens, tot_total_tokens = self.calculate_usage(usage_list)
        print(f"Total Prompt tokens: {tot_prompt_tokens} Total Candidates tokens: {tot_candidate_tokens} Total tokens: {tot_total_tokens}")
        return response, None, tot_prompt_tokens, tot_candidate_tokens, tot_total_tokens, usage_list
