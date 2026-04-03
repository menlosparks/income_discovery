import os
import sys
import argparse
from dotenv import load_dotenv
from filesearcher import FileSearcher
from claude_filesearcher import ClaudeFileSearcher
from user_data import UserData
from pconsearch import PconSearch

# Load environment variables
load_dotenv()

## updated for git
INPUT_DIR = r"../storage/irs-files"
INPUT_DIR_CHUNK = r"../storage/irs-files-chunk"
EXPLAIN_QUERY='Explain how RMD value is calculated for the user'

def get_all_files(input_dir):
    """Returns a list of all files in the given directory."""
    if not os.path.exists(input_dir):
        return []
    
    file_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            file_list.append(os.path.join(root, file))
    print(f"Found {len(file_list)} files in the directory {input_dir}.")
    for file in file_list[:5]:
        print(file)
    return file_list

def show_response(response):
    print('\n\n***************\n\n', response.text, '\n\n***************\n\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client_id", type=str, default="none", help="ID of the client")
    parser.add_argument("--pinecone", type=bool, default=False, help="Use pinecone")
    parser.add_argument("--force_reindex", type=bool, default=False, help="Force reindex")
    args = parser.parse_args()
    
    client_id = args.client_id
    use_pinecone = args.pinecone
    force_reindex = args.force_reindex
    print("use_pinecone", use_pinecone)
    
    files_list = get_all_files(INPUT_DIR_CHUNK) if use_pinecone else get_all_files(INPUT_DIR)
    searcher = PconSearch() if use_pinecone else FileSearcher()
    user_data = UserData()

    file_search_store = searcher.upload_files(files_list, force_reindex)

    if client_id == "none":
        print("No client ID provided. Skipping search.")
        sys.exit(0)
    else:
        user_data_str = user_data.get_user_data(client_id)

    response = searcher.search_files(EXPLAIN_QUERY, user_data_str)
    show_response(response)
    
    print("\nAsk questions about your files (type 'exit' or 'quit' to stop):")
    while True:
        query = input("\nEnter  your Query: ")
        if query.lower() in ["exit", "quit", ""] or query == "":
            break
        
        response = searcher.search_files(query, user_data.get_user_data(client_id))
        show_response(response)


