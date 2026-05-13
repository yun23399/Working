"""系统通知模块，负责在关键工作流状态下发送本地提醒"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Literal

from loguru import logger

from app.config import settings

NotificationLevel = Literal["info", "success", "warning", "error"]


@dataclass(frozen=True)
class NotificationPayload:
    """本地通知消息体，描述标题、内容和严重级别"""

    title: str
    message: str
    level: NotificationLevel


class SystemNotifier:
    """系统通知器，优先尝试桌面提醒，并回退到日志与声音提示"""

    def __init__(self) -> None:
        """初始化通知器，并准备通知日志目录"""

        self.enabled = settings.notifications_enabled
        self.sound_enabled = settings.notification_sound_enabled
        self.log_path = settings.log_dir_path / "notifications.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def notify_workflow_status(
        self,
        *,
        conversation_id: int,
        workflow_id: int,
        status: str,
        summary: str,
    ) -> None:
        """针对工作流关键状态生成标准化本地通知"""

        status_map: dict[str, tuple[str, NotificationLevel]] = {
            "completed": ("工作流已完成", "success"),
            "waiting_confirm": ("工作流等待确认", "warning"),
            "aborted": ("工作流已中断", "error"),
            "failed": ("工作流执行失败", "error"),
            "running": ("工作流开始执行", "info"),
        }
        title, level = status_map.get(status, ("工作流状态更新", "info"))
        message = (
            f"对话 {conversation_id} / 工作流 {workflow_id}\n"
            f"状态：{status}\n"
            f"摘要：{summary[:240]}"
        )
        self.notify(NotificationPayload(title=title, message=message, level=level))

    def notify(self, payload: NotificationPayload) -> None:
        """发送本地通知，失败时自动回退到日志记录"""

        self.append_notification_log(payload)
        if not self.enabled:
            return

        desktop_sent = self.try_send_windows_toast(payload)
        if self.sound_enabled:
            self.try_play_sound(payload.level)

        if not desktop_sent:
            logger.info("通知已回退为日志记录：{} | {}", payload.title, payload.message)

    def append_notification_log(self, payload: NotificationPayload) -> None:
        """将通知内容追加到本地通知日志，便于后续审计和排查"""

        rendered_line = (
            f"[{payload.level.upper()}] {payload.title} | " f"{payload.message}\n"
        )
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(rendered_line)

    def try_send_windows_toast(self, payload: NotificationPayload) -> bool:
        """尝试通过 PowerShell 发送 Windows 气泡通知"""

        escaped_title = payload.title.replace("'", "''")
        escaped_message = payload.message.replace("'", "''")
        script = (
            "[void][System.Reflection.Assembly]::LoadWithPartialName("
            "'System.Windows.Forms'"
            "); "
            "$notify = New-Object System.Windows.Forms.NotifyIcon; "
            "$notify.Icon = [System.Drawing.SystemIcons]::Information; "
            "$notify.Visible = $true; "
            f"$notify.BalloonTipTitle = '{escaped_title}'; "
            f"$notify.BalloonTipText = '{escaped_message}'; "
            "$notify.ShowBalloonTip(4000); "
            "Start-Sleep -Seconds 5; "
            "$notify.Dispose();"
        )
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            return True
        except OSError as exc:
            logger.warning("桌面通知发送异常，已回退日志记录：{}", exc)
            return False

    def try_play_sound(self, level: NotificationLevel) -> None:
        """尝试播放系统声音，失败时仅记录调试日志"""

        try:
            import winsound

            sound_type_map = {
                "info": winsound.MB_ICONASTERISK,
                "success": winsound.MB_ICONEXCLAMATION,
                "warning": winsound.MB_ICONHAND,
                "error": winsound.MB_ICONHAND,
            }
            winsound.MessageBeep(sound_type_map.get(level, winsound.MB_ICONASTERISK))
        except (ImportError, RuntimeError) as exc:
            logger.debug("播放通知声音失败：{}", exc)
