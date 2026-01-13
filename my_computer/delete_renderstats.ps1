function DeleteFiletype {
        <#
    .DESCRIPTION
        Deletes all files of a given extension in given folder
    .PARAMETER <folder>
        $folder = Path to remove files from

    .PARAMETER <extension>
        $extension = what file type to delete
    #>

    param([string]$folder, [string]$extension)

    Remove-Item $folder -Verbose -Recurse -Include *.$extension
}


 DeleteFiletype $Env:RADIO_FOLDER 'render_stats.html'