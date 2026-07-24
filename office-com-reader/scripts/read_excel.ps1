param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FilePath,

    [Parameter(Position = 1)]
    [string]$SheetName
)

# Read content from an Excel file via Office COM API, output UTF-8.
# Usage: powershell -ExecutionPolicy Bypass -File read_excel.ps1 "D:\path\to\file.xlsx" [SheetName]

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    $excel = New-Object -ComObject Excel.Application
} catch {
    Write-Output "ERROR: Failed to create Excel.Application: $_"
    exit 1
}

$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $wb = $excel.Workbooks.Open($FilePath, $true, $true)
} catch {
    Write-Output "ERROR: Failed to open workbook: $_"
    $excel.Quit()
    exit 1
}

Write-Output "OPEN_OK"
Write-Output "SHEETS:"
foreach ($ws in $wb.Sheets) {
    Write-Output "  $($ws.Name)"
}

foreach ($ws in $wb.Sheets) {
    if ($SheetName -and ($ws.Name -ne $SheetName)) {
        continue
    }

    Write-Output ""
    Write-Output "=== SHEET: $($ws.Name) ==="

    $used = $ws.UsedRange
    $rows = $used.Rows.Count
    $cols = $used.Columns.Count

    # Limit output to avoid flooding
    $maxRow = [Math]::Min($rows, 120)
    $maxCol = [Math]::Min($cols, 20)

    Write-Output "DIM: $maxRow rows x $maxCol cols"

    for ($r = 1; $r -le $maxRow; $r++) {
        $lineParts = @()
        for ($c = 1; $c -le $maxCol; $c++) {
            $val = $ws.Cells.Item($r, $c).Text
            if ([string]::IsNullOrWhiteSpace($val)) {
                $lineParts += ""
            } else {
                $lineParts += $val
            }
        }
        $line = ($lineParts -join "|") + "|"
        Write-Output $line
    }
}

$wb.Close($false)
$excel.Quit()
