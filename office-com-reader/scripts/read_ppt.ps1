param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FilePath
)

# Read text from a PowerPoint deck via Office COM API, output UTF-8.
# Usage: powershell -ExecutionPolicy Bypass -File read_ppt.ps1 "D:\path\to\file.pptx"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    $ppt = New-Object -ComObject PowerPoint.Application
} catch {
    Write-Output "ERROR: Failed to create PowerPoint.Application: $_"
    exit 1
}

$ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoFalse

try {
    $pres = $ppt.Presentations.Open($FilePath, $true, $true, $false)
} catch {
    Write-Output "ERROR: Failed to open presentation: $_"
    $ppt.Quit()
    exit 1
}

Write-Output "OPEN_OK"
Write-Output "SLIDES: $($pres.Slides.Count)"

foreach ($slide in $pres.Slides) {
    Write-Output ""
    Write-Output "=== SLIDE $($slide.SlideIndex) ==="

    foreach ($shape in $slide.Shapes) {
        if ($shape.HasTextFrame -eq [Microsoft.Office.Core.MsoTriState]::msoTrue) {
            $text = $shape.TextFrame.TextRange.Text
            if (-not [string]::IsNullOrWhiteSpace($text)) {
                Write-Output $text
            }
        }
    }

    if ($slide.HasNotesPage -eq [Microsoft.Office.Core.MsoTriState]::msoTrue) {
        $notesText = $slide.NotesPage.Shapes.Item(2).TextFrame.TextRange.Text
        if (-not [string]::IsNullOrWhiteSpace($notesText)) {
            Write-Output "--- NOTES ---"
            Write-Output $notesText
        }
    }
}

$pres.Close()
$ppt.Quit()
