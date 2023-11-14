$from_email = $Env:M365_ADMIN_EMAIL
$to_email = $env:EMAIL_TO
$username = $Env:M365_ADMIN_EMAIL
$password = $Env:M365_ADMIN_PASSWORD
$telos_auth = $Env:TELOS_AUTH
$cred = New-Object -TypeName System.Management.Automation.PSCredential -argumentlist $userName, $(convertto-securestring $Password -asplaintext -force)


$headers = @{
    'Cache-Control' = 'max-age=0'
	'Authorization' =  "Basic $telos_auth"
	'Upgrade-Insecure-Requests' =  '1'
	'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36'
	'Accept' = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
	'Referer' = 'http://10.10.0.20/' 
	'Accept-Encoding' = 'gzip, deflate' 
	'Accept-Language' = 'en-US,en;q=0.9'
}

Start-Transcript -Path "C:\Users\Kristin\Documents\GitHub\powershell\telos_disconnect.log"

try{
Write-Host "Starting Disconnect"
Invoke-RestMethod -Method GET -Uri http://10.10.0.20/cmd/call/disconnect -Headers $headers -StatusCodeVariable 'response'
Send-MailMessage -From $from_email -to $to_email  -Subject "Telos disconnected" -Body $response -SmtpServer smtp.office365.com -port 587 -UseSsl -Credential $cred 
}

catch {
	Write-Host "StatusCode:" $_.Exception.Response.StatusCode.value__ 
	$description = Write-Host "StatusDescription:" $_.Exception.Response.StatusDescription
	Send-MailMessage -From $from_email -to $to_email  -Subject "Telos did not disconnect" -Body "$response <p> $description</p>" -SmtpServer smtp.office365.com -port 587 -UseSsl -Credential $cred 
} 
	

Stop-Transcript