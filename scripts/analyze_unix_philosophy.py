#!/usr/bin/env python3
"""Unix Philosophy Compliance Analysis for Warifuri.

Analyzes codebase for adherence to Unix philosophy:
1. Do one thing and do it well
2. Make each program a filter
3. Build a prototype as soon as possible
4. Choose portability over efficiency
5. Store data in flat text files
6. Use software leverage to your advantage
7. Use shell scripts to increase leverage and portability
8. Avoid captive user interfaces
9. Make every program a filter
"""

import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


class UnixPhilosophyAnalyzer(ast.NodeVisitor):
    """Analyze Python code for Unix philosophy compliance."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.issues: List[Dict[str, Any]] = []
        self.classes: List[str] = []
        self.functions: List[str] = []
        self.imports: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)

        # Check for god classes (too many methods)
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > 15:
            self.issues.append(
                {
                    "type": "god_class",
                    "line": node.lineno,
                    "message": f"Class '{node.name}' has {len(methods)} methods. Consider splitting responsibilities.",
                    "severity": "high",
                }
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)

        # Check function complexity (line count approximation)
        func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
        if func_lines > 50:
            self.issues.append(
                {
                    "type": "complex_function",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' has ~{func_lines} lines. Consider breaking down.",
                    "severity": "medium",
                }
            )

        # Check parameter count
        args_count = len(node.args.args)
        if args_count > 7:
            self.issues.append(
                {
                    "type": "too_many_params",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' has {args_count} parameters. Consider using objects or fewer params.",
                    "severity": "medium",
                }
            )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            for alias in node.names:
                self.imports.append(f"{node.module}.{alias.name}")


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = UnixPhilosophyAnalyzer(file_path)
        analyzer.visit(tree)

        return {
            "file": str(file_path),
            "line_count": len(content.split("\n")),
            "classes": analyzer.classes,
            "functions": analyzer.functions,
            "imports": analyzer.imports,
            "issues": analyzer.issues,
        }
    except Exception as e:
        return {
            "file": str(file_path),
            "error": str(e),
            "issues": [{"type": "parse_error", "message": str(e), "severity": "high"}],
        }


def main():
    """Main analysis function."""
    src_path = Path("src/warifuri")
    if not src_path.exists():
        print("Error: src/warifuri directory not found", file=sys.stderr)
        sys.exit(1)

    python_files = list(src_path.rglob("*.py"))
    results = []

    print("🔍 Unix Philosophy Compliance Analysis")
    print("=" * 50)

    for file_path in python_files:
        result = analyze_file(file_path)
        results.append(result)

        if result.get("issues"):
            print(f"\n📁 {file_path.relative_to(src_path)}")
            for issue in result["issues"]:
                severity_icon = {"high": "🚨", "medium": "⚠️", "low": "ℹ️"}.get(
                    issue["severity"], "?"
                )
                print(f"  {severity_icon} Line {issue.get('line', '?')}: {issue['message']}")

    # Summary statistics
    total_files = len(results)
    files_with_issues = len([r for r in results if r.get("issues")])
    total_issues = sum(len(r.get("issues", [])) for r in results)

    print("\n📊 Summary")
    print(f"Files analyzed: {total_files}")
    print(f"Files with issues: {files_with_issues}")
    print(f"Total issues: {total_issues}")

    # Save detailed results
    with open("unix_philosophy_analysis.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n💾 Detailed results saved to unix_philosophy_analysis.json")

    # Unix philosophy specific checks
    print("\n🔧 Unix Philosophy Specific Analysis")
    print("-" * 40)

    # Check for single responsibility
    large_files = [r for r in results if r.get("line_count", 0) > 300]
    if large_files:
        print(f"📈 Large files (>300 lines): {len(large_files)}")
        for r in large_files:
            print(f"  - {Path(r['file']).name}: {r['line_count']} lines")

    # Check for modularity
    files_with_many_classes = [r for r in results if len(r.get("classes", [])) > 3]
    if files_with_many_classes:
        print(f"🏗️ Files with many classes (>3): {len(files_with_many_classes)}")
        for r in files_with_many_classes:
            print(f"  - {Path(r['file']).name}: {len(r['classes'])} classes")


if __name__ == "__main__":
    main()
