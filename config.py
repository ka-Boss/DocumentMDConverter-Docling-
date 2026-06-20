"""Shared environment and error helpers."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

_HF_REACHABLE: bool | None = None


def configure_runtime() -> None:
    """Apply settings that improve model download reliability."""
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "300")
    os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "300")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def iter_exceptions(exc: BaseException) -> Iterator[BaseException]:
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def is_network_error(exc: BaseException) -> bool:
    markers = (
        "10054",
        "connection",
        "connecterror",
        "timeout",
        "timed out",
        "remote host",
        "network",
        "huggingface",
        "hf hub",
        "ssl",
        "reset",
        "hub",
        "disconnected",
        "without sending a response",
        "server disconnected",
        "snapshot folder",
        "locate the files on the hub",
    )
    type_markers = ("connect", "timeout", "protocol", "remote", "network", "urllib")

    for item in iter_exceptions(exc):
        message = str(item).lower()
        if any(marker in message for marker in markers):
            return True
        class_name = item.__class__.__name__.lower()
        if any(marker in class_name for marker in type_markers):
            return True

    return False


def format_conversion_error(exc: BaseException) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    if is_network_error(exc):
        return (
            f"{message}\n"
            "Hugging Face への接続に失敗しました。"
            "PDF は簡易変換に切り替えるか、ネットワーク修復後に setup_models.py を実行してください。"
        )
    return message


def huggingface_reachable(timeout: float = 5.0) -> bool:
    global _HF_REACHABLE
    if _HF_REACHABLE is not None:
        return _HF_REACHABLE

    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen("https://huggingface.co", timeout=timeout) as response:
            _HF_REACHABLE = response.status < 500
    except (urllib.error.URLError, TimeoutError, OSError):
        _HF_REACHABLE = False

    return _HF_REACHABLE


def docling_pdf_models_ready() -> bool:
    try:
        from docling.datamodel.pipeline_options import LayoutOptions
        from docling.datamodel.settings import settings

        layout_dir = (
            settings.cache_dir / "models" / LayoutOptions().model_spec.model_repo_folder
        )
        return layout_dir.is_dir() and any(layout_dir.iterdir())
    except Exception:
        return False


def should_skip_docling_for_pdf(*, force_simple: bool = False) -> bool:
    """Use pymupdf when simple mode is enabled."""
    return force_simple
