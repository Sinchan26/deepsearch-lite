import ast
from pathlib import Path


def test_domain_policy_dependency_boundaries():
    for folder in ["domain", "policy"]:
        for path in Path("backend/app", folder).glob("*.py"):
            tree = ast.parse(path.read_text())
            imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
            imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
            assert not any(name.startswith(("fastapi", "openai", "langgraph")) for name in imports)


def test_no_persistence_artifacts():
    for folder in ["backend", "frontend/src", "contracts"]:
        assert not [p for p in Path(folder).rglob("*") if p.suffix in {".db", ".sqlite", ".sqlite3"}]
