# GitHub Copilot Instruction Guide

> **目的** — GitHub Copilot および任意の AI アシスタント（例：ChatGPT / CI Bot 等）が、このリポジトリでコード・テスト・ドキュメントを提案・実行する際に従うべき行動指針と技術的規範を明文化する。

---

## 1. はじめに {#intro}

* **対象**：GitHub Copilot、LLMベースのコード生成ツール、CI 上での AI スクリプトなど
* **用途**：提案補助だけでなく、ファイル生成・修正・Git 操作・スクリプト実行も許可
* **前提**：このガイドはすべての自動生成・修正・補完に対し適用される

---

## 2. 設計原則（Philosophy） {#principles}

AIアシスタントは以下の設計哲学に基づいてコードを生成・修正せよ：

| 原則           | 内容                               |
| ------------ | -------------------------------- |
| Clean        | 直線的制御 / 冗長なコメント禁止 / 意図明示の命名      |
| Safe         | 型注釈必須 / `raise` による例外 / 外部依存の抽象化 |
| Maintainable | 単一責任 / DI可能 / APIの後方互換性の維持       |
| Minimal      | 変更は必要最小限に / 最小の差分で目的を達成する        |
| UNIX-like    | 単機能・明示的・組み合わせ可能・再発明禁止            |

---

## 3. 実装規範（Coding Standards） {#standards}

### 静的解析・整形

* `black` による整形 / `ruff` によるLintを全通過すること
* `flake8` は使用不可（機能重複のため）

### 型安全

* すべての関数・メソッドにPEP484準拠の型アノテーションを付けよ
* `mypy --strict` を無修正で通過すること

### 命名・スタイル

| 要素    | 規則            |
| ----- | ------------- |
| 変数・関数 | `snake_case`  |
| クラス   | `CamelCase`   |
| 定数    | `UPPER_CASE`  |
| 文字列   | ダブルクォート `"…"` |

---

## 4. テスト戦略 {#testing}

* **優先順位**：バグ → 複雑関数 → 公共API の順にテストを書くこと
* **形式**：`pytest` + `unittest.mock` / `pytest-mock`
* **命名**：`test_<対象>_<動作>` 形式
* **副作用遮断**：ファイル = `mock_open`、HTTP = `responses` を用いること
* **カバレッジ**：数値目標は不要。品質を重視せよ。

> `print` デバッグは禁止。必ず `assert` に置換すること。

---

## 5. AI支援ガイドライン {#ai-behavior}

### 実行の自由度

AIアシスタントは以下のすべてのタスクを**即時・自律的に実行してよい**：

| タスク種別         | 自動実行 | 備考            |
| ------------- | ---- | ------------- |
| Lint 修正       | ✅    |               |
| バグ修正          | ✅    |               |
| Docstring 補完  | ✅    |               |
| テスト生成         | ✅    |               |
| Git commit    | ✅    | `main`以外のブランチ |
| Git push      | ✅    | CI環境またはPR経由限定 |
| ブランチ作成・移動     | ✅    |               |
| CLI・補助スクリプト生成 | ✅    |               |

### 重大修正（設計変更）は提案のみに留めよ

以下の操作は**AIからの提案は可、実行は人間の判断に委ねる**：

* 関数の責務分割や命名変更を伴う大規模リファクタリング
* ファイルの構成・依存構造を変える変更
* 複数モジュールにまたがる抽象化やパターン適用

提案時は必ず `# AI Suggestion:` でコメントを残すこと。

---

## 6. 禁止事項 {#prohibited}

以下の操作・生成はすべて即時却下対象とする：

* `except Exception: pass` の生成
* `print` を残したままのコミット提案
* 無意味なダミーテスト生成（assertが空、常にTrue など）
* グローバルなミュータブルステートの追加
* `eval`・`exec`・資格情報のハードコード

### 誤用例と修正例

```python
# ❌ NG: 例外を握りつぶしている
try:
    load_config()
except Exception:
    pass

# ✅ OK: 例外の明示的な捕捉と再送出
try:
    load_config()
except FileNotFoundError as e:
    logger.warning("Config not found: %s", e)
    raise
```

---

## 7. ファイル分割ルール {#split-guidelines}

### 分割すべき条件

* 300行以上かつ複数責務を含む
* 3つ以上のクラスまたは巨大関数群が存在
* 疎結合な機能（例：HTTPクライアント / 設定ローダ）
* テストが肥大化している

### 分割を避ける条件

* 単一責任に収まっている
* 分割でオーバーエンジニアリング化する
* 試作・検証中コード

### 提案方法

* 最小差分で提案せよ
* `# AI Suggestion: consider moving X to foo.py` の形式で明示せよ

---

## 8. 運用ルール・レビュー指針 {#workflow}

### AI生成結果の確認・承認手順

| 操作              | 実行元 | レビュー責任者    | 備考               |
| --------------- | --- | ---------- | ---------------- |
| Lint/整形         | AI  | 自動承認       | コミット直後にCIで反映     |
| テストコード生成        | AI  | Reviewer   | 内容とカバレッジを確認      |
| 関数の責務分割提案       | AI  | Tech Lead  | 提案コメントをベースに判断    |
| Git push / PR作成 | AI  | Maintainer | Push後、自動でPRに紐付ける |
| 補助CLIスクリプトの新規作成 | AI  | 任意         | 実行ログと目的を記述すること   |

### CI統合の推奨設定

* すべての AI 提案は PR 単位で GitHub Actions により自動検証される
* `scripts/` 以下に生成されたツールは `--dry-run` をデフォルトで実装すること
* commit メッセージに `AI-AUTO:` が含まれる場合、自動ラベル `auto` を付与

---

## 9. 付録 {#appendix}

### 推奨ディレクトリ構成（拡張版）

```
project_root/
├── src/             # アプリ本体
│   ├── domain/
│   └── service/
├── tests/           # テストコード
├── scripts/         # 補助CLI群
├── config/          # 設定ファイル群（YAML, JSON, ENV）
├── .github/         # ワークフロー/テンプレート
└── README.md
```

### コメントによるAI誘導例

```python
# AI: do not refactor this section. Compatibility-sensitive
# AI: if changed, generate corresponding tests
# AI Suggestion: consider simplifying this loop using itertools
# AI TODO: implement config loader based on schema.yaml
```

### Commitメッセージテンプレ

```
fix(parser): handle edge case in YAML parser

- Add validation for invalid list nesting
- Improve error message with line number

AI-AUTO: yes
```

---
