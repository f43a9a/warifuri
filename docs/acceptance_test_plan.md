# 📋 warifuri 受入テスト計画書

> **作成日**: 2025年5月27日
> **対象システム**: warifuri v0.1.0
> **テスト責任者**: 開発チーム
> **実施環境**: 開発環境 (Debian GNU/Linux 12)

---

## 🎯 受入テスト目的

### 主要目的
- **機能完全性**: 仕様通りの動作確認
- **使用性検証**: 実際のワークフロー体験
- **バグ検出**: 隠れた不具合の発見
- **パフォーマンス**: 実用レベルの性能確認
- **統合性**: GitHub連携・ファイル操作の安全性確認

### 成功基準
- [ ] 全機能が仕様書通りに動作する
- [ ] エラーハンドリングが適切に機能する
- [ ] ユーザビリティに問題がない
- [ ] データ破損・ファイル消失が発生しない
- [ ] GitHub統合が正常に動作する

---

## 🗺️ テストシナリオ設計

### シナリオ1: 新規プロジェクト立ち上げ
**想定**: 初回ユーザーがプロジェクトを開始する場面

```bash
# 1. ワークスペース初期化
warifuri init sample-project

# 2. 複数タスク作成
warifuri init sample-project/setup-environment
warifuri init sample-project/install-dependencies
warifuri init sample-project/run-tests
warifuri init sample-project/deploy

# 3. タスク状態確認
warifuri list
warifuri validate
```

### シナリオ2: 依存関係のあるタスクフロー
**想定**: 順序が重要な開発ワークフロー

```bash
# 1. 依存関係付きタスク作成
# setup-environment → install-dependencies → run-tests → deploy

# 2. 段階的実行
warifuri run  # setup-environment 実行
warifuri list --ready  # 次のready確認
warifuri run  # install-dependencies 実行

# 3. 依存関係グラフ確認
warifuri graph --format html --web
```

### シナリオ3: Machine・AI・Human タスクの混在
**想定**: 異なるタスク種別を含む複合ワークフロー

```bash
# Machine タスク (自動化スクリプト)
# AI タスク (コード生成・レビュー)
# Human タスク (手動確認・承認)
```

### シナリオ4: GitHub統合ワークフロー
**想定**: Issue起票からPRマージまでの一連の流れ

```bash
# 1. プロジェクトIssue作成
warifuri issue --project sample-project --assignee @user

# 2. タスクIssue一括作成
warifuri issue --all-tasks sample-project

# 3. 自動マージ設定
# auto_merge.yaml ファイル確認
```

### シナリオ5: エラー・例外ケース
**想定**: 異常系・境界値での動作確認

```bash
# 循環依存検出
# 存在しないタスク実行
# 権限エラー処理
# ネットワークエラー処理
```

---

## 🧪 詳細テストケース

### A. 基本CLI動作テスト

#### A-1: コマンドヘルプ表示
```bash
warifuri --help
warifuri init --help
warifuri run --help
warifuri list --help
```
**期待結果**: 各コマンドのヘルプが適切に表示される

#### A-2: グローバルオプション
```bash
warifuri --log-level DEBUG list
warifuri --workspace /custom/path list
```
**期待結果**: ログレベル変更・カスタムワークスペース指定が動作

#### A-3: エラーハンドリング
```bash
warifuri list  # workspace外で実行
warifuri run --task nonexistent
warifuri init existing-project  # 既存上書き
```
**期待結果**: 適切なエラーメッセージと終了コード

### B. プロジェクト・タスク管理テスト

#### B-1: プロジェクト作成
```bash
cd workspace/
warifuri init test-project
ls projects/test-project/
cat projects/test-project/instruction.yaml
```
**期待結果**:
- プロジェクトディレクトリ作成
- instruction.yaml が正しいスキーマで生成

#### B-2: タスク作成・階層構造
```bash
warifuri init test-project/backend-setup
warifuri init test-project/frontend-setup
warifuri init test-project/integration-test

ls -la projects/test-project/*/
```
**期待結果**:
- 各タスクディレクトリが作成される
- instruction.yaml が各タスクに生成される

#### B-3: 依存関係設定
```bash
# backend-setup → frontend-setup → integration-test
# の順序で依存関係を設定し、validate で確認
warifuri validate
```

### C. タスク実行テスト

#### C-1: Machine タスク実行
```bash
# run.sh を含むタスクを作成・実行
echo '#!/bin/bash
echo "Machine task executed successfully"
echo "Current dir: $(pwd)"
echo "Environment vars:"
env | grep WARIFURI
' > projects/test-project/backend-setup/run.sh

chmod +x projects/test-project/backend-setup/run.sh
warifuri run --task test-project/backend-setup
```
**期待結果**:
- スクリプトが一時ディレクトリで実行される
- 環境変数が正しく設定される
- done.md が自動生成される

#### C-2: Human タスク処理
```bash
# run.sh もprompt.yaml もないタスクの処理確認
warifuri run --task test-project/manual-review
warifuri mark-done test-project/manual-review --message "Manual review completed"
```

#### C-3: 強制実行・ドライラン
```bash
warifuri run --task test-project/backend-setup --force
warifuri run --task test-project/frontend-setup --dry-run
```

### D. 一覧・表示・検索テスト

#### D-1: タスク一覧表示
```bash
warifuri list
warifuri list --ready
warifuri list --completed
warifuri list --project test-project
```
**期待結果**: 適切なフィルタリングとステータス表示

#### D-2: タスク詳細表示
```bash
warifuri show --task test-project/backend-setup
warifuri show --task test-project --format json
```

#### D-3: 依存関係グラフ
```bash
warifuri graph --format mermaid
warifuri graph --format ascii
warifuri graph --format html --web
```
**期待結果**: 各形式で正しいグラフが生成される

### E. 検証・品質保証テスト

#### E-1: スキーマ検証
```bash
warifuri validate
warifuri validate --strict
```

#### E-2: 循環依存検出
```bash
# 意図的に循環依存を作成してテスト
# A → B → C → A のパターン
```

#### E-3: ファイル参照整合性
```bash
# inputs/outputs フィールドのファイル存在チェック
```

### F. GitHub統合テスト

#### F-1: Issue作成 (ドライラン)
```bash
warifuri issue --project test-project --dry-run
warifuri issue --task test-project/backend-setup --dry-run
warifuri issue --all-tasks test-project --dry-run
```

#### F-2: 自動マージ設定
```bash
touch projects/test-project/backend-setup/auto_merge.yaml
# GitHub Actions 連携テスト (将来実装)
```

---

## 🎯 実施手順

### Phase 1: 環境準備
1. クリーンな作業環境確保
2. 依存関係インストール確認
3. テスト用ワークスペース作成

### Phase 2: 基本機能テスト
1. CLI コマンド動作確認
2. プロジェクト・タスク作成
3. 基本的なワークフロー実行

### Phase 3: 統合テスト
1. 複雑な依存関係テスト
2. エラーハンドリング確認
3. パフォーマンステスト

### Phase 4: 実戦シミュレーション
1. リアルなプロジェクト構成での検証
2. ユーザビリティ評価
3. ドキュメント整合性確認

---

## 📊 評価基準・チェックリスト

### 機能性評価
- [ ] 全コマンドが仕様通りに動作する
- [ ] エラーメッセージが分かりやすい
- [ ] ヘルプドキュメントが正確
- [ ] ファイル操作が安全

### 使用性評価
- [ ] 直感的なコマンド体系
- [ ] 適切なデフォルト動作
- [ ] 明確なフィードバック
- [ ] 学習コストの低さ

### 信頼性評価
- [ ] データ破損が発生しない
- [ ] 予期しない終了がない
- [ ] 適切な例外処理
- [ ] ログ出力の妥当性

### パフォーマンス評価
- [ ] コマンド実行速度
- [ ] 大規模ワークスペース対応
- [ ] メモリ使用量の妥当性
- [ ] ファイルI/O効率性

---

## 🚨 想定される問題・リスク

### 高リスク項目
1. **ファイル消失**: スクリプト実行時の予期しないファイル削除
2. **権限エラー**: 一時ディレクトリ作成・実行権限問題
3. **循環依存**: 検出アルゴリズムの抜け・漏れ
4. **GitHub API**: 認証エラー・レート制限

### 中リスク項目
1. **文字エンコーディング**: 非ASCII文字の取り扱い
2. **パス処理**: Windows/Linux間の互換性
3. **同時実行**: 複数プロセス実行時の競合状態
4. **大容量ファイル**: メモリ不足・処理時間

### 低リスク項目
1. **UI表示**: 表示崩れ・文字化け
2. **ログ出力**: 過剰・不足な情報
3. **ヘルプ**: 古い情報・タイポ

---

## 📋 テスト実行記録テンプレート

### 実行環境情報
- **OS**: Debian GNU/Linux 12 (bookworm)
- **Python**: 3.11+
- **Git**: バージョン確認
- **warifuri**: v0.1.0

### テスト結果記録

| テストケース | 実行日時 | 結果 | 備考 |
|-------------|----------|------|------|
| A-1: ヘルプ表示 | YYYY-MM-DD HH:MM | ✅/❌ | - |
| A-2: グローバルオプション | YYYY-MM-DD HH:MM | ✅/❌ | - |
| ... | ... | ... | ... |

### バグ・課題記録

| ID | 発見日 | 重要度 | 内容 | 再現手順 | 状態 |
|----|--------|--------|------|----------|------|
| BUG-001 | MM-DD | 高/中/低 | 問題概要 | 再現ステップ | Open/Fixed |

---

## 🎯 次のアクション

1. **✅ テスト計画承認** - 関係者レビュー
2. **🚀 Phase 1実行** - 基本環境・機能確認
3. **📝 結果記録** - 問題点・改善点の文書化
4. **🔧 バグ修正** - 発見された問題の対応
5. **✨ 最終承認** - 受入基準クリア確認

この受入テスト計画に従って、段階的にwarifuriシステムの品質確認を行い、実用性とバグの有無を検証していきましょう！
