
function Send-SendGridEmail {
    <#
    .SYNOPSIS
    Function to send email with Twilio SendGrid
    
    .DESCRIPTION
    A function to send a text or HTML based email with PowerShell and SendGrid.
    See https://docs.sendgrid.com/api-reference/mail-send/mail-send for API details.
    Update the API key and from address in the function before using.
    This script provided as-is with no warranty. Test it before you trust it.
    www.ciraltos.com
       
    .PARAMETER to_email
    The destination email address.
       
    .PARAMETER subject
    The subject of the email.
    
    .PARAMETER contentType
    The content type, values are “text/plain” or “text/html”.  "text/plain" set by default.
    
    .PARAMETER contentBody
    The HTML or plain text content that of the email.

    .NOTES
    Version:        2.0
    Author:         Travis Roberts
    Creation Date:  12/1/2022
    Purpose/Change: Update for latest release of Twilio SendGrid
    ****   Update the API key and from email address with matching settings from SendGrid  ****
    ****   From address must be validated to before email delivery                         ****
    ****   This script provided as-is with no warranty. Test it before you trust it.       ****
    
    .Example
    See my YouTube channel at http://www.youtube.com/c/TravisRoberts or https://www.ciraltos.com for details.
    #>

    param(
        [Parameter(Mandatory = $true)]
        [String] $to_email,
        [Parameter(Mandatory = $true)]
        [String] $subject,
        [Parameter(Mandatory = $false)]
        [string]$contentType = 'text/plain',
        [Parameter(Mandatory = $true)]
        [String] $contentBody
    )

    ############ Update with your SendGrid API Key and Verified Email Address ####################
    $apiKey = $Env:SENDGRID_API_KEY
    $to_email = $Env:EMAIL_TO
    $from_email = $Env:EMAIL_FROM
    

  
    $headers = @{
        'Authorization' = 'Bearer ' + $apiKey
        'Content-Type'  = 'application/json'
    }
  
    $body = @{
        personalizations = @(
            @{
                to = @(
                    @{
                        email = $to_email
                    }
                )
            }
        )
        from             = @{
            email = $from_email
        }
        subject          = $subject
        content          = @(
            @{
                type  = $contentType
                value = $contentBody
            }
        )
    }
  
    try {
        $bodyJson = $body | ConvertTo-Json -Depth 4
    }
    catch {
        $ErrorMessage = $_.Exception.message
        write-error ('Error converting body to json ' + $ErrorMessage)
        Break
    }
  
    try {
        Invoke-RestMethod -Uri https://api.sendgrid.com/v3/mail/send -Method Post -Headers $headers -Body $bodyJson 
    }
    catch {
        $ErrorMessage = $_.Exception.message
        write-error ('Error with Invoke-RestMethod ' + $ErrorMessage)
        Break
    }

}
  

$searchText = "Idle, call duration"  
$telos_auth = $Env:TELOS_AUTH

$headers = @{
    'Cache-Control'             = 'max-age=0'
    'Authorization'             = "Basic $telos_auth"
    'Upgrade-Insecure-Requests' = '1'
    'User-Agent'                = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36'
    'Accept'                    = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    'Referer'                   = 'http://10.10.0.20/' 
    'Accept-Encoding'           = 'gzip, deflate' 
    'Accept-Language'           = 'en-US,en;q=0.9'
}


Start-Transcript -Path "C:\Users\Kristin\Documents\GitHub\powershell\telos_disconnect.log"

try {
    Write-Host "Starting Disconnect"
    Invoke-RestMethod -Method GET -Uri http://10.10.0.20/cmd/call/disconnect -Headers $headers -StatusCodeVariable 'response'
    Write-Host $response
    try {
        Start-Sleep -Seconds 30
        $webPageContent = Invoke-WebRequest -Uri "http://10.10.0.20/logs" -Headers $headers 
        $telosPage = $webPageContent.Content -split '\r?\n' | Where-Object { $_ -like "*$searchText*" }
        

        if ($telosPage.Count -gt 0) {
            foreach ($line in $telosPage) {
                Write-Host "Text '$searchText' found on $webPageUrl in line: $line"
            }
        }
        else {
            Write-Host "StatusCode:" $_.Exception.Response.StatusCode.value__ 

            $splat = @{
                subject     = 'Telos NOT disconnected'
                contentBody = $_.Exception.Response.StatusCode.value__ 
                to_email    = $to_email
            }

                Send-SendGridEmail @splat
        }
    }
    catch {
        Write-Host "StatusCode:" $_.Exception.Response.StatusCode.value__ 

        $splat = @{
            subject     = 'Telos did not respond'
            contentBody = $_.Exception.Response.StatusCode.value__ 
            to_email    = $to_email
        }

        Send-SendGridEmail @splat
        exit
    }


}

catch {

    Write-Host "StatusCode:" $_.Exception.Response.StatusCode.value__ 

    $splat = @{
        subject     = 'Telos may not be disconnected'
        contentBody = $_.Exception.Response.StatusCode.value__ 
        to_email    = $to_email
    }

    Send-SendGridEmail @splat
}

Stop-Transcript