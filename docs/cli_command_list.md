# 📄 **warifuri CLI コマンドリスト v1.2**

> **制作資料用ドキュメント** — 2025-05-26
> （全 8 コマンド＋主要オプション／使用例を網羅）

---

## 0. 一覧サマリ

| コマンド                     | 役割     | ひと言で                      |
| ------------------------ | ------ | ------------------------- |
| `warifuri init`          | 雛形生成   | プロジェクト／タスク／テンプレ展開         |
| `warifuri list`          | 状態一覧   | ready／completed／全タスク      |
| `warifuri run`           | 実行     | ready自動実行・プロジェクト実行・直接実行   |
| `warifuri show`          | 定義表示   | instruction.yaml＋メタを閲覧    |
| `warifuri validate`      | 静的検証   | スキーマ・循環依存・整合性チェック         |
| `warifuri graph`         | 可視化    | 依存グラフ（Mermaid／HTML／ASCII） |
| `warifuri mark-done`     | 手動完了   | `done.md` をワンコマンドで作成      |
| `warifuri template list` | テンプレ確認 | 登録テンプレと含まれるタスクを一覧         |

---

## 1. `warifuri init`

| 項目         | 内容                                                                                                                                                         |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **目的**     | プロジェクト／タスクを生成。テンプレート複製にも対応                                                                                                                                 |
| **構文**     | `warifuri init <project>`<br>`warifuri init <project>/<task>`<br>`warifuri init --template <tpl>`<br>`warifuri init <project> --template <tpl>/<tpl-task>` |
| **主オプション** | `--template` `<tpl>` or `<tpl>/<task>`<br>`--force` 上書き<br>`--dry-run` 生成内容のみ表示                                                                            |
| **例**      | `warifuri init vision-ai/resize`<br>`warifuri init --template data-pipeline`                                                                               |

---

## 2. `warifuri list`

|            |                                                                         |                                                                       |                                          |
| ---------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------- |
| **目的**     | 現在のタスク状態を一覧表示                                                           |                                                                       |                                          |
| **構文**     | \`warifuri list \[--ready                                               | --completed] \[--project <name>] \[--format <type>] \[--fields a,b]\` |                                          |
| **主オプション** | `--ready` / `--completed`<br>`--project` `<name>`<br>`--format` \`plain | json                                                                  | tsv`<br>`--fields` `name,description,…\` |
| **例**      | `warifuri list --ready --format tsv --fields name`                      |                                                                       |                                          |

---

## 3. `warifuri run`

|            |                                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------------- |
| **目的**     | タスク実行（Machine / AI / Human 判定）                                                                          |
| **構文**     | `warifuri run [--task <proj>[/<task>]] [--dry-run] [--force]`                                           |
| **挙動**     | *引数なし* → ready タスクを1件自動実行<br>`--task <proj>` → プロジェクト内 ready を1件実行<br>`--task <proj>/<task>` → そのタスクを実行 |
| **主オプション** | `--dry-run` / `--force`                                                                                 |
| **例**      | `warifuri run`<br>`warifuri run --task vision-ai`                                                       |

---

## 4. `warifuri show`

| 項目     | 内容                                                   |      |           |
| ------ | ---------------------------------------------------- | ---- | --------- |
| **目的** | instruction.yaml＋メタファイルを閲覧                           |      |           |
| **構文** | \`warifuri show --task <proj>/<task> \[--format yaml | json | pretty]\` |
| **例**  | `warifuri show --task media/normalize --format yaml` |      |           |

---

## 5. `warifuri validate`

|        |                                |
| ------ | ------------------------------ |
| **目的** | YAML スキーマ + 循環依存 + 入出力整合性チェック  |
| **構文** | `warifuri validate [--strict]` |
| **例**  | `warifuri validate --strict`   |

---

## 6. `warifuri graph`

| 項目     | 内容                                                      |       |                  |
| ------ | ------------------------------------------------------- | ----- | ---------------- |
| **目的** | 依存関係グラフを生成                                              |       |                  |
| **構文** | \`warifuri graph \[--project <name>] \[--format mermaid | ascii | html] \[--web]\` |
| **例**  | `warifuri graph --format html --web`                    |       |                  |

---

## 7. `warifuri mark-done`

| 項目     | 内容                                                         |
| ------ | ---------------------------------------------------------- |
| **目的** | 手動タスクを最短で完了処理                                              |
| **構文** | `warifuri mark-done <proj>/<task> [--message "text"]`      |
| **動作** | `done.md` を作成し、`--message` があれば1行目に書き込む                    |
| **例**  | `warifuri mark-done vision-ai/annotate --message "手動確認完了"` |

---

## 8. `warifuri template list`

| 項目     | 内容                                        |         |
| ------ | ----------------------------------------- | ------- |
| **目的** | 利用可能なテンプレートと含まれるタスクを確認                    |         |
| **構文** | \`warifuri template list \[--format plain | json]\` |
| **例**  | `warifuri template list --format json`    |         |


了解です。**GitHub Issue 連携コマンドを正式に追加**し、子 Issue をまとめて起票できるフローも含めて仕様をまとめ直しました。

---

## 9.`warifuri issue` コマンド仕様

| パラメータ                  | 用途                                                                  | 補足                          |
| ---------------------- | ------------------------------------------------------------------- | --------------------------- |
| `--project <proj>`     | **親 Issue**を 1 件作成                                                  | タイトル `[PROJECT] <proj>`     |
| `--task <proj>/<task>` | **子 Issue**を 1 件作成                                                  | タイトル `[TASK] <proj>/<task>` |
| `--all-tasks <proj>`   | **指定プロジェクト配下の *全タスク*** を一括で子 Issue 化                                | ready／pending 関係なくディレクトリを走査 |
| **共通オプション**            |                                                                     |                             |
| `--assignee <user>`    | 1 件生成時 : その Issue に Assignee を付与<br>一括時  : 全 Issue に同一 Assignee を付与 |                             |
| `--label a,b,c`        | カンマ区切りでラベル付与（複数可）                                                   |                             |
| `--dry-run`            | GitHub には投げず、生成されるタイトル／本文を標準出力に表示                                   |                             |

> 実装：内部で `gh issue create` を呼び出し、成功した Issue URL を CLI 出力。

---

### 1️⃣ 親 Issue生成

```bash
warifuri issue --project vision-ai --assignee @lead
```

作成内容（例）

| 項目    | 値                                                             |
| ----- | ------------------------------------------------------------- |
| Title | `[PROJECT] vision-ai`                                         |
| Body  | プロジェクト概要テンプレ＋空チェックリスト<br>（`templates/project-body.md` があれば流用） |

---

### 2️⃣ 子 Issue 1 件生成

```bash
warifuri issue --task vision-ai/resize --assignee @alice --label ready,type:machine
```

本文は `instruction.yaml` から自動抽出：

* **対象ディレクトリ**: `projects/vision-ai/resize/`
* **実行タイプ**: Machine / AI / Human を自動判定
* **依存タスク**: `dependencies` リスト
* **概要**: `description` 冒頭 3 行（長い場合は折り畳み）

---

### 3️⃣ 子 Issue 一括生成

```bash
# vision-ai プロジェクト配下のすべてのタスクをIssue化
warifuri issue --all-tasks vision-ai --label todo --assignee @pm
```

動作フロー

1. `workspace/projects/vision-ai/*/instruction.yaml` を列挙
2. まだ同名 `[TASK] …` Issue が存在しないタスクだけを対象にする
3. `gh issue create` を連続呼び出し
4. 生成された Issue URL を一覧で出力（dry-run ならプレビューのみ）

---

## コマンド一覧（最終版 v1.3 α）

| コマンド                         | 目的                         |
| ---------------------------- | -------------------------- |
| **`warifuri init`**          | プロジェクト／タスク／テンプレ生成          |
| **`warifuri list`**          | タスク状態一覧                    |
| **`warifuri run`**           | ready 自動実行・プロジェクト単位実行・直接実行 |
| **`warifuri show`**          | タスク定義／メタ表示                 |
| **`warifuri validate`**      | YAML + 依存検証                |
| **`warifuri graph`**         | 依存グラフ可視化                   |
| **`warifuri mark-done`**     | 手動完了フラグ作成                  |
| **`warifuri template list`** | テンプレ一覧                     |
| **`warifuri issue`** ★       | GitHub Issue 起票（親／子／一括）    |

