"""浏览器自动化工具，负责通过独立子进程执行 Playwright 页面校验"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from urllib.parse import urlparse

from app.config import settings
from app.tools.base_tool import BaseTool, ToolExecutionResult


class BrowserToolError(Exception):
    """浏览器工具异常，供上层统一捕获与处理"""


class BrowserTool(BaseTool):
    """浏览器自动化工具，支持访问候选 URL、截图并记录页面结果"""

    def __init__(self) -> None:
        """初始化浏览器工具名称"""

        super().__init__(tool_name="browser_tool")

    async def execute(
        self,
        *,
        workspace_path: str,
        instruction: str,
    ) -> ToolExecutionResult:
        """读取浏览器访问指令，并将截图和页面元数据写入共享工作区"""

        try:
            try:
                payload = json.loads(instruction)
            except json.JSONDecodeError as exc:
                raise BrowserToolError("浏览器工具指令必须是合法 JSON") from exc

            url_candidates = payload.get("url_candidates", [])
            wait_selector = str(payload.get("wait_selector", "")).strip()
            screenshot_name = str(
                payload.get("screenshot_name", "browser_snapshot.png")
            )
            metadata_name = str(payload.get("metadata_name", "browser_result.json"))

            if not isinstance(url_candidates, list) or not url_candidates:
                raise BrowserToolError("浏览器工具缺少可访问的 url_candidates 列表")

            validated_urls = self.validate_urls(url_candidates)
            workspace_dir = Path(workspace_path).resolve()
            artifacts_dir = workspace_dir / "artifacts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = self.resolve_artifact_path(artifacts_dir, screenshot_name)
            metadata_path = self.resolve_artifact_path(artifacts_dir, metadata_name)
            result = await asyncio.to_thread(
                self.run_browser_subprocess,
                validated_urls,
                wait_selector,
                screenshot_path,
                metadata_path,
            )

            return ToolExecutionResult(
                summary=result["summary"],
                artifacts=[str(screenshot_path), str(metadata_path)],
                raw_output=json.dumps(result["payload"], ensure_ascii=False, indent=2),
                exit_code=0,
            )
        except BrowserToolError:
            raise
        except subprocess.TimeoutExpired as exc:
            raise BrowserToolError(
                f"浏览器工具执行超时，已超过 {settings.code_exec_timeout} 秒"
            ) from exc
        except OSError as exc:
            raise BrowserToolError(f"浏览器工具执行失败：{exc}") from exc
        except Exception as exc:
            raise BrowserToolError(f"浏览器工具处理失败：{exc}") from exc

    def run_browser_subprocess(
        self,
        url_candidates: list[str],
        wait_selector: str,
        screenshot_path: Path,
        metadata_path: Path,
    ) -> dict[str, object]:
        """在独立 Python 子进程中运行 Playwright，规避服务进程事件循环限制"""

        script_payload = {
            "url_candidates": url_candidates,
            "wait_selector": wait_selector,
            "screenshot_path": str(screenshot_path),
            "metadata_path": str(metadata_path),
        }
        completed_process = subprocess.run(
            [sys.executable, "-c", self.build_runner_script()],
            input=json.dumps(script_payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=str(screenshot_path.parent.parent),
            timeout=settings.code_exec_timeout,
            check=False,
        )

        stdout_text = completed_process.stdout.strip()
        stderr_text = completed_process.stderr.strip()

        if completed_process.returncode != 0:
            error_detail = stderr_text or stdout_text or "未记录到具体错误"
            raise BrowserToolError(f"浏览器工具执行失败：{error_detail}")

        if not stdout_text:
            raise BrowserToolError("浏览器工具执行失败：未收到子进程结果")

        try:
            result = json.loads(stdout_text)
        except json.JSONDecodeError as exc:
            raise BrowserToolError(
                f"浏览器工具执行失败：子进程输出不可解析：{stdout_text}"
            ) from exc

        if result.get("status") != "success":
            error_message = str(result.get("error", "未记录到具体错误"))
            raise BrowserToolError(f"浏览器访问失败：{error_message}")

        payload = result.get("payload")
        if not isinstance(payload, dict):
            raise BrowserToolError("浏览器工具执行失败：缺少有效结果负载")

        summary = (
            f"已访问页面：{payload.get('final_url', 'unknown')}；"
            f"标题：{payload.get('title') or '无标题'}；"
            f"状态码：{payload.get('status_code', 'unknown')}。"
        )
        return {
            "summary": summary,
            "payload": payload,
        }

    def resolve_artifact_path(
        self,
        artifacts_dir: Path,
        artifact_name: str,
    ) -> Path:
        """解析产出物目标路径，并阻止写出当前 artifacts 目录"""

        normalized_name = artifact_name.strip()
        if not normalized_name:
            raise BrowserToolError("浏览器工具产出物名称不能为空")

        artifact_path = (artifacts_dir / normalized_name).resolve()
        if not artifact_path.is_relative_to(artifacts_dir):
            raise BrowserToolError("浏览器工具产出物路径越界，禁止写入工作区之外")
        return artifact_path

    def build_runner_script(self) -> str:
        """构造子进程执行脚本，负责真正发起 Playwright 浏览器访问"""

        return dedent("""
            import json
            import sys
            from pathlib import Path

            from playwright.sync_api import sync_playwright


            def launch_browser(playwright):
                \"\"\"优先复用本机 Edge，失败时回退到 Playwright Chromium\"\"\"

                try:
                    return playwright.chromium.launch(
                        channel='msedge',
                        headless=True,
                    )
                except Exception:
                    try:
                        return playwright.chromium.launch(headless=True)
                    except Exception as exc:
                        raise RuntimeError(
                            '浏览器启动失败，请先安装 Playwright Chromium '
                            '或确认本机 Edge 可用'
                        ) from exc


            def main():
                \"\"\"执行浏览器访问流程，并将结果写回父进程\"\"\"

                payload = json.loads(sys.stdin.read())
                url_candidates = payload['url_candidates']
                wait_selector = payload['wait_selector']
                screenshot_path = Path(payload['screenshot_path']).resolve()
                metadata_path = Path(payload['metadata_path']).resolve()
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                metadata_path.parent.mkdir(parents=True, exist_ok=True)
                last_error = '未记录到具体错误'

                try:
                    with sync_playwright() as playwright:
                        browser = launch_browser(playwright)
                        try:
                            page = browser.new_page(
                                viewport={'width': 1440, 'height': 900}
                            )
                            for url in url_candidates:
                                try:
                                    response = page.goto(
                                        url,
                                        wait_until='domcontentloaded',
                                        timeout=15000,
                                    )
                                    if wait_selector:
                                        page.wait_for_selector(
                                            wait_selector,
                                            timeout=5000,
                                        )

                                    page.screenshot(
                                        path=str(screenshot_path),
                                        full_page=True,
                                    )
                                    result_payload = {
                                        'requested_url': url,
                                        'final_url': page.url,
                                        'title': page.title(),
                                        'status_code': (
                                            response.status if response else None
                                        ),
                                        'wait_selector': wait_selector or None,
                                    }
                                    metadata_path.write_text(
                                        json.dumps(
                                            result_payload,
                                            ensure_ascii=False,
                                            indent=2,
                                        ),
                                        encoding='utf-8',
                                    )
                                    sys.stdout.write(
                                        json.dumps(
                                            {
                                                'status': 'success',
                                                'payload': result_payload,
                                            },
                                            ensure_ascii=False,
                                        )
                                    )
                                    return
                                except Exception as exc:
                                    last_error = f'{url} -> {exc}'
                                    continue
                        finally:
                            browser.close()
                except Exception as exc:
                    sys.stdout.write(
                        json.dumps(
                            {'status': 'error', 'error': str(exc)},
                            ensure_ascii=False,
                        )
                    )
                    return

                sys.stdout.write(
                    json.dumps(
                        {'status': 'error', 'error': last_error},
                        ensure_ascii=False,
                    )
                )


            if __name__ == '__main__':
                main()
            """).strip()

    def validate_urls(self, urls: list[object]) -> list[str]:
        """校验候选 URL 列表，仅允许访问 http 或 https 地址"""

        validated_urls: list[str] = []
        for item in urls:
            url = str(item).strip()
            if not url:
                continue
            parsed_url = urlparse(url)
            if parsed_url.scheme not in {"http", "https"}:
                raise BrowserToolError(f"浏览器工具仅允许访问 http / https 地址：{url}")
            validated_urls.append(url)

        if not validated_urls:
            raise BrowserToolError("浏览器工具未收到合法 URL")
        return validated_urls
