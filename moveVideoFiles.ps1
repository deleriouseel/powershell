$sourcePath = "D:\Studies"
$destinationPath = "\\DocuSynology\Videos"

$minAgeInDays = 14
$minAgeDate = (Get-Date).AddDays(-$minAgeInDays)

$logFolderPath = [Environment]::GetFolderPath("MyDocuments")
$logFile = Join-Path -Path $logFolderPath -ChildPath CopyToBackup.log

function Write-Log {
    param (
        [string]$Message
    )
    Add-Content -Path $logFile -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
}


Write-Log "Script started."

# Move files
Get-ChildItem -Path $sourcePath -Recurse | Where-Object { $_.LastWriteTime -lt $minAgeDate -and $_.Extension -ne ".mkv" } | ForEach-Object {
    if (-not $_.PSIsContainer) {
        $destinationFile = Join-Path -Path $destinationPath -ChildPath $_.FullName.Substring($sourcePath.Length + 1)
        $destinationFolder = Split-Path -Path $destinationFile -Parent

        # Create destination folder if it doesn't exist
        Create-DestinationFolder -Path $destinationFolder

        Move-Item -Path $_.FullName -Destination $destinationFile -Force -WhatIf
        Write-Log "Moved $($_.FullName) to $destinationFile"
    }
    else {
        # Ignore local folder if empty
        $localFolderPath = $destinationPath + $_.FullName.Substring($sourcePath.Length)
        if (Folder-IsEmpty -Path $localFolderPath) {
            Write-Log "Ignoring local empty folder: $localFolderPath"
        }
        else {
            # Creat remote folder if necessary
            $remoteFolderPath = $destinationPath + $_.FullName.Substring($sourcePath.Length)
            if (-not (Test-Path -Path $remoteFolderPath)) {
                Write-Log "Moving files into new remote folder: $remoteFolderPath"
                Create-DestinationFolder -Path $remoteFolderPath
            }
        }
    }
}

Write-Log "Script completed."


