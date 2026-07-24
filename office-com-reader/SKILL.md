---
name: office-com-reader
description: Read content from encrypted or password-protected Microsoft Office documents (Excel .xlsx, Word .docx, PowerPoint .pptx) using the native Office COM API on Windows. Use when the user needs to extract text, sheet names, cell values, slide notes, or document content from Office files that are encrypted or otherwise unreadable via standard libraries like openpyxl/python-docx. This skill works when the current Windows user session already has the document unlocked (e.g., Excel is open with the file), because the Office COM API reuses the cached credentials.
---

# Office COM Reader

Read encrypted/protected Microsoft Office documents via the native COM API.

## When to Use

- The user asks to read an Excel, Word, or PowerPoint file that is encrypted or password-protected.
- Standard Python libraries (`openpyxl`, `python-docx`, etc.) fail with password errors.
- The user indicates they can open the file manually in Office, suggesting the current Windows session has cached/unlocked access.

## How It Works

1. Use `Excel.Application`, `Word.Application`, or `PowerPoint.Application` COM objects.
2. Open the target file invisibly (`Visible = False`).
3. Extract the needed content (sheet names, cell text, document text, slide text/notes).
4. Close the document and quit the Office application without saving.

> **Important prerequisite**: This method relies on the current Windows user already having the document unlocked. If Office prompts for a password, the COM call will fail.

## Available Scripts

All scripts are in `scripts/`:

| Script | Purpose |
|--------|---------|
| `read_excel.vbs` | List sheets and dump cell text from an Excel file |
| `read_excel.ps1` | Same as above, PowerShell version, UTF-8 output |
| `read_word.vbs` | Extract plain text from a Word document |
| `read_word.ps1` | Same as above, PowerShell version |
| `read_ppt.vbs` | Extract text from each slide of a PowerPoint deck |
| `read_ppt.ps1` | Same as above, PowerShell version |

## Quick Usage

### Excel

```bash
# List sheets and dump first 120 rows x 15 cols from each sheet
cscript //Nologo scripts/read_excel.vbs "D:\path\to\file.xlsx" > output.txt

# UTF-8 PowerShell version
powershell -ExecutionPolicy Bypass -File scripts/read_excel.ps1 "D:\path\to\file.xlsx" > output.txt
```

### Word

```bash
cscript //Nologo scripts/read_word.vbs "D:\path\to\file.docx" > output.txt
powershell -ExecutionPolicy Bypass -File scripts/read_word.ps1 "D:\path\to\file.docx" > output.txt
```

### PowerPoint

```bash
cscript //Nologo scripts/read_ppt.vbs "D:\path\to\file.pptx" > output.txt
powershell -ExecutionPolicy Bypass -File scripts/read_ppt.ps1 "D:\path\to\file.pptx" > output.txt
```

## Output Handling

- VBScript output encoding depends on the system ANSI code page; use it for quick checks or ASCII content.
- PowerShell scripts explicitly set UTF-8 output; prefer these when Chinese or other non-ASCII text is present.
- If content is large, save to a file and then process with Python/Shell rather than keeping it all in context.

## Customization Tips

- Adjust row/column limits in the scripts based on the document size.
- For Excel, replace `"Sheet1"` with the actual sheet name or iterate all sheets.
- For Word, change `.Text` extraction to `.Range.Text` or paragraph iteration as needed.
- For PowerPoint, iterate `Slides`, `Shapes`, and `NotesPage.TextFrame.TextRange.Text` for complete content.

## Fallback

If COM fails (e.g., Office not installed or password prompt appears), ask the user to:
1. Open the document manually in Office.
2. Copy or export the relevant content to a plain text / CSV / PDF file.
3. Share that file instead.
