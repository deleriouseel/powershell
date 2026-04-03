# ROLAND-PC moves >2 week old files from Desktop/encoded to Desktop/backup weekly.

get-childitem -path "C:\Users\NPC\Desktop\Encoded\" -exclude *.png, 67-QAA* | where-object {$_.LastWriteTime -lt (get-date).AddDays(-14)} | move-item -destination "C:\Users\NPC\Desktop\backup\"
