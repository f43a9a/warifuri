# Warifuri依存関係解決バグ - 検証・テスト戦略

**作成日**: 2025-05-29
**目的**: 修正されたwarifuriの依存関係解決機能を包括的に検証する
**スコープ**: 複数のサンプルプロジェクトによる実践的テスト

---

## 🎯 検証目標

### 1. 修正の完全性確認
- [x] **基本ケース**: 単一依存関係 + 単一inputファイル
- [ ] **複雑ケース**: 複数依存関係 + 複数inputファイル
- [ ] **エッジケース**: 深い依存チェーン、条件分岐

### 2. 回帰テスト
- [ ] 既存機能が破損していないことを確認
- [ ] パフォーマンスの劣化がないことを確認
- [ ] エラーハンドリングが適切に動作することを確認

### 3. 実用性検証
- [ ] 実際のワークフローでの使用感
- [ ] CI/CDパイプラインでの動作
- [ ] 大規模プロジェクトでのスケーラビリティ

---

## 📂 サンプルプロジェクト戦略

### カテゴリ1: 基本機能検証
```
workspace/
├── projects/
│   ├── basic-dependency/           # 基本的な依存関係
│   │   ├── foundation/            # 基盤タスク
│   │   └── dependent/             # 依存タスク
│   ├── multiple-inputs/           # 複数inputファイル
│   │   ├── data-source-1/
│   │   ├── data-source-2/
│   │   └── aggregator/
│   └── chain-dependency/          # チェーン状依存関係
│       ├── step-1/
│       ├── step-2/
│       ├── step-3/
│       └── final/
```

### カテゴリ2: エッジケース検証
```
workspace/
├── projects/
│   ├── deep-chain/                # 深い依存チェーン (5+ レベル)
│   ├── diamond-dependency/        # ダイアモンド型依存関係
│   ├── missing-files/             # 存在しないファイル参照
│   ├── subdirectory-files/        # サブディレクトリ内のファイル
│   └── mixed-task-types/          # machine/ai/human混在
```

### カテゴリ3: 実用シナリオ
```
workspace/
├── projects/
│   ├── data-pipeline/             # データパイプライン
│   │   ├── extract/
│   │   ├── transform/
│   │   ├── validate/
│   │   └── load/
│   ├── ml-workflow/               # 機械学習ワークフロー
│   │   ├── data-prep/
│   │   ├── feature-engineering/
│   │   ├── model-training/
│   │   └── evaluation/
│   └── documentation-gen/         # ドキュメント生成
│       ├── code-analysis/
│       ├── api-docs/
│       └── user-manual/
```

---

## 🧪 テストシナリオ詳細

### シナリオ1: 基本依存関係 (basic-dependency)
**目的**: 最もシンプルなケースでの動作確認
```yaml
# foundation/instruction.yaml
name: foundation
dependencies: []
inputs: []
outputs: ["base_data.json"]

# dependent/instruction.yaml
name: dependent
dependencies: ["foundation"]
inputs: ["base_data.json"]
outputs: ["processed_data.json"]
```
**検証項目**:
- [ ] foundationタスク完了後、dependentがPENDING
- [ ] base_data.json作成後、dependentがREADY
- [ ] warifuri listで正しいステータス表示
- [ ] warifuri validateでエラーなし

### シナリオ2: 複数inputファイル (multiple-inputs)
**目的**: 複数ファイル依存の処理確認
```yaml
# aggregator/instruction.yaml
name: aggregator
dependencies: ["data-source-1", "data-source-2"]
inputs:
  - "source1_output.csv"
  - "source2_output.csv"
  - "config/settings.json"
outputs: ["aggregated_result.json"]
```
**検証項目**:
- [ ] 部分的なファイル存在での動作
- [ ] 全ファイル揃った時点でのREADY状態遷移
- [ ] サブディレクトリ内ファイルの正しい解決

### シナリオ3: 深い依存チェーン (deep-chain)
**目的**: スケーラビリティとパフォーマンス確認
```
step-1 → step-2 → step-3 → step-4 → step-5 → final
```
**検証項目**:
- [ ] 順次実行での正しい状態遷移
- [ ] 中間ステップでの停止・再開
- [ ] パフォーマンス測定 (>100タスクでの動作)

### シナリオ4: ダイアモンド型依存関係 (diamond-dependency)
**目的**: 複雑な依存関係グラフでの動作確認
```
     foundation
     /        \
   left      right
     \        /
      merger
```
**検証項目**:
- [ ] 並列実行可能性の確認
- [ ] 最終タスクの実行タイミング
- [ ] 状態管理の一貫性

---

## 🔍 検証方法

### 自動テスト
```bash
# 基本機能テスト
pytest tests/test_sample_projects.py

# パフォーマンステスト
pytest tests/test_performance.py

# 統合テスト
pytest tests/test_integration_scenarios.py
```

### 手動検証
```bash
# 各サンプルプロジェクトでの動作確認
cd samples/basic-dependency
warifuri list
warifuri validate
warifuri run --dry-run

# ワークフロー実行
warifuri run
```

### デバッグ手順
1. **状態確認**: `warifuri list --format json`でタスク状態詳細取得
2. **依存関係確認**: `warifuri graph --format ascii`で依存グラフ表示
3. **ファイル確認**: 各inputファイルの存在とパス確認
4. **ログ確認**: 実行ログでエラー内容詳細確認

---

## 📊 成功指標

### 機能的指標
- [ ] **100% シナリオ通過**: 全テストシナリオでの期待動作
- [ ] **0 回帰バグ**: 既存機能への影響なし
- [ ] **適切なエラーメッセージ**: 問題発生時の分かりやすいフィードバック

### 非機能的指標
- [ ] **パフォーマンス維持**: 100タスクプロジェクトで<2秒処理
- [ ] **メモリ効率**: 大規模プロジェクトでのメモリリーク なし
- [ ] **使いやすさ**: 直感的なエラーメッセージとワークフロー

---

## 🗂️ ドキュメント構成

```
docs/
├── validation/
│   ├── sample-projects-overview.md        # このドキュメント
│   ├── test-scenarios-detailed.md         # 詳細テストシナリオ
│   ├── verification-results.md            # 検証結果レポート
│   └── performance-benchmarks.md          # パフォーマンス測定結果
└── samples/
    ├── basic-dependency/
    ├── multiple-inputs/
    ├── deep-chain/
    └── [other scenarios]/
```

---

## 🚀 実行計画

### Phase 1: サンプルプロジェクト作成 (今回)
- [x] 基本依存関係プロジェクト
- [ ] 複数inputファイルプロジェクト
- [ ] チェーン依存関係プロジェクト

### Phase 2: 基本検証
- [ ] 各サンプルでの動作確認
- [ ] 手動テスト実行
- [ ] 問題点の特定・修正

### Phase 3: 高度なテスト
- [ ] エッジケース検証
- [ ] パフォーマンステスト
- [ ] 統合テスト

### Phase 4: ドキュメント化
- [ ] 検証結果レポート作成
- [ ] ベストプラクティス文書化
- [ ] ユーザガイド更新

---

**次のアクション**: Phase 1のサンプルプロジェクト作成を開始
