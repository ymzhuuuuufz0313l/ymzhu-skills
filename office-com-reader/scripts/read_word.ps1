param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FilePath
)

# Read plain text from a Word document via Office COM API, output UTF-8.
# Usage: powershell -ExecutionPolicy Bypass -File read_word.ps1 "D:\path\to\file.docx"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    $word = New-Object -ComObject Word.Application
} catch {
    Write-Output "ERROR: Failed to create Word.Application: $_"
    exit 1
}

$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $doc = $word.Documents.Open($FilePath, $true, $true)
} catch {
    Write-Output "ERROR: Failed to open document: $_"
    $word.Quit()
    exit 1
}

Write-Output "OPEN_OK"
Write-Output $doc.Range.Text

$doc.Close($false)
$word.Quit()
