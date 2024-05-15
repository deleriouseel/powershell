#!/bin/bash

# Path to the media folder
MEDIA_FOLDER="/home1/northdi7/public_html/media"

# Loop through names.txt
while IFS= read -r bookname || [ -n "$bookname" ];
do
    #Delete old zip folder
    rm "$MEDIA_FOLDER/$bookname.zip"

    # Append newest file to zip
    zip -FS "$MEDIA_FOLDER/$bookname.zip" "$MEDIA_FOLDER/rafiles/$bookname"* "$(basename "$MEDIA_FOLDER/rafiles")" >> "$MEDIA_FOLDER/zip_log.txt" 2>&1 || { echo "Error: Unable to zip files."; exit 1; }

    # Log the number of files in rafiles
    num_files_rafiles=$(find "$MEDIA_FOLDER/rafiles" -maxdepth 1 -name "$bookname*" | wc -l)
    echo "Audio files: $num_files_rafiles" >> "$MEDIA_FOLDER/zip_log.txt"

    # Log the number of files in zip
    # Should be +3 of actual file count
    num_files_zip=$(zipinfo -l "$MEDIA_FOLDER/$bookname.zip" | wc -l)
    echo "Zipped files: $num_files_zip" >> "$MEDIA_FOLDER/zip_log.txt"

done < "$MEDIA_FOLDER/names.txt"

exit 0
