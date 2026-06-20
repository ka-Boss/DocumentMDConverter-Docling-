"""Document MD Converter (Docling) - Desktop GUI."""

from __future__ import annotations

import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from config import configure_runtime, docling_pdf_models_ready
from converter import (
    FILE_DIALOG_TYPES,
    SUPPORTED_EXTENSIONS,
    ConversionResult,
    convert_to_markdown,
    is_supported,
)
from version import APP_NAME, __version__

APP_TITLE = f"{APP_NAME} v{__version__}"
WINDOW_SIZE = "1100x720"


def parse_dropped_paths(data: str) -> list[Path]:
    data = data.strip()
    if not data:
        return []

    if data.startswith("{"):
        raw_paths = re.findall(r"\{([^}]+)\}", data)
    else:
        raw_paths = data.split()

    return [Path(path) for path in raw_paths if path.strip()]


class DoclingMdApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self) -> None:
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(900, 600)

        self.input_files: list[Path] = []
        self.output_dir = Path.cwd() / "output"
        self.last_result: ConversionResult | None = None
        self._busy = False

        self._build_ui()
        self._setup_drag_and_drop()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=APP_TITLE,
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="PDF / Word / PowerPoint / Excel / HTML / 画像 などを Markdown に変換",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray70"),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        body = ctk.CTkFrame(self)
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=8)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body, width=320)
        left.grid(row=0, column=0, sticky="nsw", padx=(12, 8), pady=12)
        left.grid_propagate(False)

        right = ctk.CTkFrame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 12), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self._build_left_panel(left)
        self._build_right_panel(right)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 16))
        footer.grid_columnconfigure(0, weight=1)

        initial_status = "ファイルを選択するか、ドラッグ＆ドロップで追加してください"
        if not docling_pdf_models_ready():
            initial_status += "（PDF 高精度モデル未導入 → 簡易変換推奨）"

        self.status_label = ctk.CTkLabel(
            footer,
            text=initial_status,
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="ew")

        self.progress = ctk.CTkProgressBar(footer, mode="indeterminate")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.progress.grid_remove()

    def _build_left_panel(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            parent,
            text="入力ファイル",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(12, 6))

        ctk.CTkLabel(
            parent,
            text="ここへファイルをドラッグ＆ドロップ",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        ).pack(anchor="w", padx=12, pady=(0, 6))

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkButton(btn_row, text="ファイル追加", command=self._add_files, width=120).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            btn_row,
            text="クリア",
            command=self._clear_files,
            width=80,
            fg_color="transparent",
            border_width=1,
        ).pack(side="left")

        self.file_listbox = tk.Listbox(
            parent,
            height=12,
            selectmode=tk.EXTENDED,
            bg="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#f2f2f2",
            fg="#ffffff" if ctk.get_appearance_mode() == "Dark" else "#1a1a1a",
            highlightthickness=1,
            highlightbackground="#3a7ebf",
            borderwidth=0,
        )
        self.file_listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._drop_targets: list[tk.Misc] = [self, parent, self.file_listbox]

        ctk.CTkLabel(
            parent,
            text="出力先フォルダ",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(0, 6))

        output_row = ctk.CTkFrame(parent, fg_color="transparent")
        output_row.pack(fill="x", padx=12, pady=(0, 12))

        self.output_dir_var = tk.StringVar(value=str(self.output_dir))
        self.output_entry = ctk.CTkEntry(output_row, textvariable=self.output_dir_var)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(output_row, text="参照", width=60, command=self._pick_output_dir).pack(
            side="left"
        )

        ctk.CTkLabel(
            parent,
            text="オプション",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(0, 6))

        self.ocr_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            parent,
            text="PDF に OCR を使用（Docling・スキャンPDF向け）",
            variable=self.ocr_var,
        ).pack(anchor="w", padx=12, pady=(0, 6))

        self.simple_pdf_var = tk.BooleanVar(value=not docling_pdf_models_ready())
        ctk.CTkCheckBox(
            parent,
            text="PDF を簡易変換（モデル不要・推奨）",
            variable=self.simple_pdf_var,
        ).pack(anchor="w", padx=12, pady=(0, 6))

        self.auto_save_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            parent,
            text="変換後に出力フォルダへ自動保存",
            variable=self.auto_save_var,
        ).pack(anchor="w", padx=12, pady=(0, 12))

        ctk.CTkButton(
            parent,
            text="変換開始",
            height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_conversion,
        ).pack(fill="x", padx=12, pady=(0, 12))

        formats = ", ".join(sorted(ext.replace(".", "") for ext in SUPPORTED_EXTENSIONS))
        ctk.CTkLabel(
            parent,
            text=f"対応: {formats}",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            wraplength=280,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 12))

    def _build_right_panel(self, parent: ctk.CTkFrame) -> None:
        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        toolbar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            toolbar,
            text="Markdown プレビュー",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            toolbar,
            text="Markdown を保存",
            command=self._save_current_markdown,
            width=140,
        ).grid(row=0, column=1, sticky="e")

        self.preview = ctk.CTkTextbox(parent, wrap="word", font=ctk.CTkFont(family="Consolas", size=13))
        self.preview.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.preview.insert("1.0", "変換結果がここに表示されます。")
        self.preview.configure(state="disabled")
        self._drop_targets.append(parent)
        self._drop_targets.append(self.preview)

    def _setup_drag_and_drop(self) -> None:
        for widget in self._drop_targets:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event) -> None:
        if self._busy:
            messagebox.showinfo("変換中", "変換が完了するまでお待ちください。")
            return

        paths = parse_dropped_paths(event.data)
        added, skipped = self._register_paths(paths)

        if added:
            self._set_status(
                f"ドロップで {added} 件追加しました（合計 {len(self.input_files)} 件）"
            )
        elif skipped:
            messagebox.showwarning(
                "未対応",
                "ドロップされたファイルは未対応形式です。\n\n" + "\n".join(skipped[:5]),
            )

    def _register_paths(self, paths: list[Path]) -> tuple[int, list[str]]:
        added = 0
        skipped: list[str] = []

        for path in paths:
            path = path.resolve()
            if not path.is_file():
                continue
            if not is_supported(path):
                skipped.append(path.name)
                continue
            if path in self.input_files:
                continue
            self.input_files.append(path)
            self.file_listbox.insert(tk.END, str(path))
            added += 1

        return added, skipped

    def _add_files(self) -> None:
        paths = filedialog.askopenfilenames(title="変換するファイルを選択", filetypes=FILE_DIALOG_TYPES)
        if not paths:
            return

        added, skipped = self._register_paths([Path(raw_path) for raw_path in paths])

        if skipped:
            messagebox.showwarning(
                "未対応",
                "未対応の形式です:\n" + "\n".join(skipped[:5]),
            )
        if added:
            self._set_status(f"{added} 件のファイルを追加しました（合計 {len(self.input_files)} 件）")

    def _clear_files(self) -> None:
        self.input_files.clear()
        self.file_listbox.delete(0, tk.END)
        self._set_status("ファイル一覧をクリアしました")

    def _pick_output_dir(self) -> None:
        directory = filedialog.askdirectory(title="出力先フォルダを選択")
        if directory:
            self.output_dir = Path(directory)
            self.output_dir_var.set(directory)

    def _set_status(self, message: str) -> None:
        self.status_label.configure(text=message)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        if busy:
            self.progress.grid()
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.grid_remove()

    def _set_preview(self, text: str) -> None:
        self.preview.configure(state="normal")
        self.preview.delete("1.0", tk.END)
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _start_conversion(self) -> None:
        if self._busy:
            return
        if not self.input_files:
            messagebox.showinfo("ファイル未選択", "変換するファイルを追加してください。")
            return

        output_dir = Path(self.output_dir_var.get().strip()) if self.auto_save_var.get() else None
        if output_dir is not None and not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                messagebox.showerror("出力先エラー", f"出力フォルダを作成できません:\n{exc}")
                return

        self._set_busy(True)
        self._set_status(
            "変換中... PDF の初回はモデル取得で数分かかることがあります"
        )

        thread = threading.Thread(
            target=self._convert_worker,
            args=(
                list(self.input_files),
                output_dir,
                self.ocr_var.get(),
                self.simple_pdf_var.get(),
            ),
            daemon=True,
        )
        thread.start()

    def _convert_worker(
        self,
        files: list[Path],
        output_dir: Path | None,
        enable_ocr: bool,
        force_simple_pdf: bool,
    ) -> None:
        results: list[ConversionResult] = []
        errors: list[str] = []

        for index, path in enumerate(files, start=1):
            self.after(
                0,
                lambda i=index, total=len(files), name=path.name: self._set_status(
                    f"変換中 ({i}/{total}): {name}"
                ),
            )
            try:
                result = convert_to_markdown(
                    path,
                    enable_ocr=enable_ocr,
                    force_simple_pdf=force_simple_pdf,
                    output_dir=output_dir,
                )
                results.append(result)
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")

        self.after(0, lambda: self._conversion_finished(results, errors))

    def _conversion_finished(
        self,
        results: list[ConversionResult],
        errors: list[str],
    ) -> None:
        self._set_busy(False)

        if results:
            self.last_result = results[-1]
            self._set_preview(self.last_result.markdown)

        saved = sum(1 for item in results if item.output_path is not None)
        fallback_count = sum(1 for item in results if item.used_fallback)
        message_parts = [f"成功: {len(results)} 件"]
        if saved:
            message_parts.append(f"保存: {saved} 件")
        if fallback_count:
            message_parts.append(f"簡易変換: {fallback_count} 件")
        if errors:
            message_parts.append(f"失敗: {len(errors)} 件")

        self._set_status(" / ".join(message_parts))

        if errors:
            messagebox.showwarning(
                "一部失敗",
                "以下のファイルは変換できませんでした:\n\n" + "\n".join(errors),
            )
        elif results:
            last = results[-1]
            detail = f"{len(results)} 件の変換が完了しました。"
            if any(item.used_fallback for item in results):
                detail += (
                    "\n\nPDF は Hugging Face 接続不可のため簡易変換を使用しました。"
                    "\n高精度変換には setup_models.py でモデル取得が必要です。"
                )
            if last.output_path:
                detail += f"\n\n最新: {last.output_path}"
            messagebox.showinfo("変換完了", detail)

    def _save_current_markdown(self) -> None:
        if not self.last_result:
            messagebox.showinfo("保存不可", "保存する Markdown がありません。先に変換を実行してください。")
            return

        default_name = f"{self.last_result.source.stem}.md"
        save_path = filedialog.asksaveasfilename(
            title="Markdown を保存",
            defaultextension=".md",
            initialfile=default_name,
            filetypes=[("Markdown", "*.md"), ("すべて", "*.*")],
        )
        if not save_path:
            return

        Path(save_path).write_text(self.last_result.markdown, encoding="utf-8")
        self._set_status(f"保存しました: {save_path}")
        messagebox.showinfo("保存完了", f"保存しました:\n{save_path}")


def main() -> None:
    configure_runtime()
    app = DoclingMdApp()
    app.mainloop()


if __name__ == "__main__":
    main()
