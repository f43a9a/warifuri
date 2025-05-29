# Warifuri Cross-Project Integration - 実装計画詳細

## 1. システムインストール版への統合

### 現在の問題点分析

```bash
# 現在の開発環境での実行
cd /workspace/sample-projects/cross-project
PYTHONPATH=/workspace/src python -m warifuri run --task core/library-builder

# 理想的なプロダクション環境での実行
cd /path/to/user/project
warifuri run --task core/library-builder
```

### 統合手順

#### Step 1: パッケージング準備
```python
# pyproject.toml更新例
[tool.poetry]
name = "warifuri"
version = "0.3.0"  # クロスプロジェクト対応版
description = "Task automation with cross-project dependency resolution"

[tool.poetry.dependencies]
python = "^3.8"
click = "^8.0"
pyyaml = "^6.0"
# ... 既存の依存関係

[tool.poetry.scripts]
warifuri = "warifuri.__main__:main"
```

#### Step 2: リリース検証スクリプト
```bash
#!/bin/bash
# scripts/test_release.sh

echo "=== Testing Release Package ==="

# 1. 仮想環境作成
python -m venv test_env
source test_env/bin/activate

# 2. パッケージインストール
pip install dist/warifuri-*.whl

# 3. クロスプロジェクトテスト実行
cd sample-projects/cross-project
warifuri list
warifuri run --task core/config-generator
warifuri run --task core/library-builder
warifuri run --task app/main-app

# 4. 結果検証
if [ -f "projects/app/main-app/app_output.txt" ]; then
    echo "✅ Cross-project dependencies working correctly"
else
    echo "❌ Cross-project dependencies failed"
    exit 1
fi

deactivate
rm -rf test_env
```

## 2. 複雑な依存関係グラフのテスト

### テストケース構造

```
sample-projects/
└── complex-dependencies/
    ├── diamond-pattern/
    │   └── projects/
    │       ├── shared/
    │       │   └── config-base/
    │       ├── services/
    │       │   ├── service-a/
    │       │   └── service-b/
    │       └── integration/
    │           └── end-to-end-test/
    ├── deep-chain/
    │   └── projects/
    │       ├── layer-1/
    │       ├── layer-2/
    │       ├── layer-3/
    │       └── layer-4/
    └── parallel-execution/
        └── projects/
            ├── data-source/
            ├── processor-a/
            ├── processor-b/
            └── aggregator/
```

### ダイアモンド依存関係テスト

```yaml
# diamond-pattern/projects/shared/config-base/instruction.yaml
name: config-base
description: Generate base configuration
outputs:
  - base.conf
  - secrets.env

---
# diamond-pattern/projects/services/service-a/instruction.yaml
name: service-a
description: Service A processing
dependencies:
  - shared/config-base
inputs:
  - ../shared/config-base/base.conf
outputs:
  - service_a_data.json

---
# diamond-pattern/projects/services/service-b/instruction.yaml
name: service-b
description: Service B processing
dependencies:
  - shared/config-base
inputs:
  - ../shared/config-base/base.conf
outputs:
  - service_b_data.json

---
# diamond-pattern/projects/integration/end-to-end-test/instruction.yaml
name: end-to-end-test
description: Integration test using both services
dependencies:
  - services/service-a
  - services/service-b
inputs:
  - ../services/service-a/service_a_data.json
  - ../services/service-b/service_b_data.json
outputs:
  - integration_results.json
```

### 循環依存検出テスト

```python
# tests/integration/test_circular_dependency_detection.py
import pytest
from warifuri.core.discovery import discover_tasks
from warifuri.core.execution import find_ready_tasks
from warifuri.exceptions import CircularDependencyError

def test_circular_dependency_detection():
    """循環依存関係の検出テスト"""

    # 循環依存のあるプロジェクト構造を作成
    circular_project = create_circular_dependency_project()

    with pytest.raises(CircularDependencyError) as exc_info:
        projects = discover_tasks(circular_project)
        find_ready_tasks(projects)

    assert "Circular dependency detected" in str(exc_info.value)
    assert "task-a → task-b → task-a" in str(exc_info.value)

def create_circular_dependency_project():
    """循環依存のテストプロジェクト作成"""
    # テンポラリディレクトリに循環依存構造を作成
    pass
```

## 3. 自動的な出力→入力マッピング機能

### 現在の手動マッピング vs 自動マッピング

```yaml
# ========== 現在の手動マッピング ==========
# library-builder/instruction.yaml
name: library-builder
dependencies:
  - config-generator
inputs:
  - ../config-generator/shared.conf  # 手動指定

# ========== 理想的な自動マッピング ==========
# library-builder/instruction.yaml
name: library-builder
dependencies:
  - config-generator  # 自動的にshared.confがマップされる
auto_import: true
import_patterns:
  - "*.conf"
  - "*.json"
exclude_patterns:
  - "*.log"
  - "*.tmp"
```

### 実装アプローチ

#### A. 出力ディスカバリー機能

```python
# src/warifuri/core/auto_mapping.py
from typing import Dict, List, Set
from pathlib import Path
import re

class OutputDiscovery:
    """タスクの出力ファイルを自動検出する"""

    def discover_task_outputs(self, task: Task) -> Dict[str, Path]:
        """タスクの出力ファイルを検出"""
        outputs = {}

        # 1. instruction.yamlの明示的な出力
        if task.instruction and task.instruction.outputs:
            for output in task.instruction.outputs:
                output_path = task.path / output
                if output_path.exists():
                    outputs[output] = output_path

        # 2. 実行ログからの動的検出
        log_outputs = self._discover_from_execution_log(task)
        outputs.update(log_outputs)

        # 3. ファイルシステムスキャン（パターンベース）
        fs_outputs = self._scan_filesystem_outputs(task)
        outputs.update(fs_outputs)

        return outputs

    def _discover_from_execution_log(self, task: Task) -> Dict[str, Path]:
        """実行ログから出力ファイルを検出"""
        outputs = {}
        log_file = task.path / "logs" / "execution.log"

        if not log_file.exists():
            return outputs

        # ログから "Created: filename" のようなパターンを検出
        create_patterns = [
            r"Created:\s+(.+)",
            r"Generated:\s+(.+)",
            r"Output:\s+(.+)",
            r"Wrote:\s+(.+)"
        ]

        with open(log_file, 'r') as f:
            for line in f:
                for pattern in create_patterns:
                    match = re.search(pattern, line)
                    if match:
                        filename = match.group(1).strip()
                        file_path = task.path / filename
                        if file_path.exists():
                            outputs[filename] = file_path

        return outputs

    def _scan_filesystem_outputs(self, task: Task) -> Dict[str, Path]:
        """ファイルシステムをスキャンして出力ファイルを検出"""
        outputs = {}

        # タスクディレクトリ内の新しいファイルを検出
        # (done.mdより新しいファイル)
        done_file = task.path / "done.md"
        if not done_file.exists():
            return outputs

        done_time = done_file.stat().st_mtime

        for file_path in task.path.rglob("*"):
            if (file_path.is_file() and
                file_path.stat().st_mtime > done_time and
                not self._is_system_file(file_path)):

                relative_path = file_path.relative_to(task.path)
                outputs[str(relative_path)] = file_path

        return outputs

    def _is_system_file(self, file_path: Path) -> bool:
        """システムファイル（ログ、一時ファイルなど）かどうか判定"""
        system_patterns = [
            "*.log", "*.tmp", "*.cache",
            "logs/*", "__pycache__/*", "*.pyc"
        ]

        for pattern in system_patterns:
            if file_path.match(pattern):
                return True

        return False

class AutoInputResolver:
    """依存関係から入力を自動解決する"""

    def __init__(self):
        self.discovery = OutputDiscovery()

    def resolve_auto_imports(self, task: Task, dependencies: List[Task]) -> List[str]:
        """依存タスクから自動的に入力を解決"""
        auto_inputs = []

        # タスクの自動インポート設定を取得
        auto_config = self._get_auto_import_config(task)
        if not auto_config.enabled:
            return auto_inputs

        for dep_task in dependencies:
            dep_outputs = self.discovery.discover_task_outputs(dep_task)

            for output_name, output_path in dep_outputs.items():
                if self._should_import_file(output_name, auto_config):
                    relative_path = self._compute_relative_path(
                        task.path, output_path
                    )
                    auto_inputs.append(relative_path)

        return auto_inputs

    def _get_auto_import_config(self, task: Task) -> 'AutoImportConfig':
        """タスクの自動インポート設定を取得"""
        instruction = task.instruction
        if not instruction:
            return AutoImportConfig(enabled=False)

        # instruction.yamlから設定を読み込み
        auto_import = getattr(instruction, 'auto_import', False)
        import_patterns = getattr(instruction, 'import_patterns', ['*'])
        exclude_patterns = getattr(instruction, 'exclude_patterns', [])

        return AutoImportConfig(
            enabled=auto_import,
            import_patterns=import_patterns,
            exclude_patterns=exclude_patterns
        )

    def _should_import_file(self, filename: str, config: 'AutoImportConfig') -> bool:
        """ファイルをインポートすべきかどうか判定"""
        # 除外パターンチェック
        for exclude_pattern in config.exclude_patterns:
            if Path(filename).match(exclude_pattern):
                return False

        # インポートパターンチェック
        for import_pattern in config.import_patterns:
            if Path(filename).match(import_pattern):
                return True

        return False

    def _compute_relative_path(self, task_path: Path, output_path: Path) -> str:
        """タスクパスから出力パスへの相対パスを計算"""
        try:
            # projects/ ディレクトリからの相対パス計算
            projects_base = task_path.parent.parent
            relative_from_projects = output_path.relative_to(projects_base)
            return f"../{relative_from_projects}"
        except ValueError:
            # フォールバック: 絶対パス
            return str(output_path)

@dataclass
class AutoImportConfig:
    """自動インポートの設定"""
    enabled: bool
    import_patterns: List[str] = field(default_factory=lambda: ['*'])
    exclude_patterns: List[str] = field(default_factory=list)
```

#### B. 拡張されたinstruction.yaml形式

```yaml
# 基本的な自動インポート
name: data-processor
dependencies:
  - data-source
auto_import: true

---
# 詳細な自動インポート設定
name: report-generator
dependencies:
  - data-processor
  - config-manager
auto_import: true
import_patterns:
  - "*.json"
  - "*.csv"
  - "config/*.conf"
exclude_patterns:
  - "*.log"
  - "*.tmp"
  - "debug/*"

---
# 依存関係ごとの個別設定
name: complex-processor
dependencies:
  - task: data-source
    auto_import: true
    import_patterns: ["*.csv", "*.json"]
  - task: config-manager
    auto_import: true
    import_patterns: ["*.conf"]
    exclude_patterns: ["*.secret"]
manual_inputs:
  - ../other-project/manual-file.txt
```

## 4. 包括的テストスイート

### テスト構造

```
tests/
├── unit/
│   ├── test_path_resolution.py
│   ├── test_auto_mapping.py
│   ├── test_output_discovery.py
│   └── test_validation.py
├── integration/
│   ├── test_cross_project_workflows.py
│   ├── test_complex_dependencies.py
│   ├── test_parallel_execution.py
│   └── test_error_handling.py
├── e2e/
│   ├── test_real_world_scenarios.py
│   ├── test_microservice_pipeline.py
│   └── test_data_processing_workflow.py
├── performance/
│   ├── test_large_dependency_graphs.py
│   └── test_concurrent_execution.py
└── fixtures/
    ├── simple-chain/
    ├── cross-project/
    ├── diamond-dependencies/
    ├── deep-chain/
    └── parallel-execution/
```

### 主要テストケース例

```python
# tests/integration/test_cross_project_workflows.py
import pytest
from pathlib import Path
from warifuri.core.discovery import discover_tasks
from warifuri.core.execution import find_ready_tasks, execute_task

class TestCrossProjectWorkflows:

    @pytest.fixture
    def cross_project_workspace(self, tmp_path):
        """クロスプロジェクトのテストワークスペースを作成"""
        return create_cross_project_test_workspace(tmp_path)

    def test_linear_cross_project_execution(self, cross_project_workspace):
        """線形クロスプロジェクト実行テスト"""
        workspace_path = cross_project_workspace

        # タスク発見
        projects = discover_tasks(workspace_path)
        assert len(projects) == 2  # core, app

        # 実行順序テスト
        ready_tasks = find_ready_tasks(projects, workspace_path)
        assert len(ready_tasks) == 1
        assert ready_tasks[0].name == "config-generator"

        # 最初のタスク実行
        execute_task(ready_tasks[0], workspace_path)

        # 次のタスクが準備完了になることを確認
        ready_tasks = find_ready_tasks(projects, workspace_path)
        assert len(ready_tasks) == 1
        assert ready_tasks[0].name == "library-builder"

    def test_diamond_dependency_resolution(self, diamond_workspace):
        """ダイアモンド依存関係の解決テスト"""
        # 共通の基底タスク実行後、
        # 複数の依存タスクが並列実行可能になることを確認
        pass

    def test_cross_project_file_copying(self, cross_project_workspace):
        """クロスプロジェクトファイルコピーテスト"""
        # ファイルが正しい場所にコピーされることを確認
        # 相対パス構造が保持されることを確認
        pass

    def test_missing_dependency_error_handling(self, cross_project_workspace):
        """存在しない依存ファイルのエラーハンドリング"""
        # 依存ファイルが存在しない場合の適切なエラー処理
        pass

# tests/unit/test_auto_mapping.py
class TestAutoMapping:

    def test_output_discovery_from_instruction(self):
        """instruction.yamlからの出力検出テスト"""
        pass

    def test_output_discovery_from_execution_log(self):
        """実行ログからの出力検出テスト"""
        pass

    def test_filesystem_output_scanning(self):
        """ファイルシステムスキャンによる出力検出テスト"""
        pass

    def test_auto_import_pattern_matching(self):
        """自動インポートパターンマッチングテスト"""
        pass

    def test_exclude_pattern_filtering(self):
        """除外パターンフィルタリングテスト"""
        pass

# tests/performance/test_scalability.py
class TestScalability:

    def test_large_dependency_graph_performance(self):
        """大規模依存グラフ（100+タスク）のパフォーマンステスト"""
        # 100個以上のタスクを持つ依存グラフを生成
        # 実行時間が許容範囲内であることを確認
        pass

    def test_deep_dependency_chain_performance(self):
        """深い依存チェーン（20+レベル）のパフォーマンステスト"""
        pass

    def test_concurrent_execution_scalability(self):
        """並行実行のスケーラビリティテスト"""
        # 複数タスクの並列実行性能
        pass
```

### CI/CD統合

```yaml
# .github/workflows/comprehensive-test.yml
name: Comprehensive Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install poetry
        poetry install

    - name: Run unit tests
      run: |
        poetry run pytest tests/unit/ -v --cov=warifuri

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install poetry
        poetry install

    - name: Run integration tests
      run: |
        poetry run pytest tests/integration/ -v

    - name: Run E2E tests
      run: |
        poetry run pytest tests/e2e/ -v

  performance-tests:
    runs-on: ubuntu-latest
    needs: integration-tests

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install poetry
        poetry install

    - name: Run performance tests
      run: |
        poetry run pytest tests/performance/ -v --benchmark-only

  release-test:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9

    - name: Build package
      run: |
        python -m pip install --upgrade pip
        pip install poetry
        poetry build

    - name: Test package installation
      run: |
        pip install dist/*.whl
        warifuri --version

    - name: Test cross-project functionality
      run: |
        cd sample-projects/cross-project
        warifuri list
        warifuri run --task core/config-generator
        warifuri run --task core/library-builder
        warifuri run --task app/main-app

        # Verify outputs
        test -f projects/app/main-app/app_output.txt
        echo "✅ Cross-project dependencies working in release package"
```

この実装計画により、warifuriのクロスプロジェクト機能は本格的なプロダクション環境で利用可能になります。
