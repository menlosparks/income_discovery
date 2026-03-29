import os
from dotenv import load_dotenv
from filesearcher import FileSearcher


# Load environment variables
load_dotenv()

INPUT_DIR = r"C:\Users\abhi2\source\inc_disc\storage\irs-files"

def get_all_files(input_dir):
    """Returns a list of all files in the given directory."""
    if not os.path.exists(input_dir):
        return []
    
    file_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

if __name__ == "__main__":
    files_list = get_all_files(INPUT_DIR)
    searcher = FileSearcher(files_list)
    file_search_store = searcher.upload_files()
    response = searcher.search_files("At what age do RMDs need to be taken?")
    print(' REsponse text is ----> ', response.text , ' <---- End of response text')
