#!/usr/bin/env python3

import os
import argparse
import re
from PIL import Image
from PIL.ExifTags import TAGS
import datetime
from typing import Optional, Dict, Any

def get_exif_data(image_path: str) -> Optional[Dict[str, Any]]:
    """
    Extracts EXIF data from an image file.

    Args:
        image_path (str): The path to the image file.

    Returns:
        dict: A dictionary containing EXIF tags and their values,
              or None if no EXIF data is found or an error occurs.
    """
    try:
        with Image.open(image_path) as img:
            exif_data = img.getexif()
            if exif_data is None:
                return None

            decoded_exif = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                decoded_exif[tag] = value
            return decoded_exif
    except Exception as e:
        print(f"Error reading EXIF data from {image_path}: {e}")
        return None

def is_already_renamed(filename: str, prefix: str) -> bool:
    """
    Check if a filename already matches the expected rename pattern.
    
    Pattern: {prefix}_{YYYYMMDD_HHMMSS}[_NN].{ext}
    Where [_NN] is an optional collision counter like _02, _03, etc.
    
    Args:
        filename (str): The filename to check
        prefix (str): The expected prefix
        
    Returns:
        bool: True if filename matches the pattern, False otherwise
    """
    # Remove extension to check the base pattern
    name_without_ext = os.path.splitext(filename)[0]
    
    # Build regex pattern: prefix_YYYYMMDD_HHMMSS or prefix_YYYYMMDD_HHMMSS_NN
    # Where NN is a 2-digit collision counter
    pattern = rf"^{re.escape(prefix)}_\d{{8}}_\d{{6}}(?:_\d{{2}})?$"
    
    return bool(re.match(pattern, name_without_ext))

def main():
    """
    Main function to handle CLI arguments and run the photo renaming process.
    """
    parser = argparse.ArgumentParser(
        description="Rename photo files based on EXIF DateTime data to format: {prefix}_YYYYMMDD_HHMMSS.{ext}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s /path/to/photos
  %(prog)s ~/Pictures/vacation --dry-run
  %(prog)s . --extensions jpg png heic
  %(prog)s /photos --prefix "vacation" --dry-run
  %(prog)s /photos --recursive --dry-run
  %(prog)s ~/Pictures -r --prefix "trip"""
    )
    
    parser.add_argument(
        "directory",
        help="Directory containing image files to rename"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming files"
    )
    
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=["png", "jpg", "jpeg", "tiff", "tif", "heic"],
        help="File extensions to process (default: png jpg jpeg tiff tif heic)"
    )
    
    parser.add_argument(
        "--prefix",
        default="photo",
        help="Prefix for renamed files (default: photo, resulting in photo_YYYYMMDD_HHMMSS.ext)"
    )
    
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively process all subdirectories"
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist.")
        return 1
    
    # Convert extensions to lowercase and add dots if missing
    extensions = tuple(f".{ext.lower().lstrip('.')}" for ext in args.extensions)
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be renamed")
        print(f"Would process files with extensions: {', '.join(extensions)}")
        if args.recursive:
            print("Would process recursively in all subdirectories")
        print()
    
    process_directory_with_options(args.directory, extensions, args.dry_run, args.prefix, args.recursive)
    return 0

def process_file_if_image(file_path, filename, extensions, dry_run, prefix):
    """
    Process a file if it's an image with a matching extension.
    
    Args:
        file_path (str): The full path to the file.
        filename (str): The filename.
        extensions (tuple): Tuple of extensions to match.
        dry_run (bool): If True, show what would be renamed without actually renaming.
        prefix (str): Prefix for renamed files.
        
    Returns:
        bool: True if file was processed, False otherwise.
    """
    if os.path.isfile(file_path) and filename.lower().endswith(extensions):
        return rename_image_with_exif_date_with_options(file_path, dry_run, prefix)
    return False

def process_directory_with_options(directory_path, extensions, dry_run=False, prefix="photo", recursive=False):
    """
    Processes all image files in a given directory to rename them with EXIF date.
    
    Args:
        directory_path (str): The path to the directory containing image files.
        extensions (tuple): Tuple of file extensions to process.
        dry_run (bool): If True, show what would be renamed without actually renaming.
        prefix (str): Prefix for renamed files.
        recursive (bool): If True, process subdirectories recursively.
    """
    if not os.path.isdir(directory_path):
        print(f"Error: Directory not found at '{directory_path}'")
        return

    print(f"Processing images in: {directory_path}")
    if recursive:
        print("Mode: Recursive (processing all subdirectories)")
    processed_count = 0
    skipped_count = 0
    
    if recursive:
        # Use os.walk for recursive directory traversal
        for root, _, files in os.walk(directory_path):
            print(f"  Scanning: {root}")
            for filename in files:
                file_path = os.path.join(root, filename)
                if process_file_if_image(file_path, filename, extensions, dry_run, prefix):
                    processed_count += 1
                else:
                    skipped_count += 1
    else:
        # Process only the specified directory (non-recursive)
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if process_file_if_image(file_path, filename, extensions, dry_run, prefix):
                processed_count += 1
            else:
                skipped_count += 1
    
    print(f"\nProcessing complete. Processed: {processed_count}, Skipped: {skipped_count}")

def rename_image_with_exif_date_with_options(image_path, dry_run=False, prefix="photo"):
    """
    Renames an image file using the format {prefix}_YYYYMMDD_HHMMSS.{ext}
    based on EXIF DateTime data. Handles naming collisions by
    appending _02, _03, etc. Skips files already in the expected format.

    Args:
        image_path (str): The full path to the image file.
        dry_run (bool): If True, show what would be renamed without actually renaming.
        prefix (str): Prefix for renamed files (default: "photo").
        
    Returns:
        bool: True if file was processed successfully, False if skipped.
    """
    if not os.path.isfile(image_path):
        print(f"Skipping: {image_path} is not a file.")
        return False

    # Get the directory and original filename
    directory, filename = os.path.split(image_path)
    name, ext = os.path.splitext(filename)
    
    # Check if file is already renamed with the expected pattern
    if is_already_renamed(filename, prefix):
        print(f"Already renamed: {filename} (skipping)")
        return False

    exif = get_exif_data(image_path)
    
    if exif and 'DateTime' in exif:
        date_time_str = exif['DateTime']
        try:
            # EXIF date format is typically "YYYY:MM:DD HH:MM:SS"
            dt_object = datetime.datetime.strptime(date_time_str, "%Y:%m:%d %H:%M:%S")
            # Format for filename: YYYYMMDD_HHMMSS
            formatted_date = dt_object.strftime("%Y%m%d_%H%M%S")

            # New naming format: {prefix}_YYYYMMDD_HHMMSS.{ext}
            base_filename = f"{prefix}_{formatted_date}{ext}"
            new_path = os.path.join(directory, base_filename)

            # Handle naming collisions by appending _02, _03, etc.
            counter = 1
            while os.path.exists(new_path):
                counter += 1
                collision_filename = f"{prefix}_{formatted_date}_{counter:02d}{ext}"
                new_path = os.path.join(directory, collision_filename)
            
            final_filename = os.path.basename(new_path)
            
            if dry_run:
                print(f"Would rename: {filename} -> {final_filename}")
            else:
                os.rename(image_path, new_path)
                print(f"Renamed: {filename} -> {final_filename}")
            return True

        except ValueError:
            print(f"Could not parse EXIF date '{date_time_str}' for {filename}. Skipping.")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while renaming {filename}: {e}")
            return False
    else:
        print(f"No 'DateTime' EXIF data found for {filename}. Skipping.")
        if exif:
            print(f"Exif data in {filename}: {exif}")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(main())
