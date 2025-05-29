# Cross-Project Dependencies

## 概要

プロジェクト間の依存関係を検証するサンプル。
core プロジェクトが共有設定を生成し、app プロジェクトがそれを使用する。

## プロジェクト構造

```
cross-project/
├── README.md
├── project-core.yaml        # 共有機能プロジェクト
├── project-app.yaml         # アプリケーションプロジェクト
└── scripts/
    ├── core_config.py
    ├── core_library.py
    ├── app_main.py
    └── app_validator.py
```

## プロジェクト構成

### core プロジェクト
共有機能を提供するプロジェクト

#### config-generator タスク
- **入力**: なし
- **出力**: `shared.conf`, `version.txt`
- **依存**: なし
- **処理**: 共有設定ファイルの生成

#### library-builder タスク
- **入力**: `shared.conf`
- **出力**: `core_lib.json`
- **依存**: `config-generator`
- **処理**: 設定に基づいてライブラリ情報を構築

### app プロジェクト
core プロジェクトの出力を使用するアプリケーション

#### main-app タスク
- **入力**: `shared.conf`, `core_lib.json`
- **出力**: `app_output.txt`
- **依存**: `core/library-builder`
- **処理**: core の出力を使用してアプリケーション処理

#### validator タスク
- **入力**: `app_output.txt`, `version.txt`
- **出力**: `validation_report.txt`
- **依存**: `main-app`, `core/config-generator`
- **処理**: アプリケーション出力とバージョン情報の検証

## 検証ポイント

1. **プロジェクト間依存**: `core/task-name` 形式での依存関係指定
2. **依存関係名前解決**: 短縮名から完全名への変換（`core/library-builder`）
3. **複数プロジェクト並行**: 異なるプロジェクトのタスクが同時実行可能
4. **共有ファイル**: 複数プロジェクトが同じファイルを参照

## 期待される動作

### 初期状態
```
core/config-generator: READY
core/library-builder: PENDING (shared.conf なし)
app/main-app: PENDING (shared.conf, core_lib.json なし)
app/validator: PENDING (app_output.txt, version.txt なし)
```

### core/config-generator 実行後
```
core/config-generator: COMPLETED
core/library-builder: READY (shared.conf 存在)
app/main-app: PENDING (core_lib.json なし)
app/validator: PENDING (app_output.txt なし、version.txt 存在)
```

### core/library-builder 実行後
```
core/config-generator: COMPLETED
core/library-builder: COMPLETED
app/main-app: READY (shared.conf, core_lib.json 存在)
app/validator: PENDING (app_output.txt なし)
```

### app/main-app 実行後
```
core/config-generator: COMPLETED
core/library-builder: COMPLETED
app/main-app: COMPLETED
app/validator: READY (app_output.txt, version.txt 存在)
```

## テストシナリオ

1. **正常フロー**: core → app の順序実行
2. **部分実行**: core のみ実行後の状態確認
3. **依存関係名前解決**: 短縮名・完全名の混在テスト
4. **共有ファイル削除**: 中間ファイル削除時の影響確認
