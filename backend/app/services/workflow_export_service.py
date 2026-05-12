"""工作流产物导出服务，负责组织导出范围并调用导出工具"""

from pathlib import Path

from app.models.workflow import Workflow
from app.services.workflow_artifact_service import (
    collect_workflow_artifact_paths,
    resolve_artifacts_dir,
)
from app.tools.file_export import (
    EmptyArtifactExportError,
    FileExportTool,
    InvalidArtifactExportPathError,
)


def export_workflow_artifacts_archive(workflow: Workflow) -> tuple[Path, str]:
    """导出当前工作流全部产物，并返回压缩包路径与文件名"""

    artifacts_dir = resolve_artifacts_dir(workflow)
    artifact_paths = collect_workflow_artifact_paths(workflow)
    export_tool = FileExportTool()
    archive_name = export_tool.build_archive_name(workflow.id)
    archive_path = export_tool.export_artifacts(
        artifacts_dir=artifacts_dir,
        artifact_paths=artifact_paths,
        archive_name=archive_name,
    )
    return archive_path, archive_name


__all__ = [
    "EmptyArtifactExportError",
    "InvalidArtifactExportPathError",
    "export_workflow_artifacts_archive",
]
