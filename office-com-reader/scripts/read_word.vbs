' Read plain text from a Word document via Office COM API.
' Usage: cscript //Nologo read_word.vbs "D:\path\to\file.docx"

Option Explicit

Dim wordApp, doc, args, filePath

Set args = WScript.Arguments
If args.Count < 1 Then
    WScript.Echo "Usage: cscript //Nologo read_word.vbs ""D:\path\to\file.docx"""
    WScript.Quit 1
End If

filePath = args(0)

On Error Resume Next
Set wordApp = CreateObject("Word.Application")
If Err.Number <> 0 Then
    WScript.Echo "ERROR: Failed to create Word.Application: " & Err.Description
    WScript.Quit 1
End If
On Error GoTo 0

wordApp.Visible = False
wordApp.DisplayAlerts = False

On Error Resume Next
Set doc = wordApp.Documents.Open(filePath, , True)
If Err.Number <> 0 Then
    WScript.Echo "ERROR: Failed to open document: " & Err.Description
    wordApp.Quit
    WScript.Quit 1
End If
On Error GoTo 0

WScript.Echo "OPEN_OK"
WScript.Echo doc.Range.Text

doc.Close False
wordApp.Quit
