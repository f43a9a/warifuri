# Warifuri依存関係解決バグ - 詳細レポート

**報告日**: 2025-05-29
**バグID**: WARIFURI-DEP-001
**重要度**: High
**ステータス**: 再現確認済み

## 📋 問題概要

warifuriにおいて、依存関係が正しく設定され、依存タスクが完了済みでも、`inputs`配列にファイルが指定されている後続タスクが「READY」状態にならない問題。

## 🔍 バグ再現手順

### 1. テスト環境構築
```bash
mkdir -p warifuri-test/workspace
cd warifuri-test
warifuri init test-dependency-bug
```

### 2. 基盤タスク作成
```bash
warifuri init test-dependency-bug/task-a-foundation
```

**設定内容** (`task-a-foundation/instruction.yaml`):
```yaml
name: task-a-foundation
task_type: human
description: "Foundation Task A - Creates foundation files with no external dependencies"
dependencies: []
inputs: []
outputs:
  - "foundation_output.txt"
```

### 3. 依存タスク作成
```bash
warifuri init test-dependency-bug/task-b-dependent
```

**設定内容** (`task-b-dependent/instruction.yaml`):
```yaml
name: task-b-dependent
task_type: human
description: "Dependent Task B - Requires foundation_output.txt from Task A"
dependencies: ["task-a-foundation"]
inputs:
  - "foundation_output.txt"
outputs:
  - "dependent_output.txt"
```

### 4. バグ再現
```bash
# ステップ1: 初期状態確認
warifuri list
# [READY] test-dependency-bug/task-a-foundation
# [PENDING] test-dependency-bug/task-b-dependent

# ステップ2: タスクA完了
warifuri run --task test-dependency-bug/task-a-foundation
warifuri mark-done test-dependency-bug/task-a-foundation

# ステップ3: 出力ファイル作成
echo "Foundation task completed" > foundation_output.txt

# ステップ4: 期待vs実際
warifuri list
# 期待: task-b-dependent が [READY] になる
# 実際: task-b-dependent が [PENDING] のまま

warifuri list --ready
# 実際: "No tasks found"
```

## 🐛 確認されたバグ

### 症状
1. **依存関係**: ✅ 正しく設定済み
2. **依存完了**: ✅ task-a-foundation は [COMPLETED]
3. **ファイル存在**: ✅ foundation_output.txt が存在
4. **タスク状態**: ❌ task-b-dependent が [PENDING] のまま
5. **Ready判定**: ❌ warifuri list --ready で表示されない

### Validation結果
```bash
warifuri validate
# ⚠️ test-dependency-bug/task-b-dependent: Input file not found: foundation_output.txt
```

**矛盾**: ファイルは実際に存在するが、warifuriが認識しない

## 🔬 技術的分析

### 推定される原因
1. **ファイルパス解決の問題**: warifuriがinputファイルを探すパスが期待と異なる
2. **作業ディレクトリの不一致**: タスク実行時とファイル探索時の基準ディレクトリが異なる
3. **ファイル探索タイミング**: validation時とREADY判定時のファイル探索ロジックの不整合

### 検証データ
```bash
# ファイル存在確認
$ ls -la foundation_output.txt
-rw-r--r-- 1 root root 39 May 29 09:56 foundation_output.txt

# 検索結果
$ find . -name "foundation_output.txt"
./foundation_output.txt

# 作業ディレクトリ
$ pwd
/workspace/warifuri-test/warifuri-test/workspace
```

## 🎯 影響範囲

### 直接的影響
- **タスクチェーン実行の停止**: 依存関係のあるタスクが実行できない
- **自動化パイプラインの破綻**: 連続的なタスク実行が不可能

### 間接的影響
- **開発効率の低下**: 手動でのタスク管理が必要
- **CI/CD統合の阻害**: 自動化されたワークフローが機能しない

## 🔧 回避策

### 一時的回避策
1. **inputs配列を空にする**: 依存関係のみで制御
```yaml
# 修正前
inputs:
  - "foundation_output.txt"

# 修正後
inputs: []
```

2. **手動ファイル存在確認**: run.shスクリプト内でファイル存在を確認

### 根本的解決が必要な理由
- ファイル依存関係はwarifuriの重要な機能
- タスク間のデータフローを正しく管理するため

## 🧪 テストケース

### 基本ケース
- [ ] 依存タスク完了後のREADY状態遷移
- [ ] inputファイル存在時のvalidation成功
- [ ] 相対パス・絶対パスでのファイル参照

### エッジケース
- [ ] 空ファイルのinput指定
- [ ] ネストしたディレクトリでのファイル参照
- [ ] 複数inputファイルの組み合わせ

### 負荷テスト
- [ ] 大量のタスク依存関係チェーン
- [ ] 並列タスク実行時の依存解決

## 📊 修正優先度

**Priority: High** - タスク実行の基本機能に影響

### 修正スコープ
1. **コア機能**: ファイル依存関係解決ロジック
2. **Validation**: ファイル存在チェックの正確性
3. **ログ出力**: デバッグ情報の充実

## 🔄 次のアクション

1. **ソースコード調査**: dependency resolution関連のコード特定
2. **単体テスト作成**: ファイル依存関係のテストケース
3. **修正実装**: パス解決ロジックの修正
4. **回帰テスト**: 既存機能への影響確認

---

**作成者**: AI Assistant
**レビュー**: Pending
**最終更新**: 2025-05-29 09:58
