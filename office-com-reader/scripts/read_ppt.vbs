' Read text from a PowerPoint deck via Office COM API.
' Usage: cscript //Nologo read_ppt.vbs "D:\path\to\file.pptx"

Option Explicit

Dim pptApp, pres, args, filePath
Dim slide, shape, notesText

Set args = WScript.Arguments
If args.Count < 1 Then
    WScript.Echo "Usage: cscript //Nologo read_ppt.vbs ""D:\path\to\file.pptx"""
    WScript.Quit 1
End If

filePath = args(0)

On Error Resume Next
Set pptApp = CreateObject("PowerPoint.Application")
If Err.Number <> 0 Then
    WScript.Echo "ERROR: Failed to create PowerPoint.Application: " & Err.Description
    WScript.Quit 1
End If
On Error GoTo 0

pptApp.Visible = False

On Error Resume Next
Set pres = pptApp.Presentations.Open(filePath, , , False)
If Err.Number <> 0 Then
    WScript.Echo "ERROR: Failed to open presentation: " & Err.Description
    pptApp.Quit
    WScript.Quit 1
End If
On Error GoTo 0

WScript.Echo "OPEN_OK"
WScript.Echo "SLIDES: " & pres.Slides.Count

For Each slide In pres.Slides
    WScript.Echo ""
    WScript.Echo "=== SLIDE " & slide.SlideIndex & " ==="

    For Each shape In slide.Shapes
        If shape.HasTextFrame Then
            If Not IsNull(shape.TextFrame.TextRange.Text) Then
                WScript.Echo shape.TextFrame.TextRange.Text
            End If
        End If
    Next

    If slide.HasNotesPage Then
        notesText = slide.NotesPage.Shapes(2).TextFrame.TextRange.Text
        If Not IsNull(notesText) And Len(Trim(notesText)) > 0 Then
            WScript.Echo "--- NOTES ---"
            WScript.Echo notesText
        End If
    End If
Next

pres.Close
pptApp.Quit
