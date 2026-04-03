import os
import re
import json
from google import genai
from google.genai import types
import time
from pydantic import BaseModel
from pinecone import Pinecone, ServerlessSpec


MODEL_ID = "google/gemma-3-4b-it"
EMBEDDING_MODEL_ID="gemini-embedding-2-preview"
INDEX_NAME = "gemini-embedding-2-preview-income-discovery"

class PconSearch:
    """
    """
    SYSTEM_INSTRUCTION = """
    You are a helpful financial advisor. Give concise answers to the user's questions. Limit
    the answers to 3 or 4 sentences. If the answer is not in the documents, say so. 
    You have access to the user_data to retrieve information about the user's 
    spouse, income, and account balances. Use it whenever a question requires specific user data.
    Be very sure of your calculations and provide the answer in a clear and concise manner. 
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
        self.pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        self.index = None
        self.client = genai.Client()


    def get_embeddings(self, documents: list[str]):
        """ Get the embedding for a given text."""
        result = self.client.models.embed_content(
            model=EMBEDDING_MODEL_ID,
            contents=documents
        )
        # for embedding in result.embeddings:
        #     # Print just a part of the embedding to keep the output manageable
        #     print(str(embedding)[:50], '... TRIMMED]')

        dimension = len(result.embeddings[0].values)  # Gemma-3-27b hidden size

        # print('embeddings ' + str(result.embeddings))
        # print('embeddings[0] ' + str(result.embeddings[0]))
        print('embeddings result.size ' + str(len(result.embeddings)))
        print('embeddings[0].size ' + str(len(result.embeddings[0].values)))
        print('embeddings[1].size ' + str(len(result.embeddings[1].values)))
        return result.embeddings

    def get_or_create_pinecone_index(self, documents, force_recreate=False):
        """ Create a pinecone index."""
        index_name = INDEX_NAME
        embeddings = None
        if index_name  in self.pc.list_indexes().names():
            index = self.pc.Index(index_name)
            # 3. Fetch index statistics
            stats = index.describe_index_stats()

            # 4. Check the vector count
            vector_count = stats['total_vector_count']
            print(f'Index exists and here are {vector_count} vectors in the Index ')

            if vector_count > 0 and force_recreate:
                print('Force recreate is true. Deleting existing index')
                # Clear all records in the default namespace
                index.delete(delete_all=True)
                print('Index was deleted. Embeddings will be recreated.')
                embeddings = self.get_embeddings(documents)
                dimension = len(embeddings[0].values)  # Gemma-3-27b hidden size
            elif vector_count <= 0:
                print('No vectors were in DB. Recreating embeddings .')
                embeddings = self.get_embeddings(documents)
                dimension = len(embeddings[0].values)  # Gemma-3-27b hidden size

        else:            ## index_name not in self.pc.list_indexes().names():
            embeddings = self.get_embeddings(documents)
            dimension = len(embeddings[0].values)  # Gemma-3-27b hidden size
            print('Create new index of dim ' + str(dimension))
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine", # Recommended for LLM embeddings
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        index = self.pc.Index(index_name)
        print('Index  name ' + str(index) + ' with '+ str(index.describe_index_stats()['total_vector_count']) + ' vectors')
        return index, str(index.describe_index_stats()['total_vector_count']), embeddings


    def upsert_embeddings(self, embeddings, index, documents):
        """ Upsert embeddings to pinecone index."""
        # index_name = INDEX_NAME
        # index = self.pc.Index(index_name)
        # index.upsert(vectors=embeddings)

        embeddings = [embedding.values for embedding in  embeddings]
        # print('embeddings ' + str(embeddings))
        ids = [str(i) for i in range(len(documents))]

        print('Upserting ' + str(len(embeddings)) + ' vectors to pinecone index ' + str(index))
        vectors_to_upsert = [
            (ids[i], embeddings[i], {"text": documents[i]})
            for i in range(len(documents))
        ]
        index.upsert(vectors=vectors_to_upsert)
        print('Upserted ' + str(len(embeddings)) + ' vectors to pinecone index ')
        print(f'After upserthere are { index.describe_index_stats()['total_vector_count']} vectors in the Index ')

    def get_documents(self, files_list: list[str]):
        """ Read the contents of each file in files_list and return a list of documents"""
        documents = []
        print(f"Reading {len(files_list)} files")
        for file_path in files_list:
            file_text = None
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_text = f.read()
            documents.append(file_text)
        return documents

    def upload_files(self, files_list: list[str], force_reindex=False):
        """ Read the contents of each file in files_list and upload to pinecone"""
        print(f"Uploading {len(files_list)} files to pinecone...")
        documents = self.get_documents(files_list)
        print(f"Read {len(documents)} documents from {len(files_list)} files.")
        # embeddings = self.get_embeddings(documents)
        # print(f"Read {len(embeddings)} embeddings from {len(documents)} documents.")
        index, vector_count, embeddings = self.get_or_create_pinecone_index(documents, force_reindex)
        self.index = index
        # if int(vector_count) == int(len(embeddings)):
        #     print(f'Index already has {vector_count} vectors. Skipping upsert.')
        #     return index
        # else :
        #     print(f'Vectors {vector_count} are not equal to embeddings {len(embeddings)}: {(vector_count == len(embeddings))}')
        if ( embeddings is not None):
            print(f"Index has {vector_count} vectors and we have {len(embeddings)} embeddings to upsert.")
            self.upsert_embeddings(embeddings, index, documents)
        else:
            print(f'Embeddings were not created. Index already has {vector_count} vectors. Skipping upsert.')

        # for file_path in files_list:
        #     print(f"Reading file: {file_path}")
        #     file_text = None
        #     with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        #         file_text = f.read()
        #     documents.append(file_text)
            # embedding = self.get_embedding(file_text)
        #     documents.append({
        #         "id": os.path.basename(file_path),
        #         "values": embedding,
        #         "metadata": {
        #             "source": file_path
        #         }
        #     })
        
        # print(f"Read {len(files_list)} files into pinecone.")
        # pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        # index = pc.Index("income-discovery")
        # index.upsert(vectors=documents)
        return documents

        
    def retrieve_matching_documents(self,  query: str):
        """Retrieve matching documents from the store."""
        result = self.client.models.embed_content(
            model=EMBEDDING_MODEL_ID,
            contents=query)
        # query_vector = model.encode([query_text]).tolist()[0]
        query_vector = result.embeddings[0].values
        results = self.index.query(
            vector=query_vector,
            top_k=1,
            include_metadata=True
        )

        # Output Results
        print(f"Query to find matching documents: {query}")
        # for match in results['matches']:
        #     print(f"Retrieved: {match['metadata']['text']}")
        matching_docs = []
        for match in results['matches']:
            print(f"Score: {match['score']}")
            matching_docs.append(match['metadata']['text'])
        return matching_docs
        
    def search_files(self, query: str, user_data: str):
        """Search files in the store."""
        matching_docs = self.retrieve_matching_documents(query)
        print('matching_docs ' + str(matching_docs)[:400])

        # user_data=self.get_dummy_user_data(client_id)
        prompt= self.SYSTEM_INSTRUCTION + "\n\
            Use this context to answer the query: \n\
                " + "\n".join(matching_docs) + "\n\
                    And use the following user data in JSON format to answer the query: \n\
                        " + user_data + "\n\
                            Answer the following query: \n\
                                " + query + "\n\
                                    Perform needed calculations using the provided user data"

        print('Querying LLM with prompt: ' + prompt[:100])
        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=prompt);
        return response
