# 📐 warifuri 設計ドキュメント (v1.2)

## 1. 目的

* 人間・AI・マシンが **同じ Git リポジトリ** 上でタスクを割り振り合うための最小 CLI を提供する。
* **ファイル = 真実** を徹底し、データベースや専用サーバーに依存しない。
* コマンド数を絞り込みつつ、後から容易に拡張できる構造にする。

## 2. 基本方針

* **State‑less** : `done.md` があれば完了、無ければ未完。
* **Dependency‑driven** : 実行順序は `instruction.yaml` の `dependencies` のみで決定。
* **Role‑free** : タスク担当は存在ファイルで自動判定（Machine = スクリプト、AI = `prompt.yaml`、Human = どちらも無）。
* **Safety First** : ライトな保護機構（サンドボックス実行、循環検知、ログ保存など）で壊れにくくする。
* **Re‑Use** : プロジェクト横断テンプレートでタスク雛形を再利用。

## 3. ディレクトリ構成

* `workspace/` : 作業ルート（Git リポジトリ）

  * `projects/<project>/<task>/` : 実タスク

    * `instruction.yaml`
    * `run.sh` または `prompt.yaml` など
    * `done.md`
    * `auto_merge.yaml` (任意)
  * `templates/<template>/<tpl-task>/` : テンプレート雛形
* `docs/` : ドキュメント（任意）
* `warifuri/` : CLI 本体コード

## 4. instruction.yaml スキーマ

* 必須フィールド

  * `name` : タスク識別子（ディレクトリ名と一致）
  * `description` : タスク説明（ファイル末尾に配置）
* 任意フィールド

  * `dependencies` : 依存タスク一覧
  * `inputs` / `outputs` : 参照ファイル・生成ファイル。主目的はドキュメント用途だが、`warifuri validate` でのファイル存在チェックにも使用される。将来的には自動依存解決や再実行検知のヒントになる可能性も考慮。
  * `note` : 参考資料リンクやメモ。`warifuri show` で表示される。LLMプロンプトの拡張素材やレビュー時の参考情報としての活用を想定。
* JSON Schema を `schemas/instruction.schema.json` として提供し、`warifuri validate` で検証。
* **スキーマファイルの参照順序**:
    1. `workspace/schemas/instruction.schema.json` が存在すればそれを優先的に使用。
    2. 上記が存在しない場合は、`warifuri` パッケージにバンドルされた組み込みスキーマ (`warifuri/schemas/embedded/`) で検証。

## 5. 担当種別の自動判定

* `*.sh` / `*.py` がある → **Machine タスク**
    * 実行時、タスクディレクトリ (`projects/<project>/<task>/`) 全体が一時ディレクトリ (`tmpdir/`) にコピーされる。
    * スクリプトは、カレントディレクトリを一時ディレクトリ (`tmpdir/`) とした上で `bash -euo pipefail run.sh` (または `python run.py`) のように実行される。
    * スクリプト内からは、`input/` ディレクトリ内のファイルなどを相対パスで参照可能。`output/` ディレクトリに成果物を書き出す。
    * **成果物のコピーバック**: タスク実行後、`instruction.yaml` の `outputs` フィールドに指定されたファイルパスに基づき、`tmpdir/` 内の該当ファイルが元のタスクディレクトリ（例: `projects/<project>/<task>/output/`）に自動的にコピーバックされる。`outputs` に明示されていないファイルはコピーバックされない。
    * **環境変数**: スクリプト実行時、以下の標準環境変数が提供される。
        * `WARIFURI_PROJECT_NAME`: タスクが所属するプロジェクト名。
        * `WARIFURI_TASK_NAME`: 実行されるタスク名。
        * `WARIFURI_WORKSPACE_DIR`: `warifuri` コマンドが実行されたワークスペースの絶対パス。
        * `WARIFURI_INPUT_DIR`: スクリプトのカレントディレクトリ（一時タスクディレクトリ）からの相対的な入力ディレクトリパス (通常は "input")。
        * `WARIFURI_OUTPUT_DIR`: スクリプトのカレントディレクトリ（一時タスクディレクトリ）からの相対的な出力ディレクトリパス (通常は "output")。
* `prompt.yaml` がある → **AI タスク** (詳細は「5.1 AI タスクの実行詳細」を参照)
* どちらも無い → **Human タスク** (詳細は「5.2 Human タスクの実行詳細」を参照)

### 5.1 AI タスクの実行詳細

* **プロンプト構築**:
    * `prompt.yaml` に定義された `system_prompt` と、`instruction.yaml` の `description` を結合して LLM への指示プロンプトとする。
    * 将来的には `instruction.yaml` の `inputs` や `note` の内容もプロンプトテンプレート変数として組み込めるようにする拡張を検討。
* **レスポンス処理**:
    * LLM からのレスポンスは、タスクディレクトリ内の `output/response.md` に Markdown 形式で保存される（任意）。
* **エラーハンドリング**:
    * API接続失敗、レート制限、コンテンツフィルタリングなどのエラーが発生した場合、`logs/failed_<timestamp>.log` にリクエスト内容、エラーレスポンス、スタックトレース（必要な場合）などを記録する。
    * エラー発生時は `done.md` は作成されず、`warifuri run` コマンドは 0 以外の終了コードを返す。

### 5.2 Human タスクの実行詳細

* `warifuri run` を Human タスクに対して実行した場合、スクリプトもプロンプトファイルも存在しないため、以下の動作となる。
    * ターミナルに「このタスクは Human タスクです。手動で対応してください」といった趣旨のメッセージを出力する。
    * 終了コード 0 で正常終了する。ファイルへの変更は行わない。

## 6. 補助ファイル

* `done.md` : **空でも可**。存在 = 完了。warifuri はファイルの存在のみで完了と判定する。
    * **推奨追記フォーマット (Machine/AIタスク自動生成時)**: `YYYY-MM-DD HH:MM:SS SHA: <commit_sha>` (例: `2025-05-26 13:12:09 SHA: abcd1234ef5678901234567890abcdef12345678`)。これは1行のテキスト形式で、人間が読みやすく、将来的なパースも考慮している。YAML形式や複数行の構文はv1.2では不要だが、将来バージョンで導入の余地あり。
* `auto_merge.yaml` : PR 自動マージ許可フラグ。**v1.2時点では空のマーカーファイルとして機能し、ファイルが存在するだけで有効となる。中身は一切評価されない。**
    * 将来的な拡張構想 (v1.3以降) として、YAMLファイル内に特定の条件（例: `only_if_label: auto`, `only_on_branch: main`）を記述する案も検討されているが、v1.2では非対応。
* `logs/failed_<timestamp>.log` : Machine タスクおよび AI タスク実行失敗時のログ。

## 6.x ロギング戦略（最小版）

### 6.x.1 目的
* デバッグとエラー診断を低コストで可能にする。

### 6.x.2 実装方針
* **Python 標準 `logging`** を利用。
  ```python
  import logging, os

  LOG_LEVEL = os.getenv("WARIFURI_LOG_LEVEL", "INFO").upper()
  logging.basicConfig(
      level=LOG_LEVEL,
      format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
      datefmt="%Y-%m-%d %H:%M:%S",
  )
  logger = logging.getLogger("warifuri")
  ```

* ログ出力は **stderr** のみ（ファイル保存は将来検討）。

### 6.x.3 ログレベル制御

* グローバル CLI オプション `--log-level <LEVEL>` を追加。
  * 指定がない場合は上記 `LOG_LEVEL`（環境変数→既定 INFO）のまま。
  * 受け付ける `<LEVEL>`: `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL`.
* `-v`, `-vv` は v1.3 で検討。

### 6.x.4 使用例

```bash
# 通常実行（INFO）
warifuri run

# 詳細デバッグ
warifuri run --log-level DEBUG

# CI などで静かに
WARIFURI_LOG_LEVEL=ERROR warifuri run
```

## 7. コマンド一覧

* `warifuri init` : プロジェクト / タスク / テンプレ生成。
* `warifuri list` : タスク状態一覧表示。
* `warifuri run` : ready 自動実行・プロジェクト実行・直接実行。
    * `--force` オプション: 依存タスクが未完了 (`done.md` が存在しなくても) の場合や、自タスクの `done.md` が既に存在する場合でも強制的に再実行する。主に再実行テストや開発中のデバッグ用途。
* `warifuri show` : タスク定義＆メタ表示。
* `warifuri validate` : 構文＋依存検証。
* `warifuri graph` : 依存グラフ生成 (Mermaid / HTML / ASCII)。
* `warifuri mark-done` : `done.md` を手動作成。
* `warifuri template list` : テンプレート一覧。
* `warifuri issue` : GitHub Issue 起票（親 / 子 / 一括）。

## 8. GitHub 連携のポイント

* **Issue タイトル規約**

  * 親 : `[PROJECT] <project>`
  * 子 : `[TASK] <project>/<task>`
* **Issue の重複判定**: `warifuri issue --all-tasks` 実行時、GitHub CLI (`gh issue list`) を使用して、既存の `[TASK] <project>/<task>` というタイトルの Issue が存在するかどうかを確認する。存在する場合は、そのタスクの Issue 作成はスキップされる。
* **ブランチ規約** : `project/task/YYYYMMDDHHMM/NNN`。`NNN` は同日内での連番で、ユーザーが手動で採番する（CLIによる自動採番支援は現時点ではなし）。
* **PR 完了基準** : `done.md` を含むこと。
* **自動マージ** : 以下の条件をすべて満たす場合に Actions で自動マージされる。
    1. `auto_merge.yaml` がプルリクエストの変更差分に含まれている。
    2. 関連する GitHub Actions ワークフローがすべて `success` (終了コード 0) で完了している。
    3. 上記ワークフローには、`warifuri validate` のチェックが含まれ、それが成功していること。

## 9. セーフティ機構（ライト版）

* **一時ディレクトリ実行** : Machine タスクは `mktemp -d` で隔離し、コピー後に `bash` 実行。
* **bash -euo pipefail** : `.sh` 実行時に安全フラグを強制。
* **ログ標準化** : Machine タスクおよび AI タスクの実行ログ（成功時・失敗時）を `logs/` ディレクトリに保存。失敗時は `logs/failed_<timestamp>.log` に詳細情報を記録。
* **循環依存検知** : `warifuri validate` が依存ループを検出。
* **done.md の簡素仕様** : 空で OK、自動実行時のみ SHA や TIMESTAMP を記録。
* **Strict schema チェック** : `validate --strict` で誤記や不明キーをエラー検出。

## 10. テンプレート機能の詳細

* **プレースホルダー置換**:
    * 現行の `warifuri init --template` では、テンプレートファイル内のプレースホルダー（例: `{{TASK_NAME}}`）を実際のタスク名などで置換する機能は未対応。
    * 将来的には、YAMLファイルのヘッダーやREADMEファイル内などで簡易的なテンプレート置換機能を追加する余地あり。
* **テンプレート内の依存関係の維持**:
    * 複数のタスク雛形を含むテンプレート（例: `templates/my_workflow/task_A`, `templates/my_workflow/task_B`）を `warifuri init --template my_workflow` のように展開した場合、各タスクの `instruction.yaml` 内に記述された `dependencies` はそのまま維持される。
    * テンプレート内のタスク間での相対的な依存関係は、ファイルがそのままコピーされるため壊れない。

> **キャッシュによる高速走査は将来検討**：パフォーマンスは向上するが、整合性のズレや更新漏れリスクがあり、MVP では導入しない。
