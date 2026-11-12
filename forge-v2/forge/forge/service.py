"""Application services: approval, host tests, GitHub export,
Docker sandbox tests, and project diffing."""
import json
import subprocess
import sys
import urllib.request

from forge.config import settings
from forge.diff_utils import build_project_diff
from forge.paths import write_project_files
from forge.rag import build_from_approved
from forge.storage import (
    get_approved_snapshot,
    get_project,
    save_approved_snapshot,
    update_project_status,
)


def approve_project(project_id: str) -> dict:
    project = get_project(project_id)
    if project is None:
        raise ValueError("Project not found.")
    if project["status"] != "awaiting_approval":
        raise ValueError("This project is not awaiting approval.")

    files = project["result"]["code"]["files"]
    written_files = write_project_files(project_id, files)
    # Feature: diff viewer — snapshot the approved file set
    save_approved_snapshot(project_id, files)
    # Feature: RAG — refresh the corpus from all approved projects
    try:
        build_from_approved()
    except Exception:
        pass
    update_project_status(project_id, "approved")
    return {
        "project_id": project_id,
        "status": "approved",
        "written_files": written_files,
    }


def run_project_tests(project_id: str) -> dict:
    """Host-based pytest (dangerous, off by default)."""
    if not settings.allow_host_test_execution:
        raise PermissionError(
            "Host test execution is disabled. "
            "Enable ALLOW_HOST_TEST_EXECUTION only for trusted code "
            "and never for untrusted generated code. "
            "For untrusted code use the Docker sandbox instead."
        )

    project = get_project(project_id)
    if project is None:
        raise ValueError("Project not found.")

    project_dir = settings.workspace_directory / project_id
    if not project_dir.exists():
        raise FileNotFoundError("Project directory does not exist. Approve it first.")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=settings.test_timeout_seconds,
    )
    return {
        "project_id": project_id,
        "mode": "host",
        "returncode": result.returncode,
        "stdout": result.stdout[-5000:],
        "stderr": result.stderr[-5000:],
    }


def run_sandbox_tests(project_id: str) -> dict:
    """Run pytest inside an isolated Docker container with no network
    and strict resource limits. Requires Docker installed and running,
    and ENABLE_DOCKER_SANDBOX=true."""
    if not settings.enable_docker_sandbox:
        raise PermissionError(
            "Docker sandbox is disabled. Set ENABLE_DOCKER_SANDBOX=true "
            "and ensure Docker is installed and running."
        )

    project = get_project(project_id)
    if project is None:
        raise ValueError("Project not found.")

    project_dir = settings.workspace_directory / project_id
    if not project_dir.exists():
        raise FileNotFoundError("Project directory does not exist. Approve it first.")

    # Verify docker is available
    probe = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        capture_output=True, text=True, timeout=15,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"Docker not available: {probe.stderr.strip()}")

    cmd = [
        "docker", "run", "--rm",
        "--network", "none" if settings.docker_network_disabled else "bridge",
        "--memory", settings.docker_memory_limit,
        "--cpus", settings.docker_cpus,
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        "--user", "65534:65534",
        "-v", f"{project_dir.resolve()}:/workspace:ro",
        settings.docker_image,
        "sh", "-c",
        "cp -r /workspace /build && cd /build && "
        "python -m pip install --quiet --no-cache-dir pytest 2>/dev/null; "
        "python -m pytest -q",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=settings.docker_timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {
            "project_id": project_id,
            "mode": "docker-sandbox",
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timed out after {settings.docker_timeout_seconds}s",
        }
    return {
        "project_id": project_id,
        "mode": "docker-sandbox",
        "returncode": result.returncode,
        "stdout": result.stdout[-8000:],
        "stderr": result.stderr[-8000:],
    }


def get_project_diff(project_id: str) -> dict:
    """Diff the current awaiting-approval code against the last approved
    snapshot for the same project (or an empty base if none)."""
    project = get_project(project_id)
    if project is None:
        raise ValueError("Project not found.")
    new_files = project["result"]["code"]["files"]
    old_files = get_approved_snapshot(project_id) or []
    diff = build_project_diff(
        project_id=project_id,
        old_files=old_files,
        new_files=new_files,
        base_label="last_approved_snapshot" if old_files else "empty",
        comparison_label="current_awaiting_approval",
    )
    return diff.model_dump()


def github_export(project_id: str, repo_name: str | None = None,
                  visibility: str | None = None) -> dict:
    """Export an approved project to a local git repo and optionally
    push to GitHub. Requires ENABLE_GITHUB_EXPORT=true and, for remote
    push, GITHUB_TOKEN set."""
    if not settings.enable_github_export:
        raise PermissionError(
            "GitHub export is disabled. Set ENABLE_GITHUB_EXPORT=true."
        )
    project = get_project(project_id)
    if project is None:
        raise ValueError("Project not found.")
    if project["status"] != "approved":
        raise ValueError("Only approved projects can be exported. Approve it first.")

    project_dir = settings.workspace_directory / project_id
    if not project_dir.exists():
        raise FileNotFoundError("Project directory does not exist. Approve it first.")

    repo_name = repo_name or project.get("project_name", project_id).lower().replace(" ", "-")
    visibility = visibility or settings.github_default_visibility

    # Initialize local git repo
    git = ["git"]
    subprocess.run(git + ["init"], cwd=project_dir, capture_output=True, check=False)
    subprocess.run(git + ["add", "."], cwd=project_dir, capture_output=True, check=False)
    subprocess.run(
        git + ["-c", "user.email=forge@local", "-c", "user.name=Forge", "commit", "-m",
               f"Initial commit by Forge for {repo_name}"],
        cwd=project_dir, capture_output=True, check=False,
    )
    sha_proc = subprocess.run(
        git + ["rev-parse", "HEAD"], cwd=project_dir, capture_output=True, text=True
    )
    commit_sha = sha_proc.stdout.strip()

    remote_url = ""
    pushed = False
    if settings.github_token:
        remote_url = _create_github_repo(repo_name, visibility)
        if remote_url:
            # Use token in URL so push is non-interactive
            authed = remote_url.replace(
                "https://",
                f"https://x-access-token:{settings.github_token}@",
            )
            subprocess.run(git + ["remote", "remove", "origin"], cwd=project_dir,
                           capture_output=True, check=False)
            subprocess.run(git + ["remote", "add", "origin", authed], cwd=project_dir,
                           capture_output=True, check=False)
            push = subprocess.run(
                git + ["push", "-u", "origin", "HEAD"],
                cwd=project_dir, capture_output=True, text=True,
            )
            pushed = push.returncode == 0
            if not pushed:
                remote_url = f"{remote_url} (push failed: {push.stderr.strip()})"

    return {
        "project_id": project_id,
        "local_repo": str(project_dir),
        "remote_url": remote_url,
        "pushed": pushed,
        "commit_sha": commit_sha,
    }


def _create_github_repo(name: str, visibility: str) -> str:
    """Create a GitHub repo via the REST API. Returns the clone URL."""
    token = settings.github_token
    private = visibility.lower() != "public"
    payload = json.dumps({"name": name, "private": private}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/user/repos",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("clone_url") or data.get("html_url", "")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"GitHub repo creation failed ({exc.code}): {body}") from exc
