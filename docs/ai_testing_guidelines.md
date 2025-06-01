# AI用テスト実装指示書

## 📌 概要

本プロジェクトは、Python製のシステムにおいて、厳密な安全性と信頼性を担保するために、高水準の自動テスト環境を構築・維持することを目的とする。
開発者がコードを読まない前提であるため、**すべてのテストは自動検証可能かつCIでブロックされる構造を持つこと**。

---

## ✅ 作業方針

- **必ずpytestベースで構成**
- **人間が関与するのは仕様YAMLのみ**
- **コードの正当性はテスト通過のみで評価**
- **fail時のログは誰でも読める形式で明確に出力**

---

## 🗂️ ディレクトリ構成（標準）

```
project_root/
├── src/                        # 本体コード
├── tests/
│   ├── unit/                   # 単体テスト
│   ├── integration/            # 統合テスト（依存をモック）
│   ├── e2e/                    # CLI/APIなどE2E
│   ├── data/                   # 入力パターン（正常・異常・境界）
│   ├── snapshots/              # snapshot比較用出力保存
│   └── specs/                  # テスト観点（YAML形式）
├── .github/workflows/          # CI自動実行設定
├── noxfile.py or tox.ini       # 一括テスト実行用
├── ai_test_todo.yaml           # AI向けTODOリスト
```

---

## 🔧 テスト仕様

### 1. 単体テスト（tests/unit/）

- 各関数・クラスに対して、
  - 正常入力 → 正常出力
  - 異常入力 → 適切な例外
  - 境界値入力 → 安定動作
- `hypothesis` を用い、引数の自動生成で異常ケース探索を行うこと

### 2. ミューテーションテスト

- `mutmut` を使ってすべてのテストの実効性を確認
- Mutation Score が90%未満なら即エラーでCIをfailさせる

### 3. 静的解析（型・構文・セキュリティ）

- `mypy`：strictモード必須。Optional型の明示も必須
- `ruff`：構文・未使用コード・構造エラーを含めチェック
- `bandit`：全ファイル対象。severity=LOW以上でfail

### 4. 統合テスト（tests/integration/）

- 外部依存（DB・API）はすべてモック化
- 入出力・状態変化を検証。YAMLで期待値記述可能にすること

### 5. E2Eテスト（tests/e2e/）

- CLIやREST APIからエンドツーエンドで動作を確認
- 正常・失敗の両シナリオを含む
- Playwrightや `subprocess.run()` を用いて検証

### 6. スナップショットテスト

- `snapshottest`でCLI出力やAPIレスポンスの変化を検出
- 仕様が変わる場合は人間がsnapファイルをレビュー・更新する

---

## 🚨 CI条件（GitHub Actions）

- `pytest` 失敗 → ❌ ブロック
- カバレッジ（statement/branch） < 100% → ⚠️ 警告
- mutation score < 90% → ❌ ブロック
- `mypy`, `bandit`, `ruff` でのエラー → ❌ ブロック
- `safety` による脆弱性検出 → ❌ ブロック

---

## 📄 テストデータ仕様（tests/data/*.yaml）

```yaml
- case_id: "invalid_email"
  description: "メール形式が不正な場合"
  input:
    email: "xxx@"
    password: "abc123"
  expected_exception: "ValueError"
```

---

## 📋 テスト観点記述仕様（tests/specs/*.yaml）

```yaml
function: "register_user"
cases:
  - id: "valid_input"
    type: "正常系"
    description: "正しいメールとパスワード"
  - id: "empty_email"
    type: "異常系"
    description: "メールが空文字"
```

---

## 🧠 AIへの補足指示

* **assertのないテストは作らないこと**
* **CLI実行テストではexit codeも検証すること**
* **生成されるログ・出力はすべてdiff可能なテキストであること**
* **依存関係は`pyproject.toml`または`requirements.txt`に追記**
