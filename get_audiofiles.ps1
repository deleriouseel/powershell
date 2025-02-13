# Gets the files from the USB drive and copies them to the destination folder, renaming them in the process. 
# It also removes duplicate files based on their modified date and logs the changes to a file.

# Define the name of the USB drive to monitor
$usbDriveName = "ROLAND"
$sourceFolder = "\RSS\M-400\SONGS\"
$destinationFolder = "C:\Users\NPC\Desktop\backup"
$logFolder =  "C:\Users\NPC\Documents\GIthub\scripts"
$files = Get-ChildItem -Path $destinationFolder -Filter "SONG*" -File
$hashTable = @{}

function Copy-USBContents {
    param (
        [string]$source,
        [string]$destination
    )

    # Error handling for Get-ChildItem
    try {
        $files = Get-ChildItem -Path $source -ErrorAction Stop
    }
    catch {
        Write-Host "Error: Failed to retrieve files from $source. $_"
        return
    }

    Write-Host "Found $($files.Count) file(s) in $source"

    # Copy files from source to destination if they don't exist in the destination
    foreach ($file in $files) {
        $fileExtension = $file.Extension
        # Generate modified date string in the format 'yyyyMMdd'
        $modifiedDate = $file.LastWriteTime.ToString("yyyyMMdd")
        $newFileName = "{0}_{1}{2}" -f $file.BaseName, $modifiedDate, $fileExtension

        # Build destination file path
        $destinationFile = Join-Path -Path $destination -ChildPath $newFileName

        Write-Host "Copying $($file.FullName) to $destinationFile"
        if (-not (Test-Path $destinationFile)) {
            try {
                Copy-Item -Path $file.FullName -Destination $destinationFile -Force
                Write-Host "File $($file.FullName) copied successfully."
            }
            catch {
                Write-Host "Error: Failed to copy $($file.FullName) to $destination. $_"
            }
        }
        else {
            Write-Host "File $($file.FullName) already exists in $destination. Skipping."
        }
    }
}

# Function to check for the USB drive
function Update-USBInsertion {
    $drive = Get-WmiObject Win32_Volume | Where-Object { $_.DriveType -eq 2 }

    if ($drive.label -eq $usbDriveName) {
        Write-Host "USB Drive '$usbDriveName' detected."
        $sourcePath = Join-Path -Path "$($drive.DriveLetter)" -ChildPath $sourceFolder
        Copy-USBContents -source $sourcePath -destination $destinationFolder
        Write-Host "Contents of USB Drive '$usbDriveName' copied to '$destinationFolder'."
        return $true
    }
    else {
        Write-Host "No USB drive detected"
        return $false
    }
} 

function Remove-DuplicateWavs{

    $changes = @()
foreach ($file in $files) {
    # Extract the date from the file name
    $date = $file.Name -replace 'SONG(\d{8})\D*$', '$1'
    $date = $matches[1]

    # If a file with the same date exists in the hashtable
    if ($hashTable.ContainsKey($date)) {
        Remove-Item $file.FullName -Force
        $changes += "Deleted $($file.Name)."
    }
    else {
        # Add the file name to the hashtable
        $hashTable[$date] = $file.Name
    }
}
        # Write changes to log file
    $logFilePath = Join-Path -Path $logFolder -ChildPath "rename_log.txt"
    $changes | Out-File -FilePath $logFilePath -Append
}
function Rename-WavFiles {
  
    $filesToRename = Get-ChildItem -Path $destinationFolder -Filter "*_??????????.wav" -File
    $changes = @()

    # Loop through each file to rename
    foreach ($file in $filesToRename) {

        $newFileName = $file.Name -replace '_\d{8}', ''
        Write-Host $newFileName
        Rename-Item -Path $file.FullName -NewName $newFileName -Force

        $changes += "Renamed $($file.Name) to $newFileName"
        
    }

    # Write changes to log file
    $logFilePath = Join-Path -Path  $logFolder -ChildPath "rename_log.txt"
    $changes | Out-File -FilePath $logFilePath -Append

    Write-Host "Renaming operations logged to $logFilePath."
}
Update-USBInsertion
Remove-DuplicateWavs
Rename-WavFiles
