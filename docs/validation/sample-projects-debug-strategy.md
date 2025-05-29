# サンプルプロジェクト作成・デバッグ戦略

## 目的

warifuri の依存関係解決バグ修正後、様々なシナリオでの動作を検証するため、段階的にサンプルプロジェクトを作成し、デバッグを行う。

## 修正済みの内容

### 修正されたバグ
- **依存関係ファイル解決**: `inputs` を持つタスクがファイル存在時でも PENDING のままになる問題
- **ファイルパス解決**: `validate_file_references()` が `workspace_path / input_file` で検索するように修正
- **依存関係名前解決**: 短縮名（`task-name`）から完全名（`project/task-name`）への変換
- **循環インポート**: `discovery.py` と `validation.py` 間の循環依存を動的インポートで解決

### 検証済みの動作
- ✅ 基本的な依存関係解決（foundation → dependent）
- ✅ ファイル存在チェック（workspace root での検索）
- ✅ 既存テストとの後方互換性

## サンプルプロジェクト作成戦略

### Phase 1: 基本パターンの検証

#### 1.1 Simple Dependency Chain
```
project-a/
├── task-foundation (outputs: base.txt)
└── task-consumer (inputs: base.txt, depends: foundation)
```

**検証ポイント**:
- 基本的な依存関係解決
- 単一ファイルの入出力
- 修正されたファイルパス解決

#### 1.2 Multi-File Dependencies
```
project-b/
├── task-generator (outputs: data1.txt, data2.txt)
└── task-processor (inputs: data1.txt, data2.txt, depends: generator)
```

**検証ポイント**:
- 複数ファイルの依存関係
- すべてのファイルが揃うまで PENDING 状態を維持

#### 1.3 Cross-Project Dependencies
```
project-core/
└── task-shared (outputs: shared.conf)

project-app/
└── task-main (inputs: shared.conf, depends: core/shared)
```

**検証ポイント**:
- プロジェクト間の依存関係
- 完全名での依存関係指定

### Phase 2: 複雑なパターンの検証

#### 2.1 Deep Chain Dependencies
```
project-chain/
├── task-step1 (outputs: step1.txt)
├── task-step2 (inputs: step1.txt, outputs: step2.txt, depends: step1)
├── task-step3 (inputs: step2.txt, outputs: step3.txt, depends: step2)
├── task-step4 (inputs: step3.txt, outputs: step4.txt, depends: step3)
└── task-final (inputs: step4.txt, depends: step4)
```

**検証ポイント**:
- 長い依存関係チェーン（5段階）
- 各段階での正しい状態遷移
- パフォーマンスの確認

#### 2.2 Diamond Dependencies
```
project-diamond/
├── task-source (outputs: source.txt)
├── task-branch-a (inputs: source.txt, outputs: branch-a.txt, depends: source)
├── task-branch-b (inputs: source.txt, outputs: branch-b.txt, depends: source)
└── task-merge (inputs: branch-a.txt, branch-b.txt, depends: branch-a, branch-b)
```

**検証ポイント**:
- 複数の並列依存関係
- すべての並列タスク完了まで待機
- ダイヤモンド型依存グラフの解決

#### 2.3 Mixed Dependencies (file + task)
```
project-mixed/
├── external-file.txt (手動作成)
├── task-generator (outputs: generated.txt)
└── task-consumer (inputs: external-file.txt, generated.txt, depends: generator)
```

**検証ポイント**:
- 外部ファイル + タスク出力の混合依存
- 一部ファイルの事前存在確認

### Phase 3: エラーハンドリングの検証

#### 3.1 Missing Files
```
project-error/
└── task-broken (inputs: missing-file.txt)
```

**検証ポイント**:
- 存在しないファイルへの依存
- 適切なエラーメッセージ
- PENDING 状態の維持

#### 3.2 Circular Dependencies
```
project-circular/
├── task-a (outputs: a.txt, inputs: b.txt, depends: b)
└── task-b (outputs: b.txt, inputs: a.txt, depends: a)
```

**検証ポイント**:
- 循環依存の検出
- 適切なエラー報告
- システムの安定性

#### 3.3 Invalid Task References
```
project-invalid/
└── task-broken (depends: non-existent-task)
```

**検証ポイント**:
- 存在しないタスクへの依存
- エラーハンドリング
- 他タスクへの影響なし

## デバッグ手法

### 1. 段階的実行
```bash
# 各プロジェクトで状態確認
warifuri list --show-status
warifuri list --show-dependencies

# 単一タスクでの動作確認
warifuri run specific-task

# 全体実行での動作確認
warifuri run
```

### 2. ログ・デバッグ出力
```python
# debug_helper.py での詳細ログ
def debug_task_states(projects, workspace_path):
    """タスク状態の詳細デバッグ"""
    for project in projects:
        for task in project.tasks:
            print(f"Task: {task.full_name}")
            print(f"  Status: {task.status}")
            print(f"  Dependencies: {task.depends}")
            print(f"  Inputs: {task.inputs}")
            # ファイル存在チェック
            # 依存タスク状態チェック
```

### 3. 自動テスト生成
```python
# 各サンプルプロジェクトに対応するテストを自動生成
def generate_test_for_sample_project(project_name):
    """サンプルプロジェクトの期待動作テストを生成"""
    pass
```

## 実装スケジュール

### Day 1: Phase 1 実装
1. Simple Dependency Chain の作成・テスト
2. Multi-File Dependencies の作成・テスト
3. Cross-Project Dependencies の作成・テスト

### Day 2: Phase 2 実装
1. Deep Chain Dependencies の作成・テスト
2. Diamond Dependencies の作成・テスト
3. Mixed Dependencies の作成・テスト

### Day 3: Phase 3 & 総合テスト
1. エラーハンドリングシナリオの作成・テスト
2. パフォーマンステスト
3. 総合的な回帰テスト

## 成果物

### ディレクトリ構造
```
/workspace/
├── sample-projects/
│   ├── simple-chain/
│   ├── multi-file/
│   ├── cross-project/
│   ├── deep-chain/
│   ├── diamond/
│   ├── mixed/
│   └── error-cases/
├── tests/integration/
│   ├── test_sample_simple_chain.py
│   ├── test_sample_multi_file.py
│   └── ...
└── debug/
    ├── debug_helper.py
    ├── run_all_samples.py
    └── validate_samples.py
```

### ドキュメント
- 各サンプルプロジェクトの README
- デバッグ結果レポート
- パフォーマンス分析レポート
- 発見された問題と対策

## 期待される効果

1. **信頼性向上**: 様々なシナリオでの動作確認
2. **回帰防止**: 継続的なテストスイート構築
3. **ユーザビリティ**: 実際の使用パターンでの検証
4. **保守性**: デバッグツールとテストの整備

---

このドキュメントに基づいて段階的にサンプルプロジェクトを作成し、warifuri の依存関係解決機能の完全性を確保する。
