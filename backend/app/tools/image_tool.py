"""图像工具，负责生成图片产物或委托浏览器工具完成截图"""

from __future__ import annotations

import asyncio
import base64
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import httpx

from app.config import settings
from app.tools.base_tool import BaseTool, ToolExecutionResult
from app.tools.browser_tool import BrowserTool, BrowserToolError

ALLOWED_IMAGE_EXTENSIONS = {
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
}


class ImageToolError(Exception):
    """图像工具异常，供上层统一捕获与处理"""


class ImageTool(BaseTool):
    """图像工具，支持通过 OpenAI 图像接口或本地占位渲染生成图片"""

    def __init__(self) -> None:
        """初始化图像工具名称，并保留浏览器截图能力"""

        super().__init__(tool_name="image_tool")
        self.browser_tool = BrowserTool()

    async def execute(
        self,
        *,
        workspace_path: str,
        instruction: str,
    ) -> ToolExecutionResult:
        """解析图像指令，并生成真实图片文件与元数据"""

        try:
            try:
                payload = json.loads(instruction)
            except json.JSONDecodeError as exc:
                raise ImageToolError("图像工具指令必须是合法 JSON") from exc

            action = str(payload.get("action", "generate")).strip().lower()
            if action == "screenshot":
                return await self.execute_screenshot_tool(
                    workspace_path=workspace_path,
                    payload=payload,
                )
            if action != "generate":
                raise ImageToolError(f"不支持的图像工具动作：{action}")

            prompt = str(payload.get("prompt", "")).strip()
            if not prompt:
                raise ImageToolError("图像生成指令缺少 prompt 参数")

            size = str(payload.get("size", settings.image_size)).strip()
            quality = str(payload.get("quality", settings.image_quality)).strip()
            output_name = str(payload.get("output_name", "design_mockup.png")).strip()
            metadata_name = str(
                payload.get("metadata_name", "design_image_result.json")
            ).strip()

            workspace_dir = Path(workspace_path).resolve()
            artifacts_dir = workspace_dir / "artifacts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            image_path = self.resolve_artifact_path(artifacts_dir, output_name)
            metadata_path = self.resolve_artifact_path(artifacts_dir, metadata_name)
            output_format = self.resolve_output_format(image_path)

            if settings.openai_api_key:
                metadata = await self.generate_with_openai(
                    prompt=prompt,
                    image_path=image_path,
                    metadata_path=metadata_path,
                    size=size,
                    quality=quality,
                    output_format=output_format,
                )
            else:
                metadata = await asyncio.to_thread(
                    self.generate_placeholder_image,
                    prompt,
                    image_path,
                    metadata_path,
                    size,
                    quality,
                    output_format,
                )

            return ToolExecutionResult(
                summary=(
                    f"已生成图片：{image_path.name}；"
                    f"来源：{metadata['provider']}；"
                    f"尺寸：{metadata['size']}。"
                ),
                artifacts=[str(image_path), str(metadata_path)],
                raw_output=json.dumps(metadata, ensure_ascii=False, indent=2),
                exit_code=0,
            )
        except ImageToolError:
            raise
        except subprocess.TimeoutExpired as exc:
            raise ImageToolError(
                f"图像工具执行超时，已超过 {settings.image_timeout_seconds} 秒"
            ) from exc
        except BrowserToolError as exc:
            raise ImageToolError(f"图像截图失败：{exc}") from exc
        except OSError as exc:
            raise ImageToolError(f"图像工具执行失败：{exc}") from exc
        except Exception as exc:
            raise ImageToolError(f"图像工具处理失败：{exc}") from exc

    async def execute_screenshot_tool(
        self,
        *,
        workspace_path: str,
        payload: dict[str, object],
    ) -> ToolExecutionResult:
        """委托浏览器工具完成截图，用于图像工具的截图模式"""

        browser_instruction = json.dumps(
            {
                "url_candidates": payload.get("url_candidates", []),
                "wait_selector": str(payload.get("wait_selector", "")).strip(),
                "screenshot_name": str(
                    payload.get("output_name", "browser_image_snapshot.png")
                ).strip(),
                "metadata_name": str(
                    payload.get("metadata_name", "browser_image_result.json")
                ).strip(),
            },
            ensure_ascii=False,
        )
        return await self.browser_tool.execute(
            workspace_path=workspace_path,
            instruction=browser_instruction,
        )

    async def generate_with_openai(
        self,
        *,
        prompt: str,
        image_path: Path,
        metadata_path: Path,
        size: str,
        quality: str,
        output_format: str,
    ) -> dict[str, object]:
        """调用 OpenAI Images API 生成图片，并将结果写入工作区"""

        request_payload = {
            "model": settings.image_model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "output_format": output_format,
        }
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=settings.image_timeout_seconds,
                trust_env=False,
            ) as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers=headers,
                    json=request_payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ImageToolError(f"OpenAI 图像生成失败：{exc}") from exc

        response_payload = response.json()
        image_data = self.extract_image_base64(response_payload)
        image_bytes = base64.b64decode(image_data)
        image_path.write_bytes(image_bytes)

        metadata = {
            "provider": "openai_images_api",
            "model": settings.image_model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "output_format": output_format,
            "image_path": str(image_path),
            "metadata_path": str(metadata_path),
            "used_placeholder": False,
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return metadata

    def generate_placeholder_image(
        self,
        prompt: str,
        image_path: Path,
        metadata_path: Path,
        size: str,
        quality: str,
        output_format: str,
    ) -> dict[str, object]:
        """在未配置 OpenAI Key 时生成本地图像占位图，保证链路可验证"""

        script_payload = {
            "prompt": prompt,
            "image_path": str(image_path),
            "size": size,
            "quality": quality,
            "output_format": output_format,
        }
        completed_process = subprocess.run(
            [sys.executable, "-c", self.build_placeholder_script()],
            input=json.dumps(script_payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=str(image_path.parent.parent),
            timeout=settings.image_timeout_seconds,
            check=False,
        )
        stdout_text = completed_process.stdout.strip()
        stderr_text = completed_process.stderr.strip()

        if completed_process.returncode != 0:
            error_detail = stderr_text or stdout_text or "未记录到具体错误"
            raise ImageToolError(f"本地占位图渲染失败：{error_detail}")

        if not stdout_text:
            raise ImageToolError("本地占位图渲染失败：未收到子进程结果")

        try:
            render_result = json.loads(stdout_text)
        except json.JSONDecodeError as exc:
            raise ImageToolError(
                f"本地占位图渲染失败：子进程输出不可解析：{stdout_text}"
            ) from exc

        if render_result.get("status") != "success":
            raise ImageToolError(
                f"本地占位图渲染失败：{render_result.get('error', '未记录到具体错误')}"
            )

        metadata = {
            "provider": "local_placeholder_renderer",
            "model": settings.image_model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "output_format": output_format,
            "image_path": str(image_path),
            "metadata_path": str(metadata_path),
            "used_placeholder": True,
            "reason": "OPENAI_API_KEY 未配置，当前使用本地占位图保证链路可验证",
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return metadata

    def extract_image_base64(self, response_payload: dict[str, object]) -> str:
        """从 OpenAI 图像接口响应中提取首张图片的 Base64 数据"""

        data = response_payload.get("data")
        if not isinstance(data, list) or not data:
            raise ImageToolError("OpenAI 图像接口未返回可用图片数据")

        first_image = data[0]
        if not isinstance(first_image, dict):
            raise ImageToolError("OpenAI 图像接口返回的图片结构不合法")

        image_base64 = first_image.get("b64_json")
        if not isinstance(image_base64, str) or not image_base64.strip():
            raise ImageToolError("OpenAI 图像接口未返回 b64_json 数据")
        return image_base64

    def resolve_artifact_path(
        self,
        artifacts_dir: Path,
        artifact_name: str,
    ) -> Path:
        """解析图像产出物目标路径，并阻止写出当前 artifacts 目录"""

        normalized_name = artifact_name.strip()
        if not normalized_name:
            raise ImageToolError("图像工具产出物名称不能为空")

        artifact_path = (artifacts_dir / normalized_name).resolve()
        if not artifact_path.is_relative_to(artifacts_dir):
            raise ImageToolError("图像工具产出物路径越界，禁止写入工作区之外")
        return artifact_path

    def resolve_output_format(self, image_path: Path) -> str:
        """根据文件后缀推导图片输出格式，并限制当前支持范围"""

        output_format = ALLOWED_IMAGE_EXTENSIONS.get(image_path.suffix.lower())
        if output_format is None:
            raise ImageToolError("图像工具当前仅支持输出 png / jpg / jpeg 格式文件")
        return output_format

    def build_placeholder_script(self) -> str:
        """构造本地占位图渲染脚本，用 Playwright 真实输出 PNG/JPEG 文件"""

        return dedent("""
            import html
            import json
            import sys

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
                \"\"\"渲染本地占位图，并将执行结果写回父进程\"\"\"

                payload = json.loads(sys.stdin.read())
                prompt = payload['prompt']
                image_path = payload['image_path']
                output_format = payload['output_format']

                safe_prompt = html.escape(prompt[:220]).replace('\\n', '<br/>')
                html_content = f'''
                <html>
                  <head>
                    <meta charset="utf-8" />
                    <style>
                      body {{
                        margin: 0;
                        width: 1024px;
                        height: 1024px;
                        background:
                          radial-gradient(
                            circle at top left,
                            #f6d365 0%,
                            transparent 35%
                          ),
                          radial-gradient(
                            circle at bottom right,
                            #fda085 0%,
                            transparent 38%
                          ),
                          linear-gradient(135deg, #1f2937 0%, #111827 100%);
                        color: #f9fafb;
                        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                      }}
                      .card {{
                        box-sizing: border-box;
                        width: 100%;
                        height: 100%;
                        padding: 72px;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                      }}
                      .eyebrow {{
                        font-size: 24px;
                        letter-spacing: 0.24em;
                        text-transform: uppercase;
                        color: rgba(255, 255, 255, 0.72);
                      }}
                      .title {{
                        margin-top: 28px;
                        max-width: 780px;
                        font-size: 68px;
                        line-height: 1.08;
                        font-weight: 700;
                      }}
                      .prompt {{
                        max-width: 820px;
                        padding: 28px 32px;
                        border-radius: 28px;
                        background: rgba(255, 255, 255, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.16);
                        backdrop-filter: blur(8px);
                        font-size: 26px;
                        line-height: 1.55;
                        color: rgba(255, 255, 255, 0.9);
                      }}
                      .footer {{
                        display: flex;
                        justify-content: space-between;
                        font-size: 22px;
                        color: rgba(255, 255, 255, 0.72);
                      }}
                    </style>
                  </head>
                  <body>
                    <div class="card">
                      <div>
                        <div class="eyebrow">AgentFlow Image Tool</div>
                        <div class="title">设计占位图已生成</div>
                      </div>
                      <div class="prompt">{safe_prompt}</div>
                      <div class="footer">
                        <span>provider: local_placeholder_renderer</span>
                        <span>output: {output_format}</span>
                      </div>
                    </div>
                  </body>
                </html>
                '''

                try:
                    with sync_playwright() as playwright:
                        browser = launch_browser(playwright)
                        try:
                            page = browser.new_page(
                                viewport={'width': 1024, 'height': 1024}
                            )
                            page.set_content(html_content, wait_until='load')
                            screenshot_args = {
                                'path': image_path,
                                'type': output_format,
                            }
                            if output_format == 'jpeg':
                                screenshot_args['quality'] = 92
                            page.screenshot(**screenshot_args)
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
                        {'status': 'success', 'image_path': image_path},
                        ensure_ascii=False,
                    )
                )


            if __name__ == '__main__':
                main()
            """).strip()
