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
  * `inputs` / `outputs` : 参照ファイル・生成ファイル
  * `note` : 参考資料リンク
* JSON Schema を `schemas/instruction.schema.json` として提供し、`warifuri validate` で検証。

## 5. 担当種別の自動判定

* `*.sh` / `*.py` がある → **Machine タスク** (一時ディレクトリ + bash 実行)
* `prompt.yaml` がある → **AI タスク** (LLM 呼び出し)
* どちらも無い → **Human タスク** (手動作業)

## 6. 補助ファイル

* `done.md` : **空でも可**。存在 = 完了。
* `auto_merge.yaml` : PR 自動マージ許可フラグ。
* `logs/failed_<timestamp>.log` : Machine 実行失敗ログ。

## 7. コマンド一覧

* `warifuri init` : プロジェクト / タスク / テンプレ生成。
* `warifuri list` : タスク状態一覧表示。
* `warifuri run` : ready 自動実行・プロジェクト実行・直接実行。
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
* **ブランチ規約** : `project/task/<feature>`
* **PR 完了基準** : `done.md` を含むこと。
* **自動マージ** : `auto_merge.yaml` があり CI Green → Actions でマージ。

## 9. セーフティ機構（ライト版）

* **一時ディレクトリ実行** : Machine タスクは `mktemp -d` で隔離し、コピー後に `bash` 実行。
* **bash -euo pipefail** : `.sh` 実行時に安全フラグを強制。
* **ログ標準化** : `logs/YYYYMMDD_<task>.log` に出力を保存。
* **循環依存検知** : `warifuri validate` が依存ループを検出。
* **done.md の簡素仕様** : 空で OK、自動実行時のみ SHA や TIMESTAMP を記録。
* **Strict schema チェック** : `validate --strict` で誤記や不明キーをエラー検出。

> **キャッシュによる高速走査は将来検討**：パフォーマンスは向上するが、整合性のズレや更新漏れリスクがあり、MVP では導入しない。
