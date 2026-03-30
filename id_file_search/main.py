import os
from dotenv import load_dotenv
from filesearcher import FileSearcher
from claude_filesearcher import ClaudeFileSearcher

# Load environment variables
load_dotenv()

INPUT_DIR = r"../storage/irs-files"
EXPLAIN_QUERY='Explain how RMD value is calculated'

def get_all_files(input_dir):
    """Returns a list of all files in the given directory."""
    if not os.path.exists(input_dir):
        return []
    
    file_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

def show_response(response):
    print('\n\n***************\n\n', response.text, '\n\n***************\n\n')

if __name__ == "__main__":
    files_list = get_all_files(INPUT_DIR)
    # searcher = FileSearcher(files_list)
    searcher = ClaudeFileSearcher(files_list)
    file_search_store = searcher.upload_files()

    response = searcher.search_files(EXPLAIN_QUERY)
    show_response(response)
    
    print("\nAsk questions about your files (type 'exit' or 'quit' to stop):")
    while True:
        query = input("\nEnter  your Query: ")
        if query.lower() in ["exit", "quit", ""] or query == "":
            break
        
        response = searcher.search_files(query)
        show_response(response)


