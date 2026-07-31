' read_pdf_acrobat.vbs - Extract text from a PDF via Adobe Acrobat's COM API.
'
' Fallback for cases where Python/pypdf cannot read the file but the current
' Windows session can open it in Adobe Acrobat (full Acrobat, not Reader),
' e.g. the document is already unlocked in this session. This reuses the
' session's cached credentials, same philosophy as the Office COM scripts.
'
' NOTE: This requires Acrobat's IAC (AcroExch.*) COM classes to be registered.
' Acrobat Reader alone does not provide them, and some enterprise DLP agents
' block cross-process COM entirely - in that case prefer read_pdf.py.
'
' Usage:
'   cscript //Nologo read_pdf_acrobat.vbs "D:\path\to\file.pdf" [firstPage] [lastPage] > output.txt
' Pages are 1-based; defaults to the whole document.

Option Explicit

Dim fso, app, av, pd, js, path, firstPg, lastPg, i, j, nw, line

path = WScript.Arguments(0)
firstPg = 1
lastPg = -1
If WScript.Arguments.Count >= 2 Then firstPg = CInt(WScript.Arguments(1))
If WScript.Arguments.Count >= 3 Then lastPg = CInt(WScript.Arguments(2))

On Error Resume Next
Set app = CreateObject("AcroExch.App")
If Err.Number <> 0 Then
    WScript.Echo "[error] Cannot create AcroExch.App: " & Err.Description & _
        " (Acrobat IAC not registered or blocked; use read_pdf.py instead)"
    WScript.Quit 2
End If
On Error GoTo 0

app.Hide()

Set av = CreateObject("AcroExch.AVDoc")
If Not av.Open(path, "") Then
    WScript.Echo "[error] Acrobat failed to open the file (password prompt or unsupported protection)"
    app.Exit()
    WScript.Quit 3
End If

Set pd = av.GetPDDoc()
If lastPg < 1 Or lastPg > pd.GetNumPages() Then lastPg = pd.GetNumPages()

On Error Resume Next
Set js = pd.GetJSObject()
If Err.Number <> 0 Then
    WScript.Echo "[error] GetJSObject failed: " & Err.Description
    av.Close True
    app.Exit()
    WScript.Quit 4
End If
On Error GoTo 0

For i = firstPg - 1 To lastPg - 1
    WScript.Echo "<<< Page " & (i + 1) & " >>>"
    nw = js.getPageNumWords(i)
    line = ""
    For j = 0 To nw - 1
        line = line & js.getPageNthWord(i, j) & " "
    Next
    WScript.Echo line
    WScript.Echo ""
Next

av.Close True
app.Exit()
