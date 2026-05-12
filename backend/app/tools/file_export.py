"""工作流产物导出工具，负责将当前工作流产物打包为压缩文件"""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


class FileExportError(Exception):
    """产物导出异常，供服务层转换为统一业务错误"""


class EmptyArtifactExportError(FileExportError):
    """没有可导出产物时抛出的异常"""


class InvalidArtifactExportPathError(FileExportError):
    """待导出文件越界时抛出的异常"""


class FileExportTool:
    """工作流产物导出工具，负责打包当前工作流的真实产物文件"""

    def build_archive_name(self, workflow_id: int) -> str:
        """根据工作流编号生成默认压缩包名称"""

        return f"workflow_{workflow_id}_artifacts.zip"

    def export_artifacts(
        self,
        *,
        artifacts_dir: Path,
        artifact_paths: list[Path],
        archive_name: str,
    ) -> Path:
        """将指定产物列表打包为 zip，并返回压缩包路径"""

        if not artifact_paths:
            raise EmptyArtifactExportError("当前工作流还没有可导出的产物")

        resolved_artifacts_dir = artifacts_dir.resolve()
        exports_dir = (resolved_artifacts_dir.parent / "exports").resolve()
        exports_dir.mkdir(parents=True, exist_ok=True)

        archive_path = (exports_dir / archive_name.strip()).resolve()
        if not archive_path.is_relative_to(exports_dir):
            raise InvalidArtifactExportPathError(
                "导出压缩包路径超出当前工作流 exports 目录"
            )

        with ZipFile(archive_path, mode="w", compression=ZIP_DEFLATED) as archive:
            for artifact_path in artifact_paths:
                resolved_artifact_path = artifact_path.resolve()
                if not resolved_artifact_path.is_relative_to(resolved_artifacts_dir):
                    raise InvalidArtifactExportPathError(
                        "待导出文件超出当前工作流 artifacts 目录"
                    )

                archive.write(
                    resolved_artifact_path,
                    arcname=resolved_artifact_path.relative_to(
                        resolved_artifacts_dir
                    ).as_posix(),
                )

        return archive_path
