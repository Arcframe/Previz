# Previz
# Previz

## PPTX Font Replacement Utility

This repository includes `convert_pptx_fonts.py`, a small helper script that
rewrites every font reference inside a PowerPoint (`.pptx`) file.  It is useful
when slide masters or theme definitions keep reverting to an old typeface even
after running **Replace Fonts** inside PowerPoint.

### Requirements

- Python 3.8 or later (only the Python standard library is used)
- The target font (``Noto Sans KR`` by default) must be installed on the
  machine that will open the updated presentation

### Basic usage

```bash
python convert_pptx_fonts.py path/to/presentation.pptx
```

The command above replaces every `typeface` attribute with **Noto Sans KR** and
updates the original file in-place.

### Custom font or output file

- Use `--font` to supply a different typeface name:

  ```bash
  python convert_pptx_fonts.py path/to/presentation.pptx --font "Arial"
  ```

- Use `--output` when you prefer to save the converted copy to a new file
  instead of overwriting the source:

  ```bash
  python convert_pptx_fonts.py path/to/presentation.pptx \
      --output path/to/output.pptx
  ```

### How it works

1. The script opens the PowerPoint file as a zip archive.
2. Every XML file is scanned for `typeface` attributes.
3. Any existing value is replaced with the requested font name.
4. The XML is written back and a fresh `.pptx` archive is assembled.

> 💡 Tip: keep a backup of the original presentation before running the script,
> or simply use `--output` to create a separate copy.
