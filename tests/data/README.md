# Test Data Specification

## Overview

このディレクトリには、統合テストおよびE2Eテストで使用するYAMLベースのテストデータサンプルが含まれています。

## File Structure

```
tests/data/
├── README.md           # このファイル - 仕様説明
├── tasks/              # タスク定義サンプル
│   ├── simple_task.yaml
│   ├── complex_task.yaml
│   ├── dependency_chain.yaml
│   └── error_cases.yaml
├── projects/           # プロジェクト構造サンプル
│   ├── single_project.yaml
│   ├── multi_project.yaml
│   └── cross_dependency.yaml
├── workflows/          # ワークフロー設定サンプル
│   ├── automation_basic.yaml
│   ├── automation_advanced.yaml
│   └── ci_integration.yaml
└── schemas/            # スキーマ定義
    ├── task_schema.yaml
    ├── project_schema.yaml
    └── workflow_schema.yaml
```

## Data Categories

### 1. Task Definition Samples (`tasks/`)

タスク定義の各種パターンを含むサンプルデータ：

- **simple_task.yaml**: 基本的なタスク定義
- **complex_task.yaml**: 複雑な依存関係を持つタスク
- **dependency_chain.yaml**: 連鎖する依存関係のテストケース
- **error_cases.yaml**: エラーケース（無効なYAML、欠損フィールドなど）

### 2. Project Structure Samples (`projects/`)

プロジェクト構造の各種パターン：

- **single_project.yaml**: 単一プロジェクトの基本構造
- **multi_project.yaml**: 複数プロジェクトの構成
- **cross_dependency.yaml**: クロスプロジェクト依存関係

### 3. Workflow Configuration Samples (`workflows/`)

自動化ワークフローの設定例：

- **automation_basic.yaml**: 基本的な自動化設定
- **automation_advanced.yaml**: 高度な自動化設定（条件分岐、エラーハンドリング）
- **ci_integration.yaml**: CI/CD統合設定

### 4. Schema Definitions (`schemas/`)

各データ形式のスキーマ定義：

- **task_schema.yaml**: タスク定義のスキーマ
- **project_schema.yaml**: プロジェクト構造のスキーマ
- **workflow_schema.yaml**: ワークフロー設定のスキーマ

## Usage in Tests

### Loading Test Data

```python
import yaml
from pathlib import Path

def load_test_data(filename: str) -> dict:
    """テストデータを読み込む"""
    data_path = Path(__file__).parent / "data" / filename
    with open(data_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 使用例
task_data = load_test_data("tasks/simple_task.yaml")
project_data = load_test_data("projects/single_project.yaml")
```

### Parameterized Tests

```python
import pytest

@pytest.mark.parametrize("task_file", [
    "tasks/simple_task.yaml",
    "tasks/complex_task.yaml",
    "tasks/dependency_chain.yaml"
])
def test_task_processing(task_file):
    """複数のタスクファイルを使ってテスト"""
    task_data = load_test_data(task_file)
    # テストロジック
```

## Data Validation

すべてのテストデータは以下の条件を満たす必要があります：

1. **Valid YAML**: 正しいYAML形式である
2. **Schema Compliance**: 対応するスキーマに準拠している
3. **Realistic Data**: 実際の使用シナリオを反映している
4. **Edge Cases**: 境界値やエラーケースを含む
5. **Documentation**: 各ファイルにコメントで説明を記述

## Maintenance

- テストデータは定期的にレビューし、新機能に合わせて更新する
- 新しいテストケースが必要な場合は、対応するサンプルファイルを追加する
- スキーマ変更時は、すべてのサンプルデータの互換性を確認する
