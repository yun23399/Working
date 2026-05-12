"""Agent 运行时，负责基于统一 LLM 适配器执行节点任务"""

import json
from pathlib import Path

from app.agents.base_agent import AgentResult, AgentTask, BaseAgent
from app.agents.templates import get_role_template
from app.config import settings
from app.core.llm.adapter import ChatMessage, LLMAdapter
from app.tools import (
    ApiCallerError,
    ApiCallerTool,
    BrowserTool,
    BrowserToolError,
    CodeExecutionError,
    CodeExecutorTool,
    FileTool,
    FileToolError,
)


class GenericTaskAgent(BaseAgent):
    """通用任务 Agent，使用角色和任务描述生成最小执行摘要"""

    def __init__(
        self,
        role: str,
        llm_model: str,
        max_retries: int,
        template_id: str,
    ) -> None:
        """初始化通用 Agent，保留当前节点的角色与重试信息"""

        super().__init__(role=role, llm_model=llm_model, max_retries=max_retries)
        self.adapter = LLMAdapter()
        self.template = get_role_template(template_id)
        self.api_caller = ApiCallerTool()
        self.browser_tool = BrowserTool()
        self.file_tool = FileTool()
        self.code_executor = CodeExecutorTool()

    def build_messages(self, task: AgentTask) -> list[ChatMessage]:
        """构造节点执行所需的最小上下文消息"""

        return [
            ChatMessage(
                role="system",
                content=(
                    "你是多智能体编排平台中的执行 Agent。"
                    f"当前角色是：{task.role}。"
                    f"角色职责：{self.template.summary}。"
                    f"{self.template.system_prompt}"
                    "请根据任务描述输出简洁、明确、可交接的执行结果摘要。"
                    "本阶段只返回文本结果，不调用工具，不输出额外解释。"
                ),
            ),
            ChatMessage(
                role="user",
                content=(
                    f"工作流节点：{task.node_id}\n"
                    f"模板编号：{self.template.template_id}\n"
                    f"任务描述：{task.task}\n"
                    f"上下文：{task.context}\n"
                    f"共享工作区：{task.workspace_path}\n"
                    f"可用工具：{' / '.join(self.template.default_tools)}"
                ),
            ),
        ]

    def build_code_execution_command(self, task: AgentTask) -> str:
        """根据当前节点角色生成最小受限代码执行命令"""

        workspace_dir = Path(task.workspace_path)
        if self.role == "前端工程师":
            target_path = workspace_dir / "artifacts" / "frontend_plan.json"
            return (
                "python -c "
                '"import json, pathlib; '
                f"path = pathlib.Path(r'{target_path}'); "
                "path.parent.mkdir(parents=True, exist_ok=True); "
                "path.write_text(json.dumps({'type':'frontend_plan','status':'generated'},"
                " ensure_ascii=False, indent=2), encoding='utf-8'); "
                "print('frontend artifact generated')\""
            )

        target_path = workspace_dir / "artifacts" / "backend_plan.json"
        return (
            "python -c "
            '"import json, pathlib; '
            f"path = pathlib.Path(r'{target_path}'); "
            "path.parent.mkdir(parents=True, exist_ok=True); "
            "path.write_text(json.dumps({'type':'backend_plan','status':'generated'},"
            " ensure_ascii=False, indent=2), encoding='utf-8'); "
            "print('backend artifact generated')\""
        )

    def build_file_tool_instruction(
        self,
        task: AgentTask,
        content: str,
    ) -> str:
        """根据当前角色构造文件写入指令，沉淀文本型交付物"""

        file_name_map = {
            "PM": "pm_summary.md",
            "前端工程师": "frontend_summary.md",
            "后端工程师": "backend_summary.md",
            "测试工程师": "qa_checklist.md",
            "设计师": "design_brief.md",
        }
        file_name = file_name_map.get(
            self.role,
            f"{self.template.template_id}_summary.md",
        )
        rendered_content = (
            f"# {self.role} 交付摘要\n\n"
            f"- 工作流节点：{task.node_id}\n"
            f"- 模板编号：{self.template.template_id}\n"
            f"- 任务描述：{task.task}\n\n"
            f"## 执行结果\n\n{content}\n"
        )
        return json.dumps(
            {
                "action": "write",
                "path": f"artifacts/{file_name}",
                "content": rendered_content,
            },
            ensure_ascii=False,
        )

    def build_api_caller_instruction(self, task: AgentTask) -> str:
        """根据当前节点构造最小 API 调用指令，用于验证接口联通与响应落盘"""

        base_url = "http://127.0.0.1:8000"
        return json.dumps(
            {
                "method": "GET",
                "url": f"{base_url}/health",
                "headers": {
                    "X-Workflow-Id": str(task.workflow_id),
                    "X-Node-Id": task.node_id,
                },
            },
            ensure_ascii=False,
        )

    def build_browser_tool_instruction(self, task: AgentTask) -> str:
        """根据当前节点构造浏览器访问指令，用于页面可达性验证和截图归档"""

        backend_base_url = f"http://{settings.app_host}:{settings.app_port}"
        screenshot_name_map = {
            "前端工程师": "frontend_snapshot.png",
            "测试工程师": "qa_snapshot.png",
        }
        metadata_name_map = {
            "前端工程师": "frontend_browser_result.json",
            "测试工程师": "qa_browser_result.json",
        }
        return json.dumps(
            {
                "url_candidates": [
                    f"{settings.frontend_app_url.rstrip('/')}/login",
                    f"{backend_base_url}/docs",
                    f"{backend_base_url}/health",
                ],
                "wait_selector": "",
                "screenshot_name": screenshot_name_map.get(
                    self.role,
                    "browser_snapshot.png",
                ),
                "metadata_name": metadata_name_map.get(
                    self.role,
                    "browser_result.json",
                ),
            },
            ensure_ascii=False,
        )

    async def run(self, task: AgentTask) -> AgentResult:
        """执行节点任务并返回完整文本摘要"""

        parts: list[str] = []
        async for token in self.adapter.stream_chat(self.build_messages(task)):
            parts.append(token)

        content = "".join(parts).strip()
        artifacts: list[str] = []
        if "file_tool" in self.template.default_tools:
            try:
                tool_result = await self.file_tool.execute(
                    workspace_path=task.workspace_path,
                    instruction=self.build_file_tool_instruction(task, content),
                )
                artifacts.extend(tool_result.artifacts)
                content = f"{content}\n\n文件产出：{tool_result.summary}"
            except FileToolError as exc:
                content = f"{content}\n\n文件产出失败：{exc}"

        if "api_caller" in self.template.default_tools:
            try:
                tool_result = await self.api_caller.execute(
                    workspace_path=task.workspace_path,
                    instruction=self.build_api_caller_instruction(task),
                )
                artifacts.extend(tool_result.artifacts)
                content = f"{content}\n\n接口调用：{tool_result.summary}"
            except ApiCallerError as exc:
                content = f"{content}\n\n接口调用失败：{exc}"

        if "browser_tool" in self.template.default_tools:
            try:
                tool_result = await self.browser_tool.execute(
                    workspace_path=task.workspace_path,
                    instruction=self.build_browser_tool_instruction(task),
                )
                artifacts.extend(tool_result.artifacts)
                content = f"{content}\n\n页面校验：{tool_result.summary}"
            except BrowserToolError as exc:
                content = f"{content}\n\n页面校验失败：{exc}"

        if "code_executor" in self.template.default_tools:
            try:
                tool_result = await self.code_executor.execute(
                    workspace_path=task.workspace_path,
                    instruction=self.build_code_execution_command(task),
                )
                artifacts.extend(tool_result.artifacts)
                content = f"{content}\n\n工具执行：{tool_result.summary}"
            except CodeExecutionError as exc:
                content = f"{content}\n\n工具执行失败：{exc}"

        return AgentResult(
            summary=content,
            token_count=max(len(parts), 1),
            artifacts=sorted(set(artifacts)),
        )
