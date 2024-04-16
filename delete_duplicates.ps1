# Define the directory where the files are located
$destinationFolder = "C:\Users\NPC\Desktop\backup"
$files = Get-ChildItem -Path $destinationFolder -Filter "SONG*" -File
$hashTable = @{}


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
    $logFilePath = Join-Path -Path $destinationFolder -ChildPath "rename_log.txt"
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
    $logFilePath = Join-Path -Path "C:\Users\NPC\Documents\GIthub\scripts" -ChildPath "rename_log.txt"
    $changes | Out-File -FilePath $logFilePath -Append

    Write-Host "Renaming operations logged to $logFilePath."
}
Remove-DuplicateWavs
Rename-WavFiles