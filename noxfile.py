# noxfile.py
# nox: A generic cross-platform virtualenv management and test automation tool
# AI用テスト実装指示書に基づいたテストスイート統合セッション定義

import nox


# デフォルトのPythonバージョン
nox.options.sessions = [
    "lint",
    "type_check",
    "security",
    "tests",
    "coverage",
]


@nox.session(python="3.11")
def lint(session):
    """Run linting with ruff."""
    session.install("ruff")
    session.run("ruff", "check", "src/warifuri", "--fix")
    session.run("ruff", "format", "src/warifuri")


@nox.session(python="3.11")
def type_check(session):
    """Run type checking with mypy (strict mode)."""
    session.install("mypy", "types-PyYAML", "types-requests", "click", "types-jsonschema")
    session.install("-e", ".")
    session.run("mypy", "--config-file=pyproject.toml", "src/warifuri")


@nox.session(python="3.11")
def security(session):
    """Run security checks with bandit and safety."""
    session.install("bandit[toml]", "safety")
    # bandit セキュリティスキャン
    session.run("bandit", "--config", "pyproject.toml", "-r", "src", "-f", "json", "-o", "bandit-report.json")
    # safety 脆弱性チェック (updated to new API)
    session.run("safety", "scan", "--json", "--output", "safety-report.json")


@nox.session(python="3.11")
def tests(session):
    """Run all tests with pytest."""
    session.install("pytest", "pytest-asyncio", "pytest-cov", "pytest-mock", "hypothesis")
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests/",
        "--asyncio-mode=strict",
        "-v",
        *session.posargs
    )


@nox.session(python="3.11")
def coverage(session):
    """Run tests with coverage reporting."""
    session.install("pytest", "pytest-asyncio", "pytest-cov", "pytest-mock", "hypothesis")
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests/",
        "--asyncio-mode=strict",
        "--cov=src/warifuri",
        "--cov-report=html:htmlcov",
        "--cov-report=xml",
        "--cov-report=term-missing",
        "--cov-fail-under=90",  # Updated to 90% threshold to match CI
        *session.posargs
    )


@nox.session(python="3.11")
def mutation(session):
    """Run mutation testing with mutmut (experimental)."""
    session.install("mutmut")
    session.install("-e", ".")
    session.run("mutmut", "run", "--paths-to-mutate=src/warifuri")


@nox.session(python="3.11")
def integration(session):
    """Run only integration tests."""
    session.install("pytest", "pytest-asyncio", "pytest-cov", "pytest-mock")
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests/integration/",
        "--asyncio-mode=strict",
        "-v",
        *session.posargs
    )


@nox.session(python="3.11")
def property_tests(session):
    """Run property-based tests with hypothesis."""
    session.install("pytest", "pytest-asyncio", "hypothesis")
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests/unit/test_property_based.py",
        "--asyncio-mode=strict",
        "-v",
        *session.posargs
    )


@nox.session(python="3.11")
def unit(session):
    """Run only unit tests."""
    session.install("pytest", "pytest-asyncio", "pytest-cov", "pytest-mock")
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests/unit/",
        "--asyncio-mode=strict",
        "-v",
        *session.posargs
    )


@nox.session(python="3.11")
def e2e(session):
    """Run only end-to-end tests."""
    session.install("pytest", "pytest-asyncio", "pytest-cov", "pytest-mock")
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests/e2e/",
        "--asyncio-mode=strict",
        "-v",
        *session.posargs
    )


@nox.session(python="3.11")
def format_check(session):
    """Check code formatting without making changes."""
    session.install("ruff")
    session.run("ruff", "format", "--check", "src/warifuri")


@nox.session(python="3.11")
def all_quality_checks(session):
    """Run all quality checks: lint, type_check, security, tests, coverage."""
    session.notify("lint")
    session.notify("type_check")
    session.notify("security")
    session.notify("tests")
    session.notify("coverage")


# CI用の軽量セッション（GitHub Actionsなどで利用）
@nox.session(python="3.11")
def ci_fast(session):
    """Fast CI session: lint, type_check, security, tests (no coverage)."""
    session.notify("lint")
    session.notify("type_check")
    session.notify("security")
    session.notify("tests")
