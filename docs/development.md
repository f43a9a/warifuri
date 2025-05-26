# 🛠️ warifuri 開発方針 & リポジトリ構成

> **対象読者**: コントリビューター / レビュアー / CI 管理者
> **最終更新**: 2025‑05‑26

---

## 1. ルートディレクトリ構成

```text
warifuri/               # Python パッケージ本体 (src 配置)
workspace/              # 実行対象のタスク・テンプレを置く作業ツリー
  ├─ projects/          # プロジェクト & タスク (Git 追跡対象)
  └─ templates/         # テンプレ雛形 (再利用用)
schemas/                # JSON Schema ファイル (instruction 他)
docs/                   # 設計書・要件書・ADR 等
.github/workflows/      # GitHub Actions (CI / CD)
README.md               # ユーザー向け概要
pyproject.toml          # Poetry + build 設定
```

> **ポイント**: `workspace/` 内はユーザー資産。`warifuri/` はツール本体で完全分離。

---

## 2. Python パッケージ構成

```text
warifuri/
  ├─ __init__.py        # バージョン定義のみ
  ├─ cli/               # click ベース CLI
  │   ├─ __init__.py
  │   ├─ main.py       # エントリーポイント (console_scripts)
  │   └─ commands/     # 各サブコマンド実装
  ├─ core/              # ビジネスロジック (依存解析・実行エンジン)
  ├─ utils/             # 汎用ユーティリティ
  └─ schemas/embedded/  # バンドル済みスキーマ (fallback)
```

* **設計指針** : CLI ↔ Core を疎結合にし、Core を他ツールからも import 可能に。

---

## 3. コーディング規約

* **言語** : Python 3.11+ / UTF‑8
* **フォーマッタ** : `black` (line‑length = 88)
* **静的解析** : `ruff` + `mypy --strict`
* **Commit ルール** : Conventional Commits (`feat:`, `fix:`, など)
* **ブランチ規約** : `project/task/YYYYMMDDHHMM/NNN`
* **依存管理** : Poetry (`pyproject.toml`) で lock。

---

## 4. テスト戦略

| 階層   | ツール                                         | カバレッジ目標     |
| ---- | ------------------------------------------- | ----------- |
| Unit | `pytest`                                    | 90%+ (core) |
| CLI  | `pytest + click.testing`                    | 70%         |
| E2E  | GitHub Actions ワークフロー上で `projects/demo` を実行 | 成功率 100%    |

---

## 5. CI / CD

* **CI ワークフロー** : `.github/workflows/ci.yml`

  1. `setup-python` → Poetry install
  2. Lint (`ruff`, `black --check`)
  3. Type‑check (`mypy`)
  4. Test (`pytest -q`)
  5. Build package (`poetry build`)
* **自動リリース** : `release.yml` で tag push 時に PyPI upload (Test → Prod)
* **Warifuri validate** : すべての PR で `warifuri validate` を実行

---

## 6. ブランチ・PR運用

* **ブランチ名** : `project/task/202405261532/001` 形式
  `001` は同日内での連番。重複エラーを防ぐ。
* **PR タイトル** : `[TASK] project/task`
  親 Issue は `[PROJECT] project`。
* **レビュールール** : 少なくとも 1 Human reviewer が Approve でマージ。
* **Auto‑merge** : `auto_merge.yaml` が変更差分に含まれ、CI Green → 自動。

---
