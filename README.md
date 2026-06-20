# Document MD Converter (Docling)

**Version 0.9.0** · **Author: Kaboss**

Docling を使った、ローカル実行の Markdown 変換デスクトップアプリです。  
PDF / Word / PowerPoint / Excel / HTML / 画像などを Markdown に変換し、プレビュー・保存できます。

## 特徴

- **GUI** — CustomTkinter ベースのシンプルな操作
- **ドラッグ＆ドロップ** — ファイルをウィンドウや一覧へドロップして追加
- **一括変換** — 複数ファイルをまとめて処理
- **Markdown プレビュー** — 変換結果をその場で確認
- **自動保存** — 出力フォルダへ `.md` を書き出し
- **PDF 簡易変換** — Hugging Face 不要（`pymupdf4llm`）
- **PDF 高精度変換** — Docling + AI モデル（初回モデル取得が必要）

## 対応形式

| 入力 | 拡張子 |
|------|--------|
| PDF | `.pdf` |
| Word | `.docx` |
| PowerPoint | `.pptx` |
| Excel | `.xlsx` |
| HTML | `.html`, `.htm` |
| Markdown | `.md` |
| 画像 | `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`, `.webp`, `.gif` |

## 前提条件

本アプリを動かすために必要な環境です。

| 項目 | 要件 |
|------|------|
| **作者** | **Kaboss** |
| **本アプリ** | **Document MD Converter (Docling) v0.9.0** |
| **Python** | **3.10 以上 4.0 未満**（**3.11 推奨**）。3.9 以下は非対応 |
| **OS** | **Windows 10 / 11**（開発・確認環境）。Linux / macOS でも Python があれば動作見込み |
| **pip** | Python に同梱、または別途インストール済みであること |
| **ディスク空き** | **約 5 GB 以上** 推奨（venv + パッケージ。高精度 PDF モデル追加時は **+2〜5 GB**） |
| **メモリ** | **8 GB 以上** 推奨（4 GB でも動作する場合あり。大きな PDF は時間がかかります） |
| **GPU** | **不要**（CPU のみで動作） |
| **画面** | GUI 表示のためデスクトップ環境が必要（解像度 1280×720 以上推奨） |
| **ネットワーク** | **初回のみ必要**（`pip install` など。詳細は下記） |

### Python の確認

```powershell
python --version
```

`Python 3.10.x` 〜 `3.13.x` などが表示されれば OK です。

Python が未インストールの場合は [python.org](https://www.python.org/downloads/) から取得してください。  
Windows ではインストール時に **「Add python.exe to PATH」** にチェックを入れることを推奨します。

### その他の注意

- **tkinter** — GUI に使用。Windows の公式 Python には通常同梱されています
- **Hugging Face への接続** — 高精度 PDF 変換または `setup_models.py` 利用時のみ必要（**必須ではありません**）
- **管理者権限** — 通常は不要（ユーザー権限で venv 作成・実行可能）

## 動作環境

- **ネットワーク:** 初回セットアップ時に大きめの通信が発生します（下記）。2 回目以降はオフラインでも利用可能です

### 初回実行時の通信量について

初めて使うとき、**インストールや変換のタイミングで数百 MB〜数 GB 程度** のダウンロードが発生することがあります。  
**料金は基本的に通信量のみ**（パッケージ・モデル自体は無料）です。

| タイミング | 目安 | 内容 |
|-----------|------|------|
| `pip install` 初回 | **約 1〜3 GB** | Python パッケージ（PyTorch、Docling など） |
| アプリ初回起動〜初回変換 | 小〜中 | Docling 関連の追加データ（形式による） |
| PDF 簡易変換 | **ほぼなし** | 追加ダウンロードは通常不要 |
| `setup_models.py` 実行時 | **約 2〜5 GB** | Hugging Face から AI モデル（任意・高精度 PDF 向け） |
| PDF OCR を ON にした場合 | **数十〜100 MB 程度** | OCR 用モデル（RapidOCR など） |

> **ポイント:** `setup_models.py` は実行不要です。PDF はデフォルトの **簡易変換** なら、大きなモデル取得を避けられます。  
> モデルやパッケージは PC にキャッシュされるため、**同じ環境では 2 回目以降の通信は大幅に減ります**。

## セットアップ（最低限）

`setup_models.py` は **実行不要** です。以下だけでアプリを使えます。

```powershell
git clone https://github.com/ka-Boss/DocumentMDConverter-Docling-.git
cd DocumentMDConverter-Docling-

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

> Linux / macOS の場合は `source .venv/bin/activate` を使用してください。  
> Windows では `run.bat` のダブルクリックでも起動できます。

### 事前準備の一覧

| 手順 | 必須？ | 説明 |
|------|--------|------|
| `pip install -r requirements.txt` | **必須** | パッケージのインストール（初回は大容量通信あり） |
| `python app.py` | **必須** | アプリの起動 |
| `python setup_models.py` | **任意** | 高精度 PDF 用 AI モデルの事前取得（数 GB・任意） |

## 使い方

### 起動

```powershell
python app.py
```

### 基本操作

1. **ファイル追加** ボタンでファイルを選ぶ  
   **または** 左ペイン / プレビュー領域へ **ドラッグ＆ドロップ**
2. 必要なら **出力先フォルダ** を変更（デフォルト: `./output`）
3. オプションを確認（下記）
4. **変換開始** をクリック
5. 右側プレビューで確認し、必要なら **Markdown を保存**

### PDF 変換モード

| モード | 設定 | 説明 |
|--------|------|------|
| **簡易変換（推奨）** | 「PDF を簡易変換」ON | モデル不要。テキスト中心の PDF 向け |
| **高精度変換** | 「PDF を簡易変換」OFF | Docling 使用。表・レイアウト認識が強い |
| **OCR** | 「PDF に OCR を使用」ON | スキャン PDF 向け（高精度モード + モデル必要） |

デフォルトでは **「PDF を簡易変換」が ON** です。`setup_models.py` を実行しなくても PDF を含めて変換できます。

### `setup_models.py`（任意・高精度 PDF 向け）

**必須ではありません。** 表やレイアウトの認識精度を上げたい PDF 変換を使う場合だけ、事前に実行してください。

```powershell
python setup_models.py
```

- Hugging Face から AI モデル（数 GB）をダウンロードします
- 失敗してもアプリは **簡易 PDF 変換** で引き続き利用できます
- 成功後は GUI で「PDF を簡易変換」のチェックを外すと高精度 PDF 変換が使えます

モデル保存先（Windows）:

```
%USERPROFILE%\.cache\docling\models
```

## プロジェクト構成

```
.
├── version.py             # アプリバージョン（0.9.0）
├── app.py                 # GUI アプリ
├── converter.py           # 変換ロジック
├── config.py              # 環境設定・エラー判定
├── setup_models.py        # 高精度 PDF 用モデル事前取得（任意）
├── requirements.txt
├── run.bat                # Windows 起動用
├── samples/               # 動作確認用サンプル
├── LICENSE
├── THIRD_PARTY_NOTICES.md
└── README.md
```

## トラブルシューティング

### Hugging Face 接続エラー（`WinError 10054` など）

`setup_models.py` や高精度 PDF 変換時に発生することがあります。  
**`setup_models.py` は必須ではない** ため、エラーが出てもアプリ本体は使えます。

**対処:**

1. **そのまま使う** — GUI で **「PDF を簡易変換」を ON** のまま（推奨）
2. 高精度 PDF が必要な場合のみ、別回線（テザリング等）で `python setup_models.py` を再実行
3. ミラーを試す:

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
python setup_models.py
```

### ドラッグ＆ドロップが効かない

- `tkinterdnd2` がインストールされているか確認: `pip install tkinterdnd2`
- 対応形式以外のファイルは追加されません

### 変換が遅い

- PDF 高精度モードの初回はモデル取得で時間がかかります
- CPU のみでも動作しますが、大きな PDF は時間がかかることがあります

## ライセンス

本プロジェクトは [GNU Affero General Public License v3.0](LICENSE) の下で公開されています。

PyMuPDF / pymupdf4llm（AGPL-3.0）を PDF 簡易変換に使用しているため、配布時は AGPL に従う必要があります。  
商用利用で AGPL を避けたい場合は、PyMuPDF の [商用ライセンス](https://pymupdf.readthedocs.io/en/latest/about.html) を Artifex から取得してください。

第三者ライセンスの詳細は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。

## 謝辞

- [Docling](https://github.com/docling-project/docling) — ドキュメント変換エンジン（MIT）
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — GUI フレームワーク
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF 簡易変換
- [tkinterdnd2](https://github.com/petasis/tkinterdnd2) — ドラッグ＆ドロップ

## 免責

本ソフトウェアは個人プロジェクトとして提供されています。変換結果の正確性は保証されません。重要な文書は必ず原本と照合してください。
