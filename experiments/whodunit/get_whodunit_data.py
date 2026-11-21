"""
Step 1: Download replication package from Zenodo record 18834715 (_01_datasets.zip)
and extract into data/whodunit/.
Verify archive contents and schema of final_dataset.json.
"""

import os
import sys
import time
import zipfile
import json
import urllib.request
import shutil

DOWNLOAD_URL = "https://zenodo.org/records/18834715/files/_01_datasets.zip?download=1"
OUTPUT_DIR = os.path.join("data", "whodunit")
TEMP_ZIP = os.path.join("data", "_temp_01_datasets.zip")

def main():
    start_time = time.time()
    print("=" * 60)
    print("STEP 1: GETTING WHODUNIT DATASET")
    print("=" * 60)

    os.makedirs("data", exist_ok=True)
    if os.path.exists(OUTPUT_DIR):
        print(f"Directory {OUTPUT_DIR} already exists.")
    else:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Download
    if not os.path.exists(TEMP_ZIP):
        print(f"Downloading {DOWNLOAD_URL} to {TEMP_ZIP}...")
        req = urllib.request.Request(
            DOWNLOAD_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        dl_start = time.time()
        with urllib.request.urlopen(req) as response, open(TEMP_ZIP, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        dl_duration = time.time() - dl_start
        file_size_mb = os.path.getsize(TEMP_ZIP) / (1024 * 1024)
        print(f"Download complete: {file_size_mb:.2f} MB in {dl_duration:.2f}s")
    else:
        file_size_mb = os.path.getsize(TEMP_ZIP) / (1024 * 1024)
        print(f"Found existing zip at {TEMP_ZIP} ({file_size_mb:.2f} MB)")

    # 2. List archive contents
    print("\nInspecting zip archive contents:")
    with zipfile.ZipFile(TEMP_ZIP, "r") as zf:
        infolist = zf.infolist()
        print(f"Total entries in archive: {len(infolist)}")
        for info in infolist[:25]:
            print(f"  - {info.filename} ({info.file_size} bytes)")
        if len(infolist) > 25:
            print(f"  ... and {len(infolist) - 25} more files.")

        # 3. Extract into data/whodunit/
        print(f"\nExtracting archive into {OUTPUT_DIR}...")
        zf.extractall(OUTPUT_DIR)
        print("Extraction complete.")

    # Remove temporary zip file so only data/whodunit remains
    if os.path.exists(TEMP_ZIP):
        os.remove(TEMP_ZIP)
        print(f"Removed temporary zip: {TEMP_ZIP}")

    # 4. List extracted files in data/whodunit/
    print(f"\nListing extracted directory contents in {OUTPUT_DIR}:")
    extracted_files = []
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), OUTPUT_DIR)
            extracted_files.append((rel, os.path.getsize(os.path.join(root, f))))
            print(f"  - {rel} ({os.path.getsize(os.path.join(root, f))} bytes)")

    # 5. Look for final_dataset.json
    target_filename = None
    for rel, sz in extracted_files:
        if os.path.basename(rel) == "final_dataset.json":
            target_filename = os.path.join(OUTPUT_DIR, rel)
            break

    if not target_filename:
        # Search for any json
        json_candidates = [os.path.join(OUTPUT_DIR, rel) for rel, sz in extracted_files if rel.endswith(".json")]
        print(f"\nTarget final_dataset.json not found directly. JSON candidates: {json_candidates}")
        if len(json_candidates) == 1:
            target_filename = json_candidates[0]
        else:
            print("ERROR: Cannot identify target JSON file!")
            sys.exit(1)

    print(f"\nVerifying dataset file: {target_filename}")
    load_start = time.time()
    with open(target_filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded JSON in {time.time() - load_start:.2f}s")

    # Verify structure
    print(f"Top-level data type: {type(data)}")
    if isinstance(data, dict):
        print(f"Number of keys: {len(data)}")
        first_key = next(iter(data))
        print(f"First key: {first_key}")
        first_val = data[first_key]
        print(f"Type of value for first key: {type(first_val)}")
        if isinstance(first_val, dict):
            print(f"Keys in first item: {list(first_val.keys())}")
            if "human_solutions" in first_val:
                print(f"human_solutions count: {len(first_val['human_solutions'])}")
                if len(first_val['human_solutions']) > 0:
                    sample_sol = first_val['human_solutions'][0]
                    print(f"Type of human_solutions item: {type(sample_sol)}")
                    if isinstance(sample_sol, dict):
                        print(f"Keys in human solution: {list(sample_sol.keys())}")
            if "ai_solutions" in first_val:
                print(f"ai_solutions count: {len(first_val['ai_solutions'])}")
                if len(first_val['ai_solutions']) > 0:
                    sample_sol = first_val['ai_solutions'][0]
                    print(f"Type of ai_solutions item: {type(sample_sol)}")
                    if isinstance(sample_sol, dict):
                        print(f"Keys in ai solution: {list(sample_sol.keys())}")
    elif isinstance(data, list):
        print(f"Length of list: {len(data)}")
        if len(data) > 0:
            first_item = data[0]
            print(f"First item type: {type(first_item)}")
            if isinstance(first_item, dict):
                print(f"Keys in first item: {list(first_item.keys())}")

    elapsed = time.time() - start_time
    print(f"\nSTEP 1 wall-clock runtime: {elapsed:.2f}s")

if __name__ == "__main__":
    main()
