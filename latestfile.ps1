function LastRadioFile {
            <#
    .DESCRIPTION
        Gets last file worked on in a folder
    .PARAMETER <folder>
        $folder = Path to remove files from
    .PARAMETER <howmany>
        $howmany = Integer. Sometimes you want more than just the latest one.
    #>

    param([string]$folder, [int]$howmany)


(Get-ChildItem -Attributes !Directory -Path $folder | Sort-Object -Descending -Property LastWriteTime | Select-Object -First $howmany)

}

 LastRadioFile $env:RADIO_FOLDER 5