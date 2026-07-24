' Read content from an Excel file via Office COM API.
' Usage: cscript //Nologo read_excel.vbs "D:\path\to\file.xlsx" [SheetName]

Option Explicit

Dim excelApp, wb, ws, args, filePath, sheetName
Dim usedRange, maxRow, maxCol, r, c, val, line
Dim requestedSheet, processSheet

Set args = WScript.Arguments
If args.Count < 1 Then
    WScript.Echo "Usage: cscript //Nologo read_excel.vbs ""D:\path\to\file.xlsx"" [SheetName]"
    WScript.Quit 1
End If

filePath = args(0)
requestedSheet = ""
If args.Count >= 2 Then
    requestedSheet = args(1)
End If

On Error Resume Next
Set excelApp = CreateObject("Excel.Application")
If Err.Number <> 0 Then
    WScript.Echo "ERROR: Failed to create Excel.Application: " & Err.Description
    WScript.Quit 1
End If
On Error GoTo 0

excelApp.Visible = False
excelApp.DisplayAlerts = False

On Error Resume Next
Set wb = excelApp.Workbooks.Open(filePath, , True)
If Err.Number <> 0 Then
    WScript.Echo "ERROR: Failed to open workbook: " & Err.Description
    excelApp.Quit
    WScript.Quit 1
End If
On Error GoTo 0

WScript.Echo "OPEN_OK"
WScript.Echo "SHEETS:"
For Each ws In wb.Sheets
    WScript.Echo "  " & ws.Name
Next

For Each ws In wb.Sheets
    processSheet = True
    If requestedSheet <> "" Then
        If ws.Name <> requestedSheet Then
            processSheet = False
        End If
    End If

    If processSheet Then
        WScript.Echo ""
        WScript.Echo "=== SHEET: " & ws.Name & " ==="

        Set usedRange = ws.UsedRange
        maxRow = usedRange.Rows.Count
        maxCol = usedRange.Columns.Count

        ' Limit output to avoid flooding
        If maxRow > 120 Then maxRow = 120
        If maxCol > 20 Then maxCol = 20

        WScript.Echo "DIM: " & maxRow & " rows x " & maxCol & " cols"

        For r = 1 To maxRow
            line = ""
            For c = 1 To maxCol
                val = ws.Cells(r, c).Text
                If IsEmpty(val) Then
                    line = line & "|"
                Else
                    line = line & CStr(val) & "|"
                End If
            Next
            WScript.Echo line
        Next
    End If
Next

wb.Close False
excelApp.Quit
