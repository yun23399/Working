"""工作流产物服务层，负责受保护的产物列表与文件访问"""

import mimetypes
from datetime import datetime, timezone
from pathlib import Path

from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowArtifactSchema
from app.workflow.workspace import WorkflowWorkspace

IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".svg",
}
DOCUMENT_SUFFIXES = {
    ".md",
    ".txt",
    ".log",
}
CODE_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yml",
    ".yaml",
    ".css",
    ".scss",
    ".html",
    ".htm",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
}


class WorkflowArtifactNotFoundError(Exception):
    """工作流产物不存在异常，用于提示前端当前文件不可访问"""


class InvalidWorkflowArtifactPathError(Exception):
    """工作流产物路径不合法异常，用于阻止越界访问"""


def resolve_artifacts_dir(workflow: Workflow) -> Path:
    """解析当前工作流的产物目录，并确保基础目录结构已创建"""

    workspace_dir = WorkflowWorkspace(workflow).ensure_workspace()
    return (workspace_dir / "artifacts").resolve()


def resolve_preview_type(path: Path, mime_type: str) -> str:
    """根据扩展名和 MIME 类型推断前端预览方式"""

    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"

    if suffix in DOCUMENT_SUFFIXES:
        return "document"

    if suffix in CODE_SUFFIXES:
        return "code"

    if mime_type.startswith("text/"):
        return "document"

    return "binary"


def build_artifact_schema(
    artifacts_dir: Path,
    artifact_path: Path,
) -> WorkflowArtifactSchema:
    """将真实文件路径转换为前端可消费的产物描述结构"""

    stat = artifact_path.stat()
    mime_type = (
        mimetypes.guess_type(artifact_path.name)[0] or "application/octet-stream"
    )
    return WorkflowArtifactSchema(
        name=artifact_path.name,
        relative_path=artifact_path.relative_to(artifacts_dir).as_posix(),
        preview_type=resolve_preview_type(artifact_path, mime_type),
        mime_type=mime_type,
        size_bytes=stat.st_size,
        updated_at=datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        ).isoformat(),
    )


def normalize_artifact_candidate(
    artifacts_dir: Path,
    raw_path: str,
) -> Path | None:
    """将状态中的产物路径规范化为当前 artifacts 目录下的真实文件"""

    normalized = raw_path.strip()
    if not normalized:
        return None

    candidate = Path(normalized)
    candidate_options = []
    if candidate.is_absolute():
        candidate_options.append(candidate.resolve())
    else:
        candidate_options.extend(
            [
                (artifacts_dir / candidate).resolve(),
                (artifacts_dir.parent / candidate).resolve(),
            ]
        )

    for item in candidate_options:
        if item.is_file() and item.is_relative_to(artifacts_dir):
            return item

    return None


def collect_workflow_artifact_paths(workflow: Workflow) -> list[Path]:
    """汇总工作区状态和磁盘中的真实产物文件，并按更新时间倒序返回"""

    workspace = WorkflowWorkspace(workflow)
    artifacts_dir = resolve_artifacts_dir(workflow)
    state = workspace.load_workspace_state()
    collected: dict[str, Path] = {}

    for raw_path in state.get("artifacts", []):
        normalized = normalize_artifact_candidate(artifacts_dir, str(raw_path))
        if normalized is not None:
            collected[str(normalized)] = normalized

    for artifact_path in artifacts_dir.rglob("*"):
        if artifact_path.is_file():
            collected[str(artifact_path.resolve())] = artifact_path.resolve()

    return sorted(
        collected.values(),
        key=lambda item: (-item.stat().st_mtime, item.name.lower()),
    )


def list_workflow_artifacts(workflow: Workflow) -> list[WorkflowArtifactSchema]:
    """返回当前工作流可见的全部产物描述列表"""

    artifacts_dir = resolve_artifacts_dir(workflow)
    return [
        build_artifact_schema(artifacts_dir, artifact_path)
        for artifact_path in collect_workflow_artifact_paths(workflow)
    ]


def resolve_workflow_artifact_path(workflow: Workflow, relative_path: str) -> Path:
    """根据相对路径解析真实产物文件，并校验访问范围不越界"""

    normalized = relative_path.strip().replace("\\", "/")
    if not normalized:
        raise InvalidWorkflowArtifactPathError("产物路径不能为空")

    artifacts_dir = resolve_artifacts_dir(workflow)
    artifact_path = (artifacts_dir / normalized).resolve()
    if not artifact_path.is_relative_to(artifacts_dir):
        raise InvalidWorkflowArtifactPathError("产物路径超出当前工作流 artifacts 目录")

    if not artifact_path.exists() or not artifact_path.is_file():
        raise WorkflowArtifactNotFoundError(normalized)

    return artifact_path
