"""Optionally pre-download Docling models for high-quality PDF conversion.

This script is NOT required to use the app. Skip it and keep
"PDF simple conversion" enabled in the GUI if download fails.
"""

from __future__ import annotations

import os
import sys
import time

from config import configure_runtime, docling_pdf_models_ready
from version import APP_NAME, __version__

configure_runtime()

MAX_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 5


def _download_with_endpoint(use_mirror: bool):
    if use_mirror:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print("ミラー経由: https://hf-mirror.com")
    else:
        os.environ.pop("HF_ENDPOINT", None)
        print("通常経由: https://huggingface.co")

    from docling.utils.model_downloader import download_models

    return download_models(
        progress=True,
        with_layout=True,
        with_tableformer=True,
        with_code_formula=True,
        with_picture_classifier=True,
        with_rapidocr=True,
        with_easyocr=False,
    )


def main() -> int:
    print(f"{APP_NAME} v{__version__}")
    print("Docling 高精度 PDF 用モデルをダウンロードします（任意）。")
    print("このスクリプトは必須ではありません。失敗しても app.py はそのまま使えます。")
    print("初回は Hugging Face から数 GB 取得するため、時間がかかることがあります。")
    print()

    if docling_pdf_models_ready():
        print("すでにモデルがインストール済みです。再ダウンロードは不要です。")
        return 0

    last_error: Exception | None = None
    routes = (False, True)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        for use_mirror in routes:
            print(f"--- 試行 {attempt}/{MAX_ATTEMPTS} ---")
            try:
                output_dir = _download_with_endpoint(use_mirror=use_mirror)
            except Exception as exc:
                last_error = exc
                print(f"失敗: {exc}")
                continue

            print()
            print(f"完了: {output_dir}")
            print("GUI で「PDF を簡易変換」のチェックを外すと高精度 PDF 変換が使えます。")
            return 0

        if attempt < MAX_ATTEMPTS:
            print(f"{RETRY_WAIT_SECONDS} 秒待って再試行します...")
            time.sleep(RETRY_WAIT_SECONDS)

    print()
    print("ダウンロードに失敗しました:")
    print(last_error)
    print()
    print("この環境では Hugging Face への安定接続が難しいようです。")
    print("PDF は GUI の「PDF を簡易変換」を ON のまま使ってください（モデル不要）。")
    print()
    print("高精度 PDF を使う場合の代替:")
    print("  1. スマホテザリングなど別回線で python setup_models.py")
    print("  2. 成功後はオフラインでも Docling PDF 変換が可能")
    print("  3. モデル保存先: %USERPROFILE%\\.cache\\docling\\models")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
