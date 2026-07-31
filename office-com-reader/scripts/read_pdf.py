#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
read_pdf.py - Extract text from PDF files, including encrypted / DRM-protected ones.

Two protection scenarios are handled:

1. Standard PDF encryption (/Encrypt dictionary, password-protected open):
   pypdf tries an empty password first, then the password passed via --password.

2. Enterprise DLP / transparent file encryption (whole file is scrambled on disk,
   no %PDF header visible to most tools): if the current Windows session runs a
   DLP agent that whitelists python.exe, this script reads the *decrypted* bytes
   transparently and pypdf parses them normally. This mirrors the office-com-reader
   philosophy: reuse access the current user session already has.

Usage:
    python read_pdf.py <file.pdf> [--password PW] [--pages A-B] [--out out.txt]

Output: UTF-8 text, one "<<< Page N >>>" marker per page.
"""
import argparse
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="Path to the PDF file")
    ap.add_argument("--password", "-p", default=None, help="Open password, if known")
    ap.add_argument("--pages", default=None, help="Page range, 1-based, e.g. 1-10")
    ap.add_argument("--out", default=None, help="Write output to this file instead of stdout")
    ap.add_argument("--images", default=None, metavar="DIR",
                    help="Scanned-PDF mode: extract embedded page images into DIR "
                         "(one file per image) instead of text; view them with an "
                         "image-reading tool afterwards.")
    args = ap.parse_args()

    # Peek at the header to report which protection scenario we are in.
    with open(args.pdf, "rb") as fh:
        head = fh.read(8)
    transparent = not head.startswith(b"%PDF")
    if transparent:
        print("[info] File has no %PDF header as read by python: likely DLP "
              "transparent encryption; python.exe sees decrypted bytes.",
              file=sys.stderr)

    from pypdf import PdfReader

    try:
        reader = PdfReader(args.pdf)
    except Exception as e:
        print(f"[error] Cannot parse PDF: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    if reader.is_encrypted:
        for pw in ([""] if args.password is None else [args.password]):
            if reader.decrypt(pw):
                break
        else:
            print("[error] PDF is password-encrypted and the password did not work. "
                  "Pass --password, or fall back to the Acrobat COM script.",
                  file=sys.stderr)
            return 3

    total = len(reader.pages)
    start, end = 1, total
    if args.pages:
        a, _, b = args.pages.partition("-")
        start = int(a) if a else 1
        end = int(b) if b else total
    start = max(1, start)
    end = min(total, end)

    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    if out is sys.stdout:
        try:
            out.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print(f"[info] pages={total} extracting {start}-{end}", file=sys.stderr)

    if args.images:
        import os
        os.makedirs(args.images, exist_ok=True)
        saved = 0
        for i in range(start - 1, end):
            try:
                imgs = reader.pages[i].images
            except Exception as e:
                print(f"[warn] page {i + 1}: cannot list images: {e}", file=sys.stderr)
                continue
            for j, im in enumerate(imgs):
                fn = os.path.join(args.images, f"page{i + 1:04d}_{j}_{im.name}")
                with open(fn, "wb") as fh:
                    fh.write(im.data)
                print(fn)
                saved += 1
        print(f"[info] saved {saved} image(s) to {args.images}", file=sys.stderr)
        if saved == 0:
            print("[warn] No embedded images found; pages may be vector graphics. "
                  "Open the file in a viewer and screenshot the page instead.",
                  file=sys.stderr)
        return 0

    for i in range(start - 1, end):
        try:
            text = reader.pages[i].extract_text() or ""
        except Exception as e:
            text = f"[extract failed: {type(e).__name__}: {e}]"
        out.write(f"<<< Page {i + 1} >>>\n{text}\n\n")

    if args.out:
        out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
