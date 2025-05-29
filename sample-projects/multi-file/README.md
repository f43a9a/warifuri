# Multi-File Dependencies

## 概要

複数ファイルの依存関係を検証するプロジェクト。
generator タスクが複数ファイルを出力し、processor タスクがそれらすべてを入力として使用する。

## プロジェクト構造

```
multi-file/
├── README.md
├── project-multifile.yaml
└── scripts/
    ├── generator.py
    └── processor.py
```

## タスク構成

### generator タスク
- **入力**: なし
- **出力**: `data1.txt`, `data2.txt`, `config.json`
- **依存**: なし
- **処理**: 複数の異なる形式のファイルを生成

### processor タスク
- **入力**: `data1.txt`, `data2.txt`, `config.json`
- **出力**: `summary.txt`
- **依存**: `generator`
- **処理**: すべての入力ファイルを読み込んで統合処理

## 検証ポイント

1. **複数ファイル依存**: すべてのファイルが揃うまで PENDING 状態を維持
2. **異なるファイル形式**: テキスト・JSON の混合処理
3. **部分ファイル存在**: 一部ファイルのみ存在する場合の動作
4. **ファイル検証**: `validate_file_references()` での複数ファイルチェック

## 期待される動作

### 初期状態
```
generator: READY (依存なし)
processor: PENDING (入力ファイルが存在しない)
```

### generator 実行後（全ファイル生成）
```
generator: COMPLETED
processor: READY (すべての入力ファイルが存在)
```

### 部分ファイル存在の場合
```
generator: COMPLETED (data1.txt のみ存在)
processor: PENDING (data2.txt, config.json が不足)
```

## テストシナリオ

1. **正常フロー**: generator → processor の順序実行
2. **部分ファイルテスト**: 一部ファイル削除時の processor 状態
3. **ファイル形式検証**: JSON ファイルの構文エラー処理
4. **大量ファイル**: 10個以上のファイル依存でのパフォーマンス
