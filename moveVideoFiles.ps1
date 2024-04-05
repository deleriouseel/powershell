$sourcePath = "D:\Studies"
$destinationPath = "\\backup\video"

$minAgeInDays = 7
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
    $destinationFile = Join-Path -Path $destinationPath -ChildPath $_.FullName.Substring($sourcePath.Length + 1)
    $destinationFolder = Split-Path -Path $destinationFile -Parent

    # Create destination folder if it doesn't exist
    if (-not (Test-Path -Path $destinationFolder)) {
        New-Item -ItemType Directory -Path $destinationFolder | Out-Null
    }

    Move-Item -Path $_.FullName -Destination $destinationFile -Force -WhatIf
    Write-Log "Moved $($_.FullName) to $destinationFile"
}

Write-Log "Script completed."


