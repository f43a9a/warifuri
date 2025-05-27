# 📋 warifuri 実装TODO リスト

> **目的**: ドキュメント（要件定義書・設計書・CLI仕様書）に記載された機能が適切に実装されているかを検証し、不足している機能を特定する。

## 🔍 調査対象ドキュメント

- `docs/requirement.md` - 要件定義書 (v1.2)
- `docs/design.md` - 設計ドキュメント (v1.2)  
- `docs/cli_command_list.md` - CLI コマンドリスト
- `docs/development.md` - 開発方針

---

## ✅ 実装済み機能

### 基本CLI構造
- [x] 9つの基本コマンドが存在: `init`, `list`, `run`, `show`, `validate`, `graph`, `mark-done`, `template`, `issue`
- [x] `--log-level` グローバルオプション（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- [x] `--workspace` グローバルオプション
- [x] エラーハンドリング（workspace 見つからない場合の適切なエラー）

### テスト自動化
- [x] 包括的テストスイート（40/40 テスト成功）
- [x] CLI、コア機能、テンプレート、統合テスト
- [x] 循環依存検知の修正
- [x] 型安全性の検証

---

## 🚨 高優先度 TODO（機能不足・未実装）

### 1. `warifuri init` コマンド - テンプレート機能
#### 📋 要求仕様
- **ドキュメント**: `docs/cli_command_list.md` - テンプレート展開機能
- **構文**: `warifuri init --template <tpl>` および `warifuri init <project> --template <tpl>/<tpl-task>`

#### ❌ 実装ギャップ
- [ ] **テンプレート全体展開**: `warifuri init --template data-pipeline` のような使用方法
- [ ] **部分テンプレート展開**: `warifuri init myproject --template workflow/task_a` 形式
- [ ] **プレースホルダー置換**: `{{TASK_NAME}}`, `{{PROJECT_NAME}}` などの変数置換機能
- [ ] **--force** オプション: 既存ファイル上書き許可
- [ ] **--dry-run** オプション: 生成内容のプレビュー

### 2. `warifuri list` コマンド - 出力フォーマット
#### 📋 要求仕様  
- **構文**: `warifuri list [--ready|--completed] [--project <n>] [--format <type>] [--fields a,b]`

#### ❌ 実装ギャップ
- [ ] **--format** オプション: `plain`, `json`, `tsv` 出力形式
- [ ] **--fields** オプション: カスタムフィールド選択 (`name`, `description`, `status`, etc.)
- [ ] **--project** フィルタリング: 特定プロジェクトのタスクのみ表示
- [ ] **--completed** フィルタ: 完了タスクのみ表示

### 3. `warifuri run` コマンド - 自動実行機能
#### 📋 要求仕様
- 引数なし: ready タスクを1件自動実行
- `--task <proj>`: プロジェクト内 ready を1件実行

#### ❌ 実装ギャップ  
- [ ] **自動ready タスク選択**: 引数なしでのready タスク1件自動実行
- [ ] **プロジェクト内ready選択**: `--task myproject` でプロジェクト内の1件ready選択
- [ ] **環境変数設定**: Machineタスク実行時の標準環境変数
  - `WARIFURI_PROJECT_NAME`
  - `WARIFURI_TASK_NAME` 
  - `WARIFURI_WORKSPACE_DIR`
  - `WARIFURI_INPUT_DIR`
  - `WARIFURI_OUTPUT_DIR`

### 4. AI タスク実行機能 - 完全未実装
#### 📋 要求仕様
- **トリガー**: `prompt.yaml` の存在で AI タスクと判定
- **実行**: LLM API 呼び出し → `output/response.md` 保存

#### ❌ 実装ギャップ
- [ ] **prompt.yaml 読み込み**: `model`, `temperature`, `system_prompt` 等の設定
- [ ] **LLM API 統合**: OpenAI/Claude/Gemini 等のAPI呼び出し
- [ ] **プロンプト構築**: `system_prompt` + `instruction.yaml` の `description` 結合
- [ ] **レスポンス保存**: `output/response.md` への結果保存
- [ ] **エラーログ**: `logs/failed_<timestamp>.log` への失敗ログ記録

### 5. Machine タスク実行 - サンドボックス化不足
#### 📋 要求仕様
- 一時ディレクトリでの隔離実行
- `bash -euo pipefail` での安全実行
- 成果物の自動コピーバック

#### ❌ 実装ギャップ
- [ ] **一時ディレクトリ実行**: `mktemp -d` での隔離
- [ ] **ファイルコピーバック**: `outputs` フィールドに基づく自動コピー
- [ ] **ログ保存**: 実行ログの `logs/` ディレクトリ保存
- [ ] **bash安全フラグ**: `-euo pipefail` の強制適用

### 6. `warifuri show` コマンド - フォーマット不足
#### 📋 要求仕様
- `--format yaml|json|pretty` での出力形式選択

#### ❌ 実装ギャップ
- [ ] **--format** オプション: YAML, JSON, Pretty 出力
- [ ] **メタ情報表示**: タスクタイプ、依存関係、完了状況などの表示

### 7. `warifuri graph` コマンド - 出力形式不足
#### 📋 要求仕様
- `--format mermaid|ascii|html` での依存グラフ生成
- `--web` オプションでブラウザ表示

#### ❌ 実装ギャップ
- [ ] **HTML出力**: グラフのHTML生成
- [ ] **ASCII出力**: テキストベースの依存グラフ
- [ ] **--web オプション**: ブラウザでの自動表示
- [ ] **--project フィルタ**: 特定プロジェクトのグラフのみ

### 8. `warifuri issue` コマンド - GitHub 統合
#### 📋 要求仕様
- GitHub CLI (`gh`) を使用した Issue 作成
- 親Issue、子Issue、一括Issue 作成

#### ❌ 実装ギャップ
- [ ] **GitHub CLI 統合**: `gh issue create` の実行
- [ ] **Issue 重複判定**: 既存 Issue の確認と重複回避
- [ ] **Issue テンプレート**: 親Issue、子Issue の適切なテンプレート
- [ ] **ラベル・アサイン**: `--label`, `--assignee` オプションの実装

---

## 🔧 中優先度 TODO（機能改善・拡張）

### 9. 完了ファイル（done.md）機能強化
#### 📋 要求仕様
- SHA + タイムスタンプの自動記録
- 空ファイルでも完了と認識

#### ❓ 確認要
- [ ] **推奨フォーマット**: `YYYY-MM-DD HH:MM:SS SHA: <commit_sha>` 形式での自動記録
- [ ] **Git統合**: commit SHA の自動取得・記録

### 10. 自動マージ機能（auto_merge.yaml）
#### 📋 要求仕様  
- `auto_merge.yaml` 存在時の GitHub Actions 自動マージ

#### ❓ 確認要
- [ ] **GitHub Actions ワークフロー**: 自動マージ用のワークフロー作成
- [ ] **CI 統合**: `warifuri validate` 成功時のマージ条件

### 11. スキーマバリデーション強化
#### 📋 要求仕様
- `workspace/schemas/` ローカルスキーマ優先
- `--strict` オプションでの厳密検証

#### ❓ 確認要
- [ ] **ローカルスキーマ**: `workspace/schemas/instruction.schema.json` の優先使用
- [ ] **--strict オプション**: 不明キー・typo の厳密検出

### 12. 入出力ファイル管理
#### 📋 要求仕様
- `inputs`/`outputs` フィールドでのファイル管理
- 存在チェック・自動コピー

#### ❓ 確認要
- [ ] **入力ファイル検証**: `inputs` リストのファイル存在チェック
- [ ] **出力ファイル管理**: `outputs` リストに基づく成果物管理

---

## 🏗️ 低優先度 TODO（将来拡張・最適化）

### 13. ブランチ命名規約サポート
#### 📋 要求仕様
- `project/task/YYYYMMDDHHMM/NNN` 形式のブランチ自動生成

#### 💡 将来対応
- [ ] **ブランチ自動生成**: GitHub 連携でのブランチ作成
- [ ] **命名規約チェック**: ブランチ名の規約準拠確認

### 14. テンプレートギャラリー機能
#### 📋 要求仕様
- プロジェクト横断テンプレートの共有・管理

#### 💡 将来対応
- [ ] **テンプレート検索**: キーワードでのテンプレート検索
- [ ] **テンプレート評価**: 使用頻度・評価システム

### 15. パフォーマンス最適化
#### 📋 要求仕様
- 大規模ワークスペースでの高速動作

#### 💡 将来対応
- [ ] **キャッシュ機能**: タスク情報のキャッシュ化
- [ ] **並列処理**: 複数タスクの並列実行

---

## 📊 実装完了度サマリ

| カテゴリ | 実装済み | 要対応 | 完了率 |
|---------|----------|--------|--------|
| **基本CLI** | 9/9 | 0/9 | 100% |
| **init コマンド** | 2/6 | 4/6 | 33% |
| **list コマンド** | 2/6 | 4/6 | 33% |
| **run コマンド** | 3/8 | 5/8 | 38% |
| **AI タスク** | 0/5 | 5/5 | 0% |
| **Machine タスク** | 2/6 | 4/6 | 33% |
| **show コマンド** | 1/3 | 2/3 | 33% |
| **graph コマンド** | 1/5 | 4/5 | 20% |
| **issue コマンド** | 1/6 | 5/6 | 17% |
| **GitHub 統合** | 0/4 | 4/4 | 0% |

### 🎯 優先実装順序（推奨）

1. **AI タスク実行** - コア機能として最重要
2. **テンプレート機能** - `init` コマンドの基本機能
3. **Machine タスク改善** - サンドボックス化とログ
4. **出力フォーマット** - `list`, `show`, `graph` のオプション
5. **GitHub 統合** - `issue` コマンドの実装

---

## 📝 検証方法

各TODOアイテムの実装後は以下で検証：

```bash
# 基本動作確認
warifuri --help
warifuri list --format json
warifuri run --dry-run

# テンプレート機能
warifuri init --template data-pipeline --dry-run
warifuri template list

# AI タスク実行
cd workspace/projects/test-ai/
warifuri run --task test-ai/ai-task --dry-run

# GitHub 統合
warifuri issue --project test-project --dry-run

# 完全なE2Eテスト
pytest tests/ -v
```

---

このTODOリストを使用して段階的に実装を進め、ドキュメント仕様との完全な一致を目指します。
