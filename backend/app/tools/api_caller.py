"""外部 API 调用工具，负责在共享工作区内执行受限 HTTP 请求并记录结果"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.tools.base_tool import BaseTool, ToolExecutionResult


class ApiCallerError(Exception):
    """外部 API 工具异常，供上层统一捕获与处理"""


class ApiCallerTool(BaseTool):
    """外部 API 调用工具，仅允许执行受限 HTTP 请求"""

    def __init__(self) -> None:
        """初始化外部 API 工具名称"""

        super().__init__(tool_name="api_caller")

    async def execute(
        self,
        *,
        workspace_path: str,
        instruction: str,
    ) -> ToolExecutionResult:
        """解析 HTTP 请求指令，调用目标接口并将响应写入工作区产物"""

        try:
            payload = json.loads(instruction)
        except json.JSONDecodeError as exc:
            raise ApiCallerError("API 调用指令必须是合法 JSON") from exc

        method = str(payload.get("method", "GET")).strip().upper()
        url = str(payload.get("url", "")).strip()
        headers = payload.get("headers", {})
        params = payload.get("params", {})
        json_body = payload.get("json")

        if not url:
            raise ApiCallerError("API 调用缺少 url 参数")
        if method not in {"GET", "POST"}:
            raise ApiCallerError(f"当前仅支持 GET / POST，请求方法不合法：{method}")

        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"}:
            raise ApiCallerError("当前仅允许调用 http 或 https 协议")

        workspace_dir = Path(workspace_path).resolve()
        artifacts_dir = workspace_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifacts_dir / "api_response.json"

        try:
            async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                )
        except httpx.HTTPError as exc:
            raise ApiCallerError(f"API 调用失败：{exc}") from exc

        response_payload = {
            "method": method,
            "url": str(response.request.url),
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": self.parse_response_body(response),
        }
        artifact_path.write_text(
            json.dumps(response_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return ToolExecutionResult(
            summary=(
                f"已调用接口：{method} {response.request.url}；"
                f"状态码：{response.status_code}。"
            ),
            artifacts=[str(artifact_path)],
            raw_output=json.dumps(response_payload, ensure_ascii=False, indent=2),
            exit_code=0 if response.is_success else response.status_code,
        )

    def parse_response_body(self, response: httpx.Response) -> object:
        """优先解析 JSON 响应，失败时退回文本内容"""

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type.lower():
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
        return response.text
