import os
import time
import sys
import argparse
from dotenv import load_dotenv
from filesearcher import FileSearcher
from claude_filesearcher import ClaudeFileSearcher
from user_data import UserData
from pconsearch import PconSearch
from pageindexsearch import PageIndexSearch

# Load environment variables
load_dotenv()

## updated for git
INPUT_DIR = r"../storage/irs-files"
INPUT_DIR_CHUNK = r"../storage/irs-files-chunk"
INPUT_DIR_PDF = r"../storage/irs-pdfs/trial"
SAMPLE_QUERY='Explain how RMD value is calculated for the user'

INPUT_DIR_PDF_NO590A='../storage/irs-no-p590a/pdf'
INPUT_DIR_HTML_CHUNKS_NO590A='../storage/irs-no-p590a/html-chunks'

INPUT_DIR_FILESEARCH=INPUT_DIR_PDF_NO590A
INPUT_DIR_PCONSEARCH=INPUT_DIR_HTML_CHUNKS_NO590A
INPUT_DIR_PAGEINDEXSEARCH=INPUT_DIR_PDF_NO590A

def get_all_files(input_dir):
    """Returns a list of all files in the given directory."""
    if not os.path.exists(input_dir):
        print("Directory does not exist: ", input_dir)
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
    print('\n\n***************\n\n',str(response), '\n\n***************\n\n')

def save_response(response, filename, query, sources_used = None, tot_prompt_tokens = None, tot_candidate_tokens = None, tot_total_tokens = None, usage_list = None):


    prompt_tokens = tot_prompt_tokens if tot_prompt_tokens else response.usage.prompt_token_count
    candidate_tokens = tot_candidate_tokens if tot_candidate_tokens else response.usage.candidates_token_count
    total_tokens = tot_total_tokens if tot_total_tokens else response.usage.total_token_count

    with open(filename, "a") as f:
        f.write("\n\n***************\n\n Query:\n " + query + "\n\n")
        if usage_list and len(usage_list) > 1:
            for usage in usage_list[:-1]:
                f.write(f"Matching pre-query Tokens: Prompt={usage.prompt_token_count}, Candidates={usage.candidates_token_count}, Thoughts={usage.thoughts_token_count},Total={usage.total_token_count}\n")

        if response:
            f.write(f"Final Tokens: Prompt={prompt_tokens}, Candidates={candidate_tokens}, Total={total_tokens}\n")
        if sources_used:
            f.write("\n\n Sources Used: \n" + str(sources_used))
        
        
        f.write("\n\n Response: \n")
        if response:
            f.write(response.text)
        f.flush()
        print ('Flushed to file ', filename)

def get_faq_questions():
    with open("faq_questions.txt", "r") as f:
        return f.read().splitlines()

# Use with  python main.py --pinecone=False  --client_id=client_2
# Use with pinecone  python main.py --pinecone=True  --client_id=client_2
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client_id", type=str, default="none", help="ID of the client")
    parser.add_argument("--pinecone", type=bool, default=False, help="Use pinecone")
    parser.add_argument("--pageindex", type=bool, default=False, help="Use pageindex")
    parser.add_argument("--force_reindex", type=bool, default=False, help="Force reindex")
    parser.add_argument("--use_faq", type=bool, default=False, help="Use faq questions")
    parser.add_argument("--save_response_file", type=str, default="faq_results.txt", help="Save response to file")
    parser.add_argument("--search_only", type=bool, default=False, help="Search only")
    args = parser.parse_args()
    
    client_id = args.client_id
    use_pinecone = args.pinecone
    use_pageindex = args.pageindex
    force_reindex = args.force_reindex
    use_faq = args.use_faq
    save_response_file = args.save_response_file
    search_only = args.search_only
    print("use_pinecone:", use_pinecone)
    print("use_pageindex:", use_pageindex)
    print("force_reindex:", force_reindex)
    print("search_only:", search_only)
    print("use_faq:", use_faq)
    print("save_response_file:", save_response_file)
    print("client_id:", client_id)

    match (use_pinecone, use_pageindex):
        case (True, True):
            print("Both pinecone and pageindex are enabled. Please enable only one.")
            sys.exit(0)
        case (True, False):
            searcher = PconSearch()
            files_list = get_all_files(INPUT_DIR_PCONSEARCH)
        case (False, True):
            searcher = PageIndexSearch()
            print("Using pageindex to read from directory: ", INPUT_DIR_PDF, " for pdf files")
            files_list = get_all_files(INPUT_DIR_PAGEINDEXSEARCH)
        case (False, False):
            searcher = FileSearcher()
            files_list = get_all_files(INPUT_DIR_FILESEARCH)

    user_data = UserData()

    if not search_only:
        file_search_store = searcher.upload_files(files_list, force_reindex)

    if client_id == "none":
        print("No client ID provided. Skipping search.")
        sys.exit(0)
    else:
        user_data_str = user_data.get_user_data(client_id)

    response, sources_used, tot_prompt_tokens, tot_candidate_tokens, tot_total_tokens, usage_list = searcher.search_files(SAMPLE_QUERY, user_data_str)
    if usage_list and len(usage_list) > 1:
        for usage in usage_list[:-1]:
            print(f"Matching pre-query Tokens: Prompt={usage.prompt_token_count}, Candidates={usage.candidates_token_count}, Thoughts={usage.thoughts_token_count},Total={usage.total_token_count}\n")


    show_response(response if response else "No response from searcher")
    

    if use_faq:
        faq_questions = get_faq_questions()
        for faq_question in faq_questions:
            print("\n\nQuerying from FAQ: ", faq_question)
            response, sources_used, tot_prompt_tokens, tot_candidate_tokens, tot_total_tokens, usage_list = searcher.search_files(faq_question, user_data.get_user_data(client_id))
            show_response(response)
            save_response(response, save_response_file, faq_question, sources_used, tot_prompt_tokens, tot_candidate_tokens, tot_total_tokens, usage_list)
            time.sleep(15)

    else:
        print("\nAsk questions about your files (type 'exit' or 'quit' to stop):")
        while True:
            query = input("\nEnter  your Query: ")
            if query.lower() in ["exit", "quit", ""] or query == "":
                break
        
        response, sources_used, tot_prompt_tokens, tot_candidate_tokens, tot_total_tokens, usage_list = searcher.search_files(query, user_data.get_user_data(client_id))
        show_response(response)


