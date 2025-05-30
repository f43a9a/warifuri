# 🔍 Warifuri 包括的バグ調査計画

## 🎯 調査目的

今回のクロスプロジェクト依存解決バグのような基本的・構造的問題を体系的に発見し、修正することで、warifuriの堅牢性と信頼性を向上させる。

## 🚨 発見された深刻な問題

### 1. **型安全性の破綻** (Critical)

#### 問題詳細
```python
# src/warifuri/cli/commands/template.py:30
workspace_path = ctx.workspace_path  # Path | None
templates_dir = workspace_path / "templates"  # Type error!
```

**影響**: `ctx.workspace_path`が`None`の場合、実行時エラーが発生する可能性

#### 影響ファイル
- `src/warifuri/cli/commands/template.py`
- `src/warifuri/cli/commands/validate.py`
- `src/warifuri/cli/commands/show.py`
- `src/warifuri/cli/commands/run.py`
- `src/warifuri/cli/commands/mark_done.py`
- `src/warifuri/cli/commands/list.py`
- `src/warifuri/cli/commands/issue.py`
- `src/warifuri/cli/commands/init.py`
- `src/warifuri/cli/commands/graph.py`

### 2. **例外処理の不適切な抑制** (High)

#### 問題パターン
```python
# 禁止パターン1: 無言で失敗を握りつぶす
try:
    templates = [d.name for d in templates_dir.iterdir() if d.is_dir()]
except Exception:  # 具体的な例外を指定せず
    templates = []  # 静かに空リストを返す

# 禁止パターン2: Gitエラーを隠蔽
except Exception:
    return None  # エラーの原因が分からない
```

**影響**: デバッグが困難になり、サイレントな機能停止が発生

### 3. **ファイルパス処理の脆弱性** (Medium)

#### 問題パターン
```python
# 危険なパス操作
clean_path = input_file.replace("../", "")  # 単純な文字列置換
while clean_path.startswith("../"):         # 無限ループの可能性
    clean_path = clean_path[3:]             # 範囲外アクセスリスク
```

**影響**: パス・トラバーサル攻撃、予期しないファイルアクセス

### 4. **競合状態と原子性の欠如** (Medium)

#### 問題パターン
```python
# done.mdの競合状態
if not (task.path / "done.md").exists():  # チェック
    # 別プロセスがここでdone.mdを作成する可能性
    execute_task(task)                    # 実行
    create_done_file(task)               # 作成
```

**影響**: 同一タスクの重複実行、データ競合

## 📋 詳細調査計画

### Phase 1: Critical Issues (即座対応)

#### 1.1 型安全性の完全修復
- [ ] `Context.workspace_path`のNull安全性確保
- [ ] すべてのCLIコマンドで`workspace_path`が`None`の場合の適切なエラーハンドリング
- [ ] `mypy --strict`の完全通過

#### 1.2 例外処理の標準化
- [ ] 具体的な例外クラスの指定
- [ ] ログ出力の追加
- [ ] サイレント失敗の排除

### Phase 2: High Priority (1週間以内)

#### 2.1 ファイルパス処理の強化
- [ ] `pathlib.Path.resolve()`による正規化
- [ ] パス・トラバーサル攻撃対策
- [ ] Windows/Linux互換性確保

#### 2.2 並行性・競合状態対策
- [ ] ファイルロック機構の導入
- [ ] 原子性操作の実装
- [ ] プロセス間競合の検出・対策

#### 2.3 セキュリティ強化
- [ ] 入力値検証の統一
- [ ] 権限チェック機能
- [ ] サンドボックス強化

### Phase 3: Medium Priority (2週間以内)

#### 3.1 エラー処理の改善
- [ ] 構造化ログの導入
- [ ] エラー回復機能
- [ ] ユーザーフレンドリーなエラーメッセージ

#### 3.2 パフォーマンス問題
- [ ] 大規模依存グラフでの性能テスト
- [ ] メモリリーク検出
- [ ] I/O最適化

#### 3.3 テストカバレッジ拡張
- [ ] エッジケースの網羅
- [ ] 統合テスト強化
- [ ] 性能回帰テスト

## 🛠️ 修正手順テンプレート

### 型安全性修正パターン
```python
# Before (危険)
def command(ctx: Context) -> None:
    workspace_path = ctx.workspace_path
    result = workspace_path / "file"  # Type error!

# After (安全)
def command(ctx: Context) -> None:
    workspace_path = ctx.ensure_workspace_path()  # raises if None
    result = workspace_path / "file"  # Type safe!
```

### 例外処理修正パターン
```python
# Before (危険)
try:
    risky_operation()
except Exception:
    return default_value

# After (安全)
try:
    risky_operation()
except SpecificError as e:
    logger.warning("Operation failed: %s", e)
    return default_value
except AnotherError as e:
    logger.error("Critical error: %s", e)
    raise
```

### ファイル操作修正パターン
```python
# Before (脆弱)
clean_path = input_file.replace("../", "")

# After (安全)
try:
    resolved_path = (base_path / input_file).resolve()
    if not resolved_path.is_relative_to(base_path):
        raise SecurityError("Path traversal detected")
    return resolved_path
except (OSError, ValueError) as e:
    raise PathResolutionError(f"Invalid path: {input_file}") from e
```

## 🔄 継続的品質保証

### 自動化されたチェック
- [ ] pre-commit hookでの型チェック強化
- [ ] CI/CDでのセキュリティスキャン
- [ ] パフォーマンスベンチマーク
- [ ] メモリリーク検出

### コードレビュー基準
- [ ] 型安全性の必須確保
- [ ] 例外処理の標準パターン遵守
- [ ] セキュリティベストプラクティス適用
- [ ] テストカバレッジ要件

## 📊 進捗トラッキング

### Critical Issues (0/2 完了)
- [ ] 型安全性修復
- [ ] 例外処理標準化

### High Priority (0/4 完了)
- [ ] ファイルパス処理強化
- [ ] 並行性対策
- [ ] セキュリティ強化
- [ ] エラー処理改善

### Medium Priority (0/3 完了)
- [ ] パフォーマンス最適化
- [ ] テストカバレッジ拡張
- [ ] ドキュメント整備

## 🎯 最終目標

**堅牢性**: 型安全性100%、例外処理の標準化
**セキュリティ**: パス・トラバーサル対策、入力値検証
**信頼性**: 競合状態対策、原子性保証
**保守性**: 構造化ログ、明確なエラーメッセージ

この調査により、warifuriは次のレベルの品質と信頼性を達成する。
