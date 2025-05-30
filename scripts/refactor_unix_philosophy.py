#!/usr/bin/env python3
"""Unix Philosophy-based Refactoring Script.

Implements refactoring based on Unix philosophy analysis:
1. Break down large functions (>50 lines)
2. Extract service objects from large classes
3. Apply single responsibility principle
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import json


class FunctionExtractor:
    """Extract functions that violate Unix philosophy principles."""

    def __init__(self):
        self.violations: List[Dict[str, Any]] = []

    def analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze a file for Unix philosophy violations."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            self.violations = []
            self._extract_violations(tree, file_path)
            return self.violations

        except Exception as e:
            return [{"error": str(e)}]

    def _extract_violations(self, node: ast.AST, file_path: Path, parent_class: str = None):
        """Recursively extract violations."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef):
                self._check_function(child, file_path, parent_class)
            elif isinstance(child, ast.ClassDef):
                self._extract_violations(child, file_path, child.name)
            else:
                self._extract_violations(child, file_path, parent_class)

    def _check_function(self, node: ast.FunctionDef, file_path: Path, parent_class: str = None):
        """Check if function violates Unix philosophy."""
        func_lines = (node.end_lineno or node.lineno) - node.lineno

        if func_lines > 50:
            violation = {
                "file": str(file_path),
                "function": node.name,
                "class": parent_class,
                "lines": func_lines,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "args_count": len(node.args.args),
                "type": "large_function"
            }

            # Add refactoring suggestions
            if func_lines > 100:
                violation["priority"] = "high"
                violation["suggestion"] = "Extract into service class with multiple methods"
            elif func_lines > 75:
                violation["priority"] = "medium"
                violation["suggestion"] = "Split into 2-3 smaller functions"
            else:
                violation["priority"] = "low"
                violation["suggestion"] = "Extract helper functions"

            self.violations.append(violation)


def create_refactoring_plan(analysis_file: str = "unix_philosophy_analysis.json") -> Dict[str, Any]:
    """Create a refactoring plan from analysis results."""
    try:
        with open(analysis_file, 'r') as f:
            analysis = json.load(f)
    except FileNotFoundError:
        print(f"Analysis file {analysis_file} not found. Run analyze_unix_philosophy.py first.")
        return {}

    extractor = FunctionExtractor()
    plan = {
        "high_priority": [],
        "medium_priority": [],
        "low_priority": [],
        "file_splits": []
    }

    for file_result in analysis:
        if "error" in file_result:
            continue

        file_path = Path(file_result["file"])
        violations = extractor.analyze_file(file_path)

        for violation in violations:
            priority = violation.get("priority", "low")
            plan[f"{priority}_priority"].append(violation)

        # Check for large files that should be split
        if file_result.get("line_count", 0) > 300:
            plan["file_splits"].append({
                "file": file_result["file"],
                "lines": file_result["line_count"],
                "classes": len(file_result.get("classes", [])),
                "functions": len(file_result.get("functions", []))
            })

    return plan


def generate_refactoring_suggestions(plan: Dict[str, Any]) -> List[str]:
    """Generate specific refactoring suggestions."""
    suggestions = []

    # High priority function refactoring
    if plan["high_priority"]:
        suggestions.append("## High Priority Function Refactoring")
        for violation in plan["high_priority"]:
            suggestions.append(f"""
### {violation['function']} in {Path(violation['file']).name}
- **Lines**: {violation['lines']} (starts at line {violation['start_line']})
- **Class**: {violation.get('class', 'module level')}
- **Suggestion**: {violation['suggestion']}

**Refactoring approach**:
1. Extract logical sections into private methods
2. Use service objects for complex operations
3. Consider command pattern for multi-step processes
""")

    # File splitting suggestions
    if plan["file_splits"]:
        suggestions.append("\n## File Splitting Recommendations")
        for file_info in plan["file_splits"]:
            suggestions.append(f"""
### {Path(file_info['file']).name}
- **Lines**: {file_info['lines']}
- **Classes**: {file_info['classes']}
- **Functions**: {file_info['functions']}

**Split strategy**:
1. Extract related classes into separate modules
2. Move utility functions to dedicated utils module
3. Create service layer for complex operations
""")

    return suggestions


def main():
    """Main refactoring analysis."""
    print("🔧 Unix Philosophy Refactoring Analysis")
    print("=" * 50)

    # Create refactoring plan
    plan = create_refactoring_plan()
    if not plan:
        sys.exit(1)

    # Generate suggestions
    suggestions = generate_refactoring_suggestions(plan)

    # Save refactoring plan
    with open("refactoring_plan.json", "w") as f:
        json.dump(plan, f, indent=2)

    # Save suggestions
    with open("REFACTORING_SUGGESTIONS.md", "w") as f:
        f.write("# Unix Philosophy Refactoring Suggestions\n\n")
        f.write("\n".join(suggestions))

    print(f"📊 Refactoring Analysis Summary:")
    print(f"  High priority functions: {len(plan['high_priority'])}")
    print(f"  Medium priority functions: {len(plan['medium_priority'])}")
    print(f"  Low priority functions: {len(plan['low_priority'])}")
    print(f"  Files requiring splits: {len(plan['file_splits'])}")

    print(f"\n💾 Detailed plan saved to:")
    print(f"  - refactoring_plan.json")
    print(f"  - REFACTORING_SUGGESTIONS.md")

    # Show top priority items
    if plan["high_priority"]:
        print(f"\n🚨 Top priority refactoring:")
        for violation in plan["high_priority"][:3]:
            print(f"  - {violation['function']}() in {Path(violation['file']).name} ({violation['lines']} lines)")


if __name__ == "__main__":
    main()
