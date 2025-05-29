# Simple Dependency Chain

## 概要

最もシンプルな依存関係のパターンを検証するプロジェクト。
foundation タスクが base.txt を生成し、consumer タスクがそれを入力として使用する。

## プロジェクト構造

```
simple-chain/
├── README.md
├── project-simple.yaml
└── scripts/
    ├── foundation.py
    └── consumer.py
```

## タスク構成

### foundation タスク
- **入力**: なし
- **出力**: `base.txt`
- **依存**: なし
- **処理**: シンプルなテキストファイルを生成

### consumer タスク
- **入力**: `base.txt`
- **出力**: `processed.txt`
- **依存**: `foundation`
- **処理**: base.txt の内容を読み込んで加工

## 検証ポイント

1. **基本的な依存関係解決**: foundation → consumer の順序で実行される
2. **ファイルパス解決**: `base.txt` がワークスペースルートで正しく見つかる
3. **状態遷移**: foundation 完了後、consumer が PENDING → READY に変わる
4. **入力ファイル検証**: consumer が base.txt の存在を正しく確認する

## 期待される動作

### 初期状態
```
foundation: READY (依存なし)
consumer: PENDING (base.txt が存在しない)
```

### foundation 実行後
```
foundation: COMPLETED
consumer: READY (base.txt が存在する)
```

### consumer 実行後
```
foundation: COMPLETED
consumer: COMPLETED
```

## テストシナリオ

1. **正常フロー**: foundation → consumer の順序実行
2. **ファイル削除テスト**: base.txt を削除した場合の consumer 状態
3. **部分実行**: foundation のみ実行後の状態確認
4. **リセットテスト**: 出力ファイル削除後の状態復旧
