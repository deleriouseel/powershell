#!/bin/bash

# To use: ./shellzipSingle.sh <bookname>

# Check if book name is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <bookname>"
    echo "Example: $0 mybook"
    exit 1
fi

# Configuration
MEDIA_FOLDER="/home1/northdi7/public_html/media"
MAX_FILES_PER_ZIP=30
TEMP_DIR="$MEDIA_FOLDER/temp_zip_parts"
LOG_FILE="$MEDIA_FOLDER/zip_log.txt"
LOCK_FILE="/tmp/book_zip.lock"
BOOKNAME="$1"

# Error handling
set -euo pipefail

# Logging function
log_message() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" >> "$LOG_FILE"
    # Also print to console for testing
    echo "[$timestamp] $1"
}

# Cleanup function
cleanup() {
    rm -rf "$TEMP_DIR"/*
    rm -f "$LOCK_FILE"
    log_message "Cleanup completed"
}

# Check if script is already running
if [ -f "$LOCK_FILE" ]; then
    echo "Another instance is running. Exiting."
    exit 1
fi

# Create lock file
touch "$LOCK_FILE"

# Ensure cleanup happens on script exit
trap cleanup EXIT ERR

# Create temporary directory if it doesn't exist
mkdir -p "$TEMP_DIR"

log_message "Starting to process: $BOOKNAME"

# Handle existing zip file - move to temporary backup
if [ -f "$MEDIA_FOLDER/$BOOKNAME.zip" ]; then
    mv "$MEDIA_FOLDER/$BOOKNAME.zip" "$MEDIA_FOLDER/$BOOKNAME.zip.bak"
    log_message "Created temporary backup of existing zip"
fi

# Get list of files and count
mapfile -t files < <(find "$MEDIA_FOLDER/rafiles" -maxdepth 1 -type f -name "$BOOKNAME*" | sort)
total_files=${#files[@]}

if [ $total_files -eq 0 ]; then
    log_message "Error: No files found for $BOOKNAME"
    # Restore backup if no files found
    if [ -f "$MEDIA_FOLDER/$BOOKNAME.zip.bak" ]; then
        mv "$MEDIA_FOLDER/$BOOKNAME.zip.bak" "$MEDIA_FOLDER/$BOOKNAME.zip"
        log_message "Restored backup zip due to no files found"
    fi
    exit 1
fi

log_message "Found $total_files files"

# Process based on file count
success=false
if [ $total_files -gt $MAX_FILES_PER_ZIP ]; then
    log_message "Creating split zip files"
    
    # Calculate parts needed
    num_parts=$(( (total_files + MAX_FILES_PER_ZIP - 1) / MAX_FILES_PER_ZIP ))
    
    # Create zip parts
    for ((i=0; i<num_parts; i++)); do
        start_idx=$((i * MAX_FILES_PER_ZIP))
        end_idx=$(( start_idx + MAX_FILES_PER_ZIP ))
        
        if [ $end_idx -gt $total_files ]; then
            end_idx=$total_files
        fi
        
        part_files=("${files[@]:start_idx:MAX_FILES_PER_ZIP}")
        
        if ! zip -q -FS "$TEMP_DIR/${BOOKNAME}_part$((i+1)).zip" "${part_files[@]}"; then
            log_message "Error creating part $((i+1))"
            break
        fi
        log_message "Created part $((i+1)) of $num_parts"
    done
    
    # Create final zip
    cd "$TEMP_DIR" || exit 1
    if zip -q -FS "$MEDIA_FOLDER/$BOOKNAME.zip" "${BOOKNAME}_part"*; then
        success=true
        log_message "Created final combined zip"
    fi
    cd - || exit 1
    
else
    # Create single zip for smaller books
    if zip -q -FS "$MEDIA_FOLDER/$BOOKNAME.zip" "${files[@]}"; then
        success=true
        log_message "Created single zip file"
    fi
fi

# Verify the new zip file
if [ "$success" = true ] && zipinfo -1 "$MEDIA_FOLDER/$BOOKNAME.zip" > /dev/null 2>&1; then
    zip_size=$(du -h "$MEDIA_FOLDER/$BOOKNAME.zip" | cut -f1)
    log_message "Successfully created $BOOKNAME.zip (Size: $zip_size)"
    # Remove backup if new zip is valid
    rm -f "$MEDIA_FOLDER/$BOOKNAME.zip.bak"
else
    log_message "Error: New zip file creation or verification failed"
    # Restore backup if new zip failed
    if [ -f "$MEDIA_FOLDER/$BOOKNAME.zip.bak" ]; then
        mv "$MEDIA_FOLDER/$BOOKNAME.zip.bak" "$MEDIA_FOLDER/$BOOKNAME.zip"
        log_message "Restored backup zip due to creation failure"
    fi
    exit 1
fi

log_message "Completed processing $BOOKNAME"
echo "----------------------------------------" >> "$LOG_FILE"

exit 0