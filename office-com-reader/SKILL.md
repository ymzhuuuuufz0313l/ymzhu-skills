---
name: office-com-reader
description: Read content from encrypted or password-protected Microsoft Office documents (Excel .xlsx, Word .docx, PowerPoint .pptx) and PDF files on Windows. For Office files it uses the native Office COM API; for PDFs it uses Python/pypdf (with an Adobe Acrobat COM fallback). Use when the user needs to extract text, sheet names, cell values, slide notes, or document content from files that are encrypted or otherwise unreadable via standard libraries — including PDFs scrambled on disk by enterprise DLP transparent encryption. This skill works when the current Windows user session already has the document unlocked or transparent decryption access (e.g., the file opens fine manually in Office/Acrobat, or python.exe is a DLP-trusted process).
---

# Office COM Reader

Read encrypted/protected Microsoft Office documents via the native COM API, and encrypted PDFs via Python/pypdf or Adobe Acrobat COM.

## When to Use

- The user asks to read an Excel, Word, PowerPoint, or PDF file that is encrypted or password-protected.
- Standard Python libraries (`openpyxl`, `python-docx`, etc.) fail with password errors.
- PDF tools (`pdftotext`, etc.) report "not a PDF" or garbage, but the file opens fine in a viewer — a hallmark of enterprise DLP transparent file encryption (whole file scrambled, no `%PDF` header).
- The user indicates they can open the file manually, suggesting the current Windows session has cached/unlocked access.

## How It Works (Office)

1. Use `Excel.Application`, `Word.Application`, or `PowerPoint.Application` COM objects.
2. Open the target file invisibly (`Visible = False`).
3. Extract the needed content (sheet names, cell text, document text, slide text/notes).
4. Close the document and quit the Office application without saving.

> **Important prerequisite**: This method relies on the current Windows user already having the document unlocked. If Office prompts for a password, the COM call will fail.

## How It Works (PDF)

Three protection scenarios, in order of preference:

1. **DLP transparent encryption** (file scrambled on disk, no `%PDF` header; opens fine in authorized apps): read the file **with python.exe** (`scripts/read_pdf.py`). DLP filter drivers commonly whitelist python.exe, so Python reads *decrypted* bytes transparently and pypdf parses them normally. Verified on VESA DP standard PDFs protected this way.
2. **Standard PDF encryption** (`/Encrypt` dictionary): same script — it tries an empty password first (covers owner-password-only files), then `--password` if provided.
3. **Acrobat COM fallback** (`scripts/read_pdf_acrobat.vbs`): when Python cannot read the file but the session can open it in full Adobe Acrobat, extract text via `AcroExch` + JSObject. Requires Acrobat IAC to be registered (Reader alone is not enough); note that some DLP agents block cross-process COM entirely, in which case only the Python path works.

For **scanned/image-only PDFs** (text extraction returns empty), use `read_pdf.py --images DIR` to dump embedded page images, then read the images with the multimodal image-reading tool. Pages that are pure vector graphics (no embedded image, no text) cannot be handled this way — open them in a viewer and screenshot instead.

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
| `read_pdf.py` | Extract text (or page images) from PDFs, incl. DLP-encrypted and password-protected ones |
| `read_pdf_acrobat.vbs` | PDF text extraction fallback via Adobe Acrobat COM (AcroExch + JSObject) |

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

### PDF

```bash
# Extract all text (handles DLP-encrypted and empty-password PDFs)
python scripts/read_pdf.py "D:\path\to\file.pdf" --out output.txt

# A page range only (1-based)
python scripts/read_pdf.py "D:\path\to\file.pdf" --pages 1-20 --out output.txt

# Password-protected PDF
python scripts/read_pdf.py "D:\path\to\file.pdf" --password 123456 --out output.txt

# Scanned PDF: dump page images, then view them with the image-reading tool
python scripts/read_pdf.py "D:\path\to\file.pdf" --pages 1-5 --images out_imgs

# Acrobat COM fallback (only when the Python path fails but Acrobat opens the file)
cscript //Nologo scripts/read_pdf_acrobat.vbs "D:\path\to\file.pdf" 1 10 > output.txt
```

For large PDFs (hundreds of pages), always extract to a file with `--out` and then search/page through it with Grep/Read instead of pulling everything into context.

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

If COM fails (e.g., Office not installed or password prompt appears) and `read_pdf.py` cannot read a PDF either (python.exe not DLP-trusted, unknown password, Acrobat IAC blocked), ask the user to:
1. Open the document manually in Office / a PDF viewer.
2. Copy or export the relevant content to a plain text / CSV file, or screenshot the relevant pages.
3. Share that file or image instead.

> **Compliance note**: this skill only reuses access the current Windows session already legitimately has (cached Office/Acrobat credentials, DLP transparent decryption for trusted processes). Do not attempt to crack passwords, and do not write decrypted copies of DLP-protected files to locations the user did not ask for.
