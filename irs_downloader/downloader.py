import os
import requests
from typing import List

class IRSDownloader:
    """
    A class to download files from IRS URLs and save them to a specified directory.
    """

    def __init__(self, storage_dir: str):
        """
        Initialize the downloader with a target storage directory.
        """
        self.storage_dir = storage_dir
        # Ensure target directory exists
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def _get_filename_from_url(self, url: str) -> str:
        """
        Extract a filename from the URL.
        """
        # Get the last part of the URL as the filename
        filename = url.rstrip('/').split('/')[-1]
        # Add .html if no extension is present (likely a page)
        if '.' not in filename:
            filename += '.html'
        return filename

    def download(self, url: str) -> str:
        """
        Download a single URL and save it to the storage directory.
        Returns the path to the saved file.
        """
        print(f"Downloading from: {url}")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            filename = self._get_filename_from_url(url)
            save_path = os.path.join(self.storage_dir, filename)

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Saved to: {save_path}")
            return save_path

        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        return None

    def download_multiple(self, urls: List[str]) -> List[str]:
        """
        Download multiple URLs.
        """
        saved_paths = []
        for url in urls:
            path = self.download(url)
            if path:
                saved_paths.append(path)
        return saved_paths

if __name__ == "__main__":
    # Test block
    STORAGE_DIR = r"C:\Users\abhi2\source\inc_disc\storage\irs-files"
    downloader = IRSDownloader(STORAGE_DIR)
    
    test_urls = [
        "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-required-minimum-distributions-rmds",
        "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-beneficiary"
    ]
    
    downloader.download_multiple(test_urls)
