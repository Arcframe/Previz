import argparse
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET


def replace_font_in_xml(xml_path: Path, new_font: str) -> bool:
    """Replace all typeface attributes in a single XML file."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError:
        return False

    root = tree.getroot()
    replaced = False

    for elem in root.iter():
        attribs = list(elem.attrib.items())
        for attr_key, attr_val in attribs:
            if attr_key.startswith("{"):
                attr_name = attr_key.split("}", 1)[1]
            else:
                attr_name = attr_key

            if attr_name == "typeface" and attr_val != new_font:
                elem.set(attr_key, new_font)
                replaced = True

    if replaced:
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    return replaced


def convert_pptx_fonts(source_pptx: Path, output_pptx: Path, new_font: str) -> None:
    if not source_pptx.exists():
        raise FileNotFoundError(f"Source PPTX file not found: {source_pptx}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        with zipfile.ZipFile(source_pptx, "r") as pptx_zip:
            pptx_zip.extractall(tmp_path)

        for xml_file in tmp_path.rglob("*.xml"):
            replace_font_in_xml(xml_file, new_font)

        if output_pptx.exists():
            os.remove(output_pptx)

        with zipfile.ZipFile(output_pptx, "w", zipfile.ZIP_DEFLATED) as new_zip:
            for file_path in sorted(tmp_path.rglob("*")):
                if file_path.is_file():
                    archive_name = file_path.relative_to(tmp_path)
                    new_zip.write(file_path, arcname=str(archive_name))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace all fonts in a PPTX file with a specified font by editing XML contents."
    )
    parser.add_argument("source", type=Path, help="Path to the source PPTX file")
    parser.add_argument(
        "-f",
        "--font",
        default="Noto Sans KR",
        help="Font name to replace all typefaces with (default: Noto Sans KR)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional path for the output PPTX file (default: overwrite source)",
    )

    args = parser.parse_args()

    source = args.source
    output = args.output if args.output else source

    # If we overwrite the source file, save to temp file first
    if output == source:
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp_output:
            tmp_output_path = Path(tmp_output.name)
        try:
            convert_pptx_fonts(source, tmp_output_path, args.font)
            shutil.move(tmp_output_path, source)
        finally:
            if tmp_output_path.exists():
                tmp_output_path.unlink(missing_ok=True)
    else:
        convert_pptx_fonts(source, output, args.font)


if __name__ == "__main__":
    main()
