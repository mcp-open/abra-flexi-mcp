from __future__ import annotations

import re
import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
PYTHON_IMAGE = (
    "python:3.13-slim@sha256:"
    "6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91"
)


def _input_requirements(path: Path) -> dict[str, Requirement]:
    result: dict[str, Requirement] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "-r ")):
            continue
        requirement = Requirement(line)
        result[canonicalize_name(requirement.name)] = requirement
    return result


def test_direct_connector_requirements_are_fresh() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    runtime = _input_requirements(ROOT / "release/runtime-requirements.in")
    tests = _input_requirements(ROOT / "release/python-requirements.in")
    declared_runtime = {
        canonicalize_name(Requirement(spec).name): Requirement(spec)
        for spec in project["dependencies"]
        if not spec.startswith("openmcp-sdk")
    }
    declared_tests = {
        canonicalize_name(Requirement(spec).name): Requirement(spec)
        for spec in project["optional-dependencies"]["test"]
    }
    assert {name: str(req) for name, req in declared_runtime.items()} == {
        name: str(runtime[name]) for name in declared_runtime
    }
    assert {name: str(req) for name, req in declared_tests.items()} == {
        name: str(tests[name]) for name in declared_tests
    }


def test_lock_files_are_hash_pinned() -> None:
    pairs = (
        ("release/runtime-requirements.in", "release/runtime-requirements.lock"),
        ("release/python-requirements.in", "release/python-requirements.lock"),
    )
    for input_relative, relative in pairs:
        lock = (ROOT / relative).read_text(encoding="utf-8")
        assert lock.count("--hash=sha256:") >= 50, relative
        pinned = {
            canonicalize_name(match.group(1)): Version(match.group(2))
            for match in re.finditer(r"^([A-Za-z0-9_.-]+)==([^\\\s]+)", lock, re.MULTILINE)
        }
        for name, requirement in _input_requirements(ROOT / input_relative).items():
            assert name in pinned, (relative, name)
            assert pinned[name] in requirement.specifier, (relative, requirement, pinned[name])


def test_dependency_and_container_inputs_are_pinned() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert PYTHON_IMAGE in dockerfile
    assert "--require-hashes" in dockerfile
    assert "--no-deps --no-build-isolation" in dockerfile


def test_ci_release_gate_order_and_scope() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "github.event_name == 'push' && github.ref == 'refs/heads/main'" in ci
    assert "release/python-requirements.lock" in ci
    assert "--require-hashes" in ci
    assert "--no-deps --no-build-isolation" in ci
    assert "trivy image" in ci
    assert "cyclonedx" in ci
    assert "X-OpenMCP-Gateway-Token" in ci
    assert "SOURCE_DIR: abraflexi-source-${{ github.run_id }}" in ci
    assert "Chybí OPENMCP_PII_SALT" in ci
    assert ci.index("name: Scan candidate") < ci.index("name: Push verified image")
    assert ci.index("name: Generate CycloneDX SBOM") < ci.index("name: Push verified image")
    assert ci.index("name: Smoke test image") < ci.index("name: Push verified image")


def test_workflow_actions_are_commit_pinned_and_public_sdk_has_no_token() -> None:
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    assert workflows
    for workflow_path in workflows:
        workflow = workflow_path.read_text(encoding="utf-8")
        for reference in re.findall(
            r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", workflow, flags=re.MULTILINE
        ):
            assert re.search(r"@[0-9a-f]{40}$", reference), (workflow_path, reference)
        assert "repository: mcp-open/openmcp-sdk\n          token:" not in workflow
