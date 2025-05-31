"""
Test comprehensive schema validation and cross-reference validation
包括的スキーマ検証およびクロスリファレンス検証テスト
"""

import json
import yaml
from pathlib import Path
import pytest


class DataLoader:
    """テストデータローダーユーティリティ"""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def load_yaml(self, relative_path: str):
        """YAMLファイルを読み込み"""
        file_path = self.base_path / relative_path
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_yaml_all(self, relative_path: str):
        """複数ドキュメントYAMLファイルを読み込み"""
        file_path = self.base_path / relative_path
        with open(file_path, "r", encoding="utf-8") as f:
            # First try loading as multiple documents
            documents = list(yaml.safe_load_all(f))

            # If we got exactly one document and it's a list, return the list items
            if len(documents) == 1 and isinstance(documents[0], list):
                return documents[0]

            # Otherwise return the documents as-is
            return documents

    def load_schema(self, schema_name: str):
        """スキーマファイルを読み込み"""
        return self.load_yaml(f"schemas/{schema_name}.yaml")


class TestSchemaValidation:
    """スキーマ検証テスト"""

    @pytest.fixture
    def data_loader(self):
        """データローダーフィクスチャ"""
        data_path = Path(__file__).parent.parent / "data"
        return DataLoader(data_path)

    def test_task_schema_against_simple_task(self, data_loader):
        """シンプルタスクに対するタスクスキーマ検証"""
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            pytest.skip("jsonschema not available")

        task_data = data_loader.load_yaml("tasks/simple_task.yaml")
        schema = data_loader.load_schema("task_schema")

        try:
            validate(instance=task_data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Simple task schema validation failed: {e.message}")

    def test_task_schema_against_complex_task(self, data_loader):
        """複雑タスクに対するタスクスキーマ検証"""
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            pytest.skip("jsonschema not available")

        task_data = data_loader.load_yaml("tasks/complex_task.yaml")
        schema = data_loader.load_schema("task_schema")

        try:
            validate(instance=task_data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Complex task schema validation failed: {e.message}")

    def test_task_schema_against_dependency_chain(self, data_loader):
        """依存関係チェーンに対するタスクスキーマ検証"""
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            pytest.skip("jsonschema not available")

        task_documents = data_loader.load_yaml_all("tasks/dependency_chain.yaml")
        schema = data_loader.load_schema("task_schema")

        valid_tasks = [doc for doc in task_documents if doc and isinstance(doc, dict)]
        assert len(valid_tasks) > 0, "No valid task documents found"

        for i, task_data in enumerate(valid_tasks):
            try:
                validate(instance=task_data, schema=schema)
            except ValidationError as e:
                pytest.fail(f"Dependency chain task {i} schema validation failed: {e.message}")

    def test_project_schema_against_single_project(self, data_loader):
        """単一プロジェクトに対するプロジェクトスキーマ検証"""
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            pytest.skip("jsonschema not available")

        project_data = data_loader.load_yaml("projects/single_project.yaml")
        schema = data_loader.load_schema("project_schema")

        try:
            validate(instance=project_data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Single project schema validation failed: {e.message}")

    def test_project_schema_against_multi_project(self, data_loader):
        """複数プロジェクトに対するプロジェクトスキーマ検証"""
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            pytest.skip("jsonschema not available")

        project_documents = data_loader.load_yaml_all("projects/multi_project.yaml")
        schema = data_loader.load_schema("project_schema")

        valid_projects = [doc for doc in project_documents if doc and isinstance(doc, dict)]
        assert len(valid_projects) > 0, "No valid project documents found"

        for i, project_data in enumerate(valid_projects):
            try:
                validate(instance=project_data, schema=schema)
            except ValidationError as e:
                pytest.fail(f"Multi project {i} schema validation failed: {e.message}")

    def test_workflow_schema_against_automation_basic(self, data_loader):
        """基本自動化ワークフローに対するワークフロースキーマ検証"""
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            pytest.skip("jsonschema not available")

        workflow_data = data_loader.load_yaml("workflows/automation_basic.yaml")
        schema = data_loader.load_schema("workflow_schema")

        try:
            validate(instance=workflow_data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Basic automation workflow schema validation failed: {e.message}")


class TestCrossReference:
    """クロスリファレンス検証テスト"""

    @pytest.fixture
    def data_loader(self):
        """データローダーフィクスチャ"""
        data_path = Path(__file__).parent.parent / "data"
        return DataLoader(data_path)

    def test_task_dependency_references(self, data_loader):
        """タスク依存関係リファレンス検証"""
        dependency_documents = data_loader.load_yaml_all("tasks/dependency_chain.yaml")
        valid_tasks = [doc for doc in dependency_documents if doc and isinstance(doc, dict)]

        # タスクIDとタスクの対応を作成
        task_map = {task.get('id'): task for task in valid_tasks if task.get('id')}
        task_ids = set(task_map.keys())

        # 各タスクの依存関係をチェック
        for task in valid_tasks:
            task_id = task.get('id', 'unknown')
            dependencies = task.get('dependencies', [])

            for dep in dependencies:
                # 依存関係は辞書形式（id, typeフィールドを持つ）またはstring形式
                if isinstance(dep, dict):
                    dep_id = dep.get('id')
                elif isinstance(dep, str):
                    dep_id = dep
                else:
                    continue

                if dep_id:
                    assert dep_id in task_ids, f"Task {task_id} depends on non-existent task: {dep_id}"

    def test_no_circular_dependencies(self, data_loader):
        """循環依存関係の検証"""
        dependency_documents = data_loader.load_yaml_all("tasks/dependency_chain.yaml")
        valid_tasks = [doc for doc in dependency_documents if doc and isinstance(doc, dict)]

        # タスクIDと依存関係の対応を作成
        dependencies = {}
        for task in valid_tasks:
            task_id = task.get('id')
            if task_id:
                task_deps = task.get('dependencies', [])
                # 依存関係を正規化（辞書形式からIDのリストに変換）
                dep_ids = []
                for dep in task_deps:
                    if isinstance(dep, dict):
                        dep_id = dep.get('id')
                        if dep_id:
                            dep_ids.append(dep_id)
                    elif isinstance(dep, str):
                        dep_ids.append(dep)
                dependencies[task_id] = dep_ids

        def has_circular_dependency(task_id, visited=None, path=None):
            """循環依存をチェックする再帰関数"""
            if visited is None:
                visited = set()
            if path is None:
                path = []

            if task_id in path:
                return True  # 循環依存検出

            if task_id in visited:
                return False  # すでにチェック済み

            visited.add(task_id)
            path.append(task_id)

            for dep_id in dependencies.get(task_id, []):
                if has_circular_dependency(dep_id, visited, path.copy()):
                    return True

            return False

        # すべてのタスクについて循環依存をチェック
        for task_id in dependencies.keys():
            assert not has_circular_dependency(task_id), f"Circular dependency detected involving task: {task_id}"

    def test_error_case_intentional_failures(self, data_loader):
        """エラーケースの意図的な失敗検証"""
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            pytest.skip("jsonschema not available")

        error_documents = data_loader.load_yaml_all("tasks/error_cases.yaml")
        schema = data_loader.load_schema("task_schema")

        # エラーケースとして期待される検証失敗
        invalid_count = 0
        for doc in error_documents:
            if not doc or not isinstance(doc, dict):
                continue

            try:
                validate(instance=doc, schema=schema)
                # 検証が通った場合（エラーケースでない可能性）
                doc_id = doc.get('id', 'unknown')
                if doc_id not in ['invalid-yaml-syntax']:  # 一部の有効なケースは除外
                    print(f"Warning: Error case document {doc_id} passed validation unexpectedly")
            except ValidationError:
                invalid_count += 1

        # 少なくとも一部のエラーケースが検証に失敗することを確認
        assert invalid_count > 0, "No error cases failed validation as expected"


class TestDataIntegrity:
    """データ整合性テスト"""

    @pytest.fixture
    def data_loader(self):
        """データローダーフィクスチャ"""
        data_path = Path(__file__).parent.parent / "data"
        return DataLoader(data_path)

    def test_all_schemas_are_valid_json_schema(self, data_loader):
        """すべてのスキーマが有効なJSONスキーマであることを検証"""
        try:
            from jsonschema import Draft7Validator, SchemaError
        except ImportError:
            pytest.skip("jsonschema not available")

        schema_dir = Path(__file__).parent.parent / "data" / "schemas"
        schema_files = list(schema_dir.glob("*.yaml"))

        assert len(schema_files) > 0, "No schema files found"

        for schema_file in schema_files:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = yaml.safe_load(f)

            try:
                Draft7Validator.check_schema(schema)
            except SchemaError as e:
                pytest.fail(f"Schema {schema_file.name} is invalid: {e}")

    def test_required_test_data_files_exist(self, data_loader):
        """必要なテストデータファイルの存在確認"""
        required_files = [
            "tasks/simple_task.yaml",
            "tasks/complex_task.yaml",
            "tasks/dependency_chain.yaml",
            "tasks/error_cases.yaml",
            "projects/single_project.yaml",
            "projects/multi_project.yaml",
            "workflows/automation_basic.yaml",
            "schemas/task_schema.yaml",
            "schemas/project_schema.yaml",
            "schemas/workflow_schema.yaml"
        ]

        data_path = Path(__file__).parent.parent / "data"

        missing_files = []
        for file_path in required_files:
            if not (data_path / file_path).exists():
                missing_files.append(file_path)

        assert not missing_files, f"Missing required test data files: {missing_files}"

    def test_task_instructions_integration(self, data_loader):
        """TaskInstruction統合テスト"""
        # この部分は実際のTaskInstructionクラスが利用可能な場合のみ実行
        try:
            from src.orchestration.types import TaskInstruction
        except ImportError:
            pytest.skip("TaskInstruction not available")

        # シンプルタスクでのTaskInstruction作成テスト
        task_data = data_loader.load_yaml("tasks/simple_task.yaml")

        try:
            task_instruction = TaskInstruction(
                name=task_data["title"],
                description=task_data.get("description", ""),
                dependencies=task_data.get("dependencies", []),
                inputs=task_data.get("inputs", []),
                outputs=task_data.get("outputs", []),
                note=task_data.get("note")
            )
            assert task_instruction.name == task_data["title"]
        except Exception as e:
            pytest.fail(f"Failed to create TaskInstruction from simple task: {e}")
