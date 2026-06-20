"""Docling-based document to Markdown conversion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import (
    configure_runtime,
    format_conversion_error,
    is_network_error,
    should_skip_docling_for_pdf,
    docling_pdf_models_ready,
)

configure_runtime()

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".html",
    ".htm",
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".gif",
}

FILE_DIALOG_TYPES = [
    ("対応形式", " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))),
    ("すべてのファイル", "*.*"),
]


@dataclass(frozen=True)
class ConversionResult:
    source: Path
    markdown: str
    output_path: Path | None = None
    used_fallback: bool = False


def convert_pdf_fallback(source: Path) -> str:
    import pymupdf4llm

    markdown = pymupdf4llm.to_markdown(str(source))
    notice = (
        "<!-- PDF 簡易変換モード: Docling モデル取得不可のため pymupdf4llm で変換 -->\n\n"
    )
    return notice + markdown


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def _pdf_format_option(enable_ocr: bool):
    from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
    from docling.document_converter import PdfFormatOption

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = enable_ocr
    if enable_ocr:
        pipeline_options.ocr_options = RapidOcrOptions(lang=["english", "chinese"])

    return PdfFormatOption(pipeline_options=pipeline_options)


def create_converter(enable_ocr: bool = False):
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter

    return DocumentConverter(
        format_options={
            InputFormat.PDF: _pdf_format_option(enable_ocr=enable_ocr),
        }
    )


def _convert_with_docling(source: Path, *, enable_ocr: bool) -> str:
    converter = create_converter(enable_ocr=enable_ocr)
    result = converter.convert(str(source))
    return result.document.export_to_markdown()


def _should_use_pdf_fallback(exc: BaseException) -> bool:
    if isinstance(exc, (FileNotFoundError, PermissionError, ValueError)):
        return False
    if is_network_error(exc):
        return True
    return not docling_pdf_models_ready()


def convert_to_markdown(
    source: Path,
    *,
    enable_ocr: bool = False,
    force_simple_pdf: bool = False,
    output_dir: Path | None = None,
) -> ConversionResult:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"ファイルが見つかりません: {source}")
    if not is_supported(source):
        raise ValueError(f"未対応の形式です: {source.suffix}")

    used_fallback = False
    is_pdf = source.suffix.lower() == ".pdf"

    if is_pdf and should_skip_docling_for_pdf(force_simple=force_simple_pdf):
        markdown = convert_pdf_fallback(source)
        used_fallback = True
    else:
        try:
            markdown = _convert_with_docling(source, enable_ocr=enable_ocr)
        except Exception as exc:
            if is_pdf and _should_use_pdf_fallback(exc):
                markdown = convert_pdf_fallback(source)
                used_fallback = True
            else:
                raise RuntimeError(format_conversion_error(exc)) from exc

    output_path = None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{source.stem}.md"
        output_path.write_text(markdown, encoding="utf-8")

    return ConversionResult(
        source=source,
        markdown=markdown,
        output_path=output_path,
        used_fallback=used_fallback,
    )
