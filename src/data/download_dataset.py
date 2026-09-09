import os
import urllib.request
import sys
from pathlib import Path

# Add project root to path so we can import configs
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from configs.config import TRAIN_DATA_URL, TEST_DATA_URL, RAW_DATA_DIR

def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download {url}. Error: {e}")

def main():
    if not RAW_DATA_DIR.exists():
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    train_dest = RAW_DATA_DIR / 'KDDTrain+.txt'
    test_dest = RAW_DATA_DIR / 'KDDTest+.txt'
    
    if not train_dest.exists():
        download_file(TRAIN_DATA_URL, train_dest)
    else:
        print(f"{train_dest} already exists.")
        
    if not test_dest.exists():
        download_file(TEST_DATA_URL, test_dest)
    else:
        print(f"{test_dest} already exists.")

if __name__ == "__main__":
    main()
