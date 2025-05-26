# 📑 warifuri 要件定義書 (v1.2)

## 1. 目的と背景

 目的: GitHub リポジトリ上で人間・AI・マシンがタスクを“割り振り”できる最小 CLI を提供する。
 背景: 従来の PM ツールは DB や Web UI が重い。ファイル構造だけで完結し、GitHub Issue / PR と自然に連携できるワークフローが求められる。

## 2. 基本原則

 State‑less: `done.md` の存在だけで完了判定。
 Dependency‑driven: 実行可否は `dependencies` のみで決定。
 Role‑free: `run.sh` / `.py` / `prompt.yaml` の有無で担当を自動判定。
 Safety First: tmpdir 実行・`bash -euo pipefail`・循環依存検知で壊れにくく。
 Re‑Use: プロジェクト横断テンプレートでタスク雛形を再利用。

## 3. 標準ディレクトリ構成

```
workspace/
├─ projects/<project>/<task>/
│   instruction.yaml
│   run.sh | prompt.yaml …
│   done.md
│   auto_merge.yaml (任意)
├─ templates/<template>/<tpl-task>/
│   instruction.yaml
│   run.sh …
├─ docs/            # 任意
└─ warifuri/        # CLI 本体
```

> 命名ルール: タスク名に順序番号を付けない（順序は依存で決まる）。

## 4. instruction.yaml スキーマ

 必須: `name`, `description`
 任意: `dependencies`, `inputs`, `outputs`, `note`
 JSON Schema は `schemas/instruction.schema.json` で提供。

## 5. 担当種別の自動判定

| 優先 | 存在ファイル          | 担当      | 実行方法                             |
| -- | --------------- | ------- | -------------------------------- |
| 1  | `.sh` / `.py` | Machine | tmpdir + `bash -euo pipefail`    |
| 2  | `prompt.yaml`   | AI      | LLM へ送信し `output/response.md` 保存 |
| 3  | なし              | Human   | warifuri は 0 exit（手動対応）          |

## 6. 補助ファイル

 `done.md`: 空でも可。存在 = 完了。自動実行時は日時・SHA を追記。
 `auto_merge.yaml`: PR 自動マージを許可するフラグ。
 `logs/failed_<ts>.log`: Machine 実行失敗時のログ。

## 7. CLI コマンド一覧

| コマンド                     | 機能概要                                                                                                                                                        |       |                  |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ---------------- |
| `warifuri init`          | プロジェクト／タスク生成・テンプレ展開 (`--template`, `--force`, `--dry-run`)                                                                                                  |       |                  |
| `warifuri list`          | タスク一覧 (`--ready`, `--completed`, `--project`, `--format`, `--fields`)                                                                                       |       |                  |
| `warifuri run`           | タスク実行  • 引数なし: ready タスクを1件自動実行  • `--task <proj>`: プロジェクト内 ready を1件実行  • `--task <proj>/<task>`: 指定タスク実行 (`--dry-run`, `--force`)                         |       |                  |
| `warifuri show`          | タスク定義／メタ表示 (`--task`, `--format`)                                                                                                                           |       |                  |
| `warifuri validate`      | 構文 + 循環依存 + 入出力整合チェック (`--strict`)                                                                                                                          |       |                  |
| `warifuri graph`         | 依存グラフ生成 (`--project`, `--format mermaid                                                                                                                    | ascii | html`, `--web`) |
| `warifuri mark-done`     | 手動で `done.md` 作成 (`<proj>/<task>`, `--message`)                                                                                                             |       |                  |
| `warifuri template list` | テンプレート + タスク一覧 (`--format`)                                                                                                                                 |       |                  |
| `warifuri issue`         | GitHub Issue 起票  • `--project <proj>` 親 Issue  • `--task <proj>/<task>` 子 Issue  • `--all-tasks <proj>` 一括子 Issue  共通: `--assignee`, `--label`, `--dry-run` |       |                  |

## 8. GitHub 連携規約

 Issue タイトル

   親: `[PROJECT] <project>`
   子: `[TASK] <project>/<task>`
 ブランチ名: `project/task/YYMMDDHHMM/number` ※numberは同名のブランチがあった場合にインクリメント。重複によるエラー防止
 PR 完了条件: `done.md` を含むこと。
 自動マージ: `auto_merge.yaml` があり CI Green の場合、Actions でマージ。

## 9. セーフティ機構（ライト版）

 一時ディレクトリ実行 + `bash -euo pipefail` で元データを保護。
 循環依存を `warifuri validate` で検知。
 Machine 実行ログを `logs/` に保存し、失敗時は `exit≠0` を検知。
 `done.md` は空で OK、成功時に SHA/時間を追記。
 Strict スキーマで typo/未知キーを排除。

## 10. 受け入れテスト（抜粋）

 init: 空／テンプレ全体／テンプレ単体が正しく生成。
 validate: 循環依存で非0終了＋パス表示。
 Machine 失敗: logs 生成・done.md なし。
 mark-done: `touch done.md` で list 結果が completed に移動。

---

依存グラフ × `done.md` だけで回る、シンプルかつ安全な“割り振り” CLI。
