# GitHub Actions ワークフロー設定ガイド

このドキュメントでは、warifuri プロジェクトの GitHub Actions ワークフローの設定と使用方法について説明します。

## 📋 ワークフロー一覧

### 1. `auto-merge.yml` - 自動マージワークフロー 🤖

**目的**: `auto_merge.yaml` ファイルを含むタスクの自動マージ機能

**トリガー**:
- プルリクエストの作成・更新
- 手動実行（特定のPR番号を指定）

**機能**:
- ✅ warifuri workspace の自動検証
- ✅ テストスイートの実行
- ✅ コード品質チェック（ruff, mypy）
- ✅ `auto_merge.yaml` ファイルの検出
- ✅ 条件満たし時の自動マージ

**使用例**:
```yaml
# タスクディレクトリに配置
workspace/projects/my-project/my-task/auto_merge.yaml
```

### 2. `ci.yml` - 継続的インテグレーション 🔍

**目的**: コード品質と機能の継続的検証

**トリガー**:
- main/master/develop ブランチへのプッシュ
- プルリクエストの作成・更新

**機能**:
- ✅ Python 3.9, 3.10, 3.11 でのマルチバージョンテスト
- ✅ Ruff リンティング
- ✅ MyPy 型チェック
- ✅ テストカバレッジ計測
- ✅ 統合テスト実行
- ✅ セキュリティスキャン（Bandit）

### 3. `release.yml` - リリース自動化 🚀

**目的**: バージョンタグ作成時の自動リリース

**トリガー**:
- `v*` タグのプッシュ（例: `v1.0.0`）
- 手動実行（バージョン指定）

**機能**:
- ✅ バージョン形式の検証
- ✅ パッケージビルドとテスト
- ✅ GitHub Release 作成
- ✅ PyPI への自動公開
- ✅ ドキュメント更新

**使用例**:
```bash
# リリースタグの作成
git tag v1.0.0
git push origin v1.0.0
```

### 4. `deploy.yml` - タスクデプロイメント 🚀

**目的**: warifuri タスクの自動実行・デプロイ

**トリガー**: 手動実行のみ

**機能**:
- ✅ 環境選択（development/staging/production）
- ✅ プロジェクトフィルタリング
- ✅ Machine タスクの自動実行
- ✅ AI タスクの自動実行
- ✅ デプロイメントレポート生成
- ✅ ドライランモード

**使用例**:
```bash
# GitHub UI から手動実行
# - Environment: production
# - Project Filter: my-project
# - Dry Run: false
```

## 🔧 セットアップ手順

### 1. 必要なシークレットの設定

GitHub リポジトリの Settings > Secrets and variables > Actions で以下を設定：

```bash
# PyPI 公開用（リリース時のみ必要）
PYPI_TOKEN=your_pypi_token

# AI タスク実行用（任意）
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
```

### 2. ブランチ保護ルールの設定

main ブランチの保護設定（推奨）：

```bash
# Settings > Branches > Add rule
Branch name pattern: main

☑️ Require a pull request before merging
☑️ Require status checks to pass before merging
  ☑️ Require branches to be up to date before merging
  Required status checks:
    - quality-checks (3.11)
    - integration-tests
    - validate-warifuri

☑️ Restrict pushes that create files
☑️ Do not allow bypassing the above settings
```

### 3. 環境の設定

デプロイワークフロー用の環境設定：

```bash
# Settings > Environments
Environments:
- development (保護なし)
- staging (レビュー必須)
- production (レビュー必須 + 管理者承認)
```

## 🎯 自動マージの使用方法

### 1. タスクでの自動マージ有効化

タスクディレクトリに `auto_merge.yaml` を配置：

```yaml
# workspace/projects/my-project/my-task/auto_merge.yaml
enabled: true
conditions:
  - validation_passed
  - tests_passed
  - quality_checks_passed
merge_strategy: squash
delete_branch: true
```

### 2. プルリクエストの作成

```bash
# 通常のPR作成プロセス
git checkout -b feature/my-task
git add .
git commit -m "feat: implement my-task"
git push origin feature/my-task

# GitHub でプルリクエスト作成
```

### 3. 自動マージの実行

以下の条件が満たされると自動マージが実行されます：

1. ✅ `auto_merge.yaml` ファイルが存在
2. ✅ `warifuri validate` が成功
3. ✅ テストスイートが成功
4. ✅ コード品質チェックが成功

## 📊 ワークフロー監視

### 1. GitHub Actions タブでの確認

```bash
# リポジトリページ
Actions タブ > 各ワークフロー名 > 実行履歴
```

### 2. 通知の設定

```bash
# Settings > Notifications
☑️ Actions
  ☑️ Only failures and cancelled workflow runs
```

### 3. ステータスバッジの追加

README.md にバッジを追加：

```markdown
[![CI](https://github.com/your-org/warifuri/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/warifuri/actions/workflows/ci.yml)
[![Auto-merge](https://github.com/your-org/warifuri/actions/workflows/auto-merge.yml/badge.svg)](https://github.com/your-org/warifuri/actions/workflows/auto-merge.yml)
```

## 🚨 トラブルシューティング

### 自動マージが実行されない場合

1. **`auto_merge.yaml` ファイルの確認**:
   ```bash
   find workspace/ -name "auto_merge.yaml"
   ```

2. **検証失敗の確認**:
   ```bash
   warifuri validate --workspace workspace
   ```

3. **ワークフローログの確認**:
   ```bash
   # GitHub Actions タブで詳細ログを確認
   ```

### テスト失敗の対処

1. **ローカルでのテスト実行**:
   ```bash
   poetry run pytest tests/ -v
   ```

2. **コード品質の確認**:
   ```bash
   poetry run ruff check .
   poetry run mypy warifuri
   ```

### デプロイメント失敗の対処

1. **環境変数の確認**:
   ```bash
   # GitHub Secrets の設定確認
   ```

2. **ドライランでのテスト**:
   ```bash
   # Deploy ワークフローを Dry Run: true で実行
   ```

## 🔄 ワークフローの更新

ワークフローファイルの変更は以下の手順で行います：

1. `.github/workflows/` ディレクトリのファイルを編集
2. プルリクエストを作成
3. CI チェックの確認
4. レビューとマージ

**注意**: main ブランチに直接プッシュは推奨されません。

## 📚 参考リンク

- [GitHub Actions ドキュメント](https://docs.github.com/en/actions)
- [warifuri CLI リファレンス](../docs/cli_command_list.md)
- [ブランチ保護設定](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
