import csv
from pathlib import Path
from datetime import datetime

def main():
    # 1. Base inputs
    line_no = "3-1"
    sign = "(-)"
    model = "JF2"
    date_str = "20251207"

    
    # 2. Souce and destination folders
    src_dir = Path(r"D:\Files\Data\Result\Day")
    dst_dir = Path(r"D:\Files\Data\Result\Output")

    print("Line:", line_no)
    print("Sign:", sign)
    print("Model:", model)
    print("Date:", date_str)
    print("Source folder:", src_dir)
    print("Destination folder", dst_dir)

if __name__ == "__main__":
    main()