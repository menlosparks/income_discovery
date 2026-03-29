from downloader import IRSDownloader

def main():
    # Define storage directory
    STORAGE_DIR = r"C:\Users\abhi2\source\inc_disc\storage\irs-files"
    
    # Initialize the downloader
    downloader = IRSDownloader(STORAGE_DIR)
    
    # Example URLs provided by user
    urls = [
        "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-required-minimum-distributions-rmds",
        "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-beneficiary"
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
    main()
