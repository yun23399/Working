"""代码执行工具，负责在共享工作区内运行受限命令并记录产出物"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from pathlib import Path

from app.config import settings
from app.tools.base_tool import BaseTool, ToolExecutionResult

ALLOWED_COMMAND_PATTERNS = [
    re.compile(r"^python\s+-c\s+.+", re.IGNORECASE),
    re.compile(r"^python\s+.+\.py(\s+.*)?$", re.IGNORECASE),
    re.compile(r"^node\s+-e\s+.+", re.IGNORECASE),
    re.compile(r"^node\s+.+\.js(\s+.*)?$", re.IGNORECASE),
]


class CodeExecutionError(Exception):
    """代码执行工具异常，供上层统一记录和处理"""


class CodeExecutorTool(BaseTool):
    """代码执行工具，在工作区内执行受限 Python / Node 命令"""

    def __init__(self) -> None:
        """初始化代码执行工具"""

        super().__init__(tool_name="code_executor")

    async def execute(
        self,
        *,
        workspace_path: str,
        instruction: str,
    ) -> ToolExecutionResult:
        """执行受限命令，并将运行日志写入工作区产出物目录"""
        try:
            command = instruction.strip()
            if not command:
                raise CodeExecutionError("代码执行命令不能为空")

            if not self.is_command_allowed(command):
                raise CodeExecutionError(
                    "当前仅允许执行 python/node 的受限命令，请提供明确脚本入口"
                )

            workspace_dir = Path(workspace_path).resolve()
            artifacts_dir = workspace_dir / "artifacts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            before_snapshot = self.build_artifact_snapshot(artifacts_dir)

            try:
                completed_process = await asyncio.to_thread(
                    self.run_command,
                    command,
                    workspace_dir,
                )
            except subprocess.TimeoutExpired as exc:
                raise CodeExecutionError(
                    f"代码执行超时，已超过 {settings.code_exec_timeout} 秒"
                ) from exc
            except OSError as exc:
                raise CodeExecutionError(f"代码执行失败：{exc}") from exc
            except Exception as exc:
                raise CodeExecutionError(f"代码执行失败：{exc}") from exc

            stdout_text = completed_process.stdout.strip()
            stderr_text = completed_process.stderr.strip()
            raw_output = (
                f"STDOUT:\n{stdout_text or '(empty)'}\n\n"
                f"STDERR:\n{stderr_text or '(empty)'}"
            )
            exit_code = completed_process.returncode

            artifact_name = "code_execution_result.json"
            artifact_path = artifacts_dir / artifact_name
            artifact_path.write_text(
                json.dumps(
                    {
                        "command": command,
                        "exit_code": exit_code,
                        "stdout": stdout_text,
                        "stderr": stderr_text,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            summary = (
                f"已执行命令：{command}；退出码：{exit_code}；"
                f"标准输出 {len(stdout_text)} 字符，标准错误 {len(stderr_text)} 字符。"
            )
            if exit_code != 0:
                summary = f"命令执行失败：{command}；退出码：{exit_code}。"

            artifacts = self.collect_changed_artifacts(
                artifacts_dir=artifacts_dir,
                before_snapshot=before_snapshot,
                result_artifact_path=artifact_path,
            )
            return ToolExecutionResult(
                summary=summary,
                artifacts=artifacts,
                raw_output=raw_output,
                exit_code=exit_code,
            )
        except CodeExecutionError:
            raise
        except Exception as exc:
            raise CodeExecutionError(f"代码执行工具处理失败：{exc}") from exc

    def run_command(
        self,
        command: str,
        workspace_dir: Path,
    ) -> subprocess.CompletedProcess[str]:
        """在线程中执行受限命令，兼容 Windows 下的运行时事件循环限制"""

        return subprocess.run(
            command,
            cwd=str(workspace_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            shell=True,
            timeout=settings.code_exec_timeout,
            check=False,
        )

    def is_command_allowed(self, command: str) -> bool:
        """校验命令是否符合最小受限执行白名单"""

        normalized_command = " ".join(command.split())
        return any(
            pattern.match(normalized_command) for pattern in ALLOWED_COMMAND_PATTERNS
        )

    def build_artifact_snapshot(
        self,
        artifacts_dir: Path,
    ) -> dict[str, tuple[int, int]]:
        """记录执行前产出物目录的文件快照，用于识别本次新增或更新文件"""

        snapshot: dict[str, tuple[int, int]] = {}
        for artifact_path in artifacts_dir.rglob("*"):
            if artifact_path.is_file():
                stat = artifact_path.stat()
                snapshot[str(artifact_path.resolve())] = (
                    stat.st_mtime_ns,
                    stat.st_size,
                )
        return snapshot

    def collect_changed_artifacts(
        self,
        *,
        artifacts_dir: Path,
        before_snapshot: dict[str, tuple[int, int]],
        result_artifact_path: Path,
    ) -> list[str]:
        """收集本次执行新增或变更的产出物，并强制包含执行结果文件"""

        changed_artifacts: set[str] = {str(result_artifact_path.resolve())}
        for artifact_path in artifacts_dir.rglob("*"):
            if not artifact_path.is_file():
                continue

            resolved_path = str(artifact_path.resolve())
            stat = artifact_path.stat()
            current_signature = (stat.st_mtime_ns, stat.st_size)
            if before_snapshot.get(resolved_path) != current_signature:
                changed_artifacts.add(resolved_path)

        return sorted(changed_artifacts)
