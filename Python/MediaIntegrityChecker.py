import os
import shutil
import sys
import subprocess

# --- DYNAMIC CONFIGURATION ---
print("--- ⚡ ALL-FORMAT HIGH-SPEED MEDIA SCANNER ---")
TARGET_DIR = input("Please enter or paste the absolute folder path to scan: ").strip()
print("----------------------------------------------\n")

if not os.path.exists(TARGET_DIR):
    print(f"❌ Error: The path '{TARGET_DIR}' does not exist.")
    sys.exit(1)

# Establish destination directory path for broken assets
CORRUPT_DIR = os.path.join(TARGET_DIR, "CORRUPT_FILES")
LOG_FILE = os.path.join(TARGET_DIR, "corrupt_files_report.txt")
# ------------------------------

def check_video_fast(file_path):
    """Fast check: Inspects container metadata headers without decoding video frames."""
    cmd = [
        'ffprobe', '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=4)
        if result.returncode != 0 or result.stderr:
            err = result.stderr.decode('utf-8', errors='ignore').strip()
            return False, err if err else "Invalid metadata/container header structure"
        return True, ""
    except subprocess.TimeoutExpired:
        return True, "" # Huge valid videos can trigger timeouts during header seeks
    except Exception as e:
        return False, str(e)

def check_image_fast(file_path):
    """Fast check: Validates structural image format integrity boundaries."""
    cmd = ['identify', '-ping', file_path]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            err = result.stderr.decode('utf-8', errors='ignore').strip()
            return False, err if err else "Corrupt image format header"
        return True, ""
    except Exception as e:
        return False, str(e)

def main():
    # Comprehensive dictionary grouping of all common photo, video, and raw camera extensions
    video_exts = {
        '.mp4', '.mov', '.mkv', '.avi', '.mpg', '.mpeg', '.3gp', '.webm', 
        '.m2ts', '.mts', '.flv', '.wmv', '.vob', '.ogv', '.m4v'
    }
    image_exts = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif', '.bmp', 
        '.tiff', '.tif', '.svg', '.ico', '.psd', '.avif',
        '.cr2', '.cr3', '.nef', '.arw', '.dng', '.orf', '.rw2', '.pef', '.raf'
    }
    
    os.makedirs(CORRUPT_DIR, exist_ok=True)
    
    print(f"🚀 Initializing high-speed integrity parsing inside: {TARGET_DIR}")
    print(f"📁 Corrupt items will be quarantined to: {CORRUPT_DIR}\n")
    
    valid_count = 0
    corrupt_count = 0
    total_count = 0
    
    with open(LOG_FILE, "w") as log:
        log.write("=== ⚠️ AUTOMATED QUARANTINE CORRUPTED FILES REPORT ===\n\n")
        
        for root, _, files in os.walk(TARGET_DIR):
            if '\x00' in root or "CORRUPT_FILES" in root:
                continue
                
            for file in files:
                if file.startswith('.') or '\x00' in file or file == "corrupt_files_report.txt" or file == "verify_media.py":
                    continue
                    
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file.lower())
                
                if ext not in video_exts and ext not in image_exts:
                    continue
                
                total_count += 1
                is_valid = True
                error_msg = ""
                
                if ext in video_exts:
                    is_valid, error_msg = check_video_fast(file_path)
                elif ext in image_exts:
                    is_valid, error_msg = check_image_fast(file_path)
                
                if is_valid:
                    valid_count += 1
                else:
                    corrupt_count += 1
                    clean_msg = str(error_msg).replace("\n", " ")[:60]
                    log_entry = f"❌ CORRUPT: {file_path} | {clean_msg}\n"
                    log.write(log_entry)
                    
                    # Safely move the file to CORRUPT_FILES folder
                    dest_path = os.path.join(CORRUPT_DIR, file)
                    base, extension = os.path.splitext(file)
                    counter = 1
                    
                    # Handle name collisions in the quarantine folder
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(CORRUPT_DIR, f"{base}_corrupt_{counter}{extension}")
                        counter += 1
                        
                    try:
                        shutil.move(file_path, dest_path)
                    except Exception as e:
                        log.write(f"  └─ Failed to move file: {str(e)}\n")
                
                if total_count % 50 == 0:
                    sys.stdout.write(f"🔄 Processing: Checked {total_count:,} | Healthy: {valid_count:,} | Corrupt: {corrupt_count:,}\r")
                    sys.stdout.flush()

    # Final screen display
    sys.stdout.write("\033[H\033[J") # Smooth screen clear
    print("==================================================")
    print("      🏁 MEDIA INTEGRITY SCAN COMPLETE 🏁        ")
    print("==================================================")
    print(f"  📊 Total Files Evaluated:    {total_count:,}")
    print(f"  🟢 Healthy/Valid Media:       {valid_count:,}")
    print(f"  🔴 Corrupted & Moved:        {corrupt_count:,}")
    print("==================================================")
    print(f"📍 Quarantine folder: {CORRUPT_DIR}")
    print(f"📄 Detailed text log saved to: {LOG_FILE}\n")

if __name__ == "__main__":
    main()
