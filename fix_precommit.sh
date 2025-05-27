#!/bin/bash
# pre-commit修正スクリプト

echo "🔧 Pre-commitエラー自動修正スクリプト開始"

echo "📝 Step 1: ruff自動修正を実行"
ruff check warifuri/ --fix || true

echo "📝 Step 2: 主要なPythonファイルの修正"

# mypyタイプ関連の修正
echo "🔍 Step 2.1: __all__アノテーション追加"
find warifuri/ -name "__init__.py" -exec sed -i 's/^__all__ = /__all__: list[str] = /' {} \;

echo "🔍 Step 2.2: 未使用import削除"
# utils/__init__.pyの未使用importを削除
cat > warifuri/utils/__init__.py << 'EOF'
"""Utilities package."""

__all__: list[str] = [
    "find_workspace_root",
    "create_directory",
    "safe_write_file",
    "setup_logging",
    "load_yaml",
    "ValidationError",
    "validate_instruction_yaml",
    "detect_circular_dependencies",
]

from .filesystem import create_directory, find_workspace_root, safe_write_file
from .logging import setup_logging
from .validation import ValidationError, detect_circular_dependencies, validate_instruction_yaml
from .yaml_utils import load_yaml
EOF

echo "🔍 Step 2.3: validation.pyの修正"
# from節の修正
sed -i 's/raise ValidationError(/raise ValidationError(/g; s/) from None/) from e/g' warifuri/utils/validation.py
sed -i 's/raise click.Abort()/raise click.Abort() from e/g' warifuri/cli/commands/validate.py

echo "🔍 Step 2.4: 未使用変数削除"
sed -i '/project_name = task.project/d' warifuri/utils/validation.py

echo "🔍 Step 2.5: YAMLファイル修正"
# 破損したYAMLファイルの修正
find workspace/ -name "prompt.yaml" -exec sed -i '1s/^/# /' {} \;
find docs/ -name "*.yaml" -exec sed -i '1s/^\\/# /' {} \;

echo "📝 Step 3: 必要な依存関係をpyproject.tomlに追加"
if ! grep -q "types-jsonschema" pyproject.toml; then
    sed -i '/mypy = /a types-jsonschema = "*"' pyproject.toml
fi

echo "✅ 自動修正完了。再度pre-commitを実行してください。"
