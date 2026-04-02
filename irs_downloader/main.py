from downloader import IRSDownloader
from chunker import Chunker
import argparse

## Down loads files from IRS
def main(chunk=False):
    # Define storage directory
    STORAGE_DIR = r"../storage/irs-files"
    STORAGE_DIR_CHUNK = r"../storage/irs-files-chunk"

    # Initialize the downloader
    downloader = None
    if ( not chunk):
        downloader = IRSDownloader(STORAGE_DIR)
    else:
        downloader = Chunker(STORAGE_DIR_CHUNK)
    
    # Example URLs provided by user
    urls = [
        "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-required-minimum-distributions-rmds",
        "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-beneficiary",
        "https://www.irs.gov/publications/p590b",
        "https://www.irs.gov/retirement-plans/retirement-plan-and-ira-required-minimum-distributions-faqs",
        "https://www.irs.gov/retirement-plans/rmd-comparison-chart-iras-vs-defined-contribution-plans",
        "https://www.irs.gov/publications/p560",
        "https://www.irs.gov/publications/p590a",
        "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-ira-contribution-limits",
    ]
    
    # Download files
    print("Starting IRS file downloads...")
    saved_paths = downloader.download_multiple(urls)
    
    if saved_paths:
        print("\nSuccess! Files saved at:")
        for path in saved_paths:
            print(f"- {path}")
    else:
        print("\nNo files downloaded.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk", type=bool, default=False, help="Chunk number")
    args = parser.parse_args()
    
    chunk = args.chunk
    print(f'Chunking is {chunk}')
    main(chunk)
