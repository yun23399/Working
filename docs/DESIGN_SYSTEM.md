# DESIGN_SYSTEM

本文档用于约束当前项目的前端视觉系统，保证后续页面扩展时风格一致，且可直接映射到 React + TypeScript + TailwindCSS 代码。

## 1. 设计方向

- 关键词：专业、克制、柔和、工具型、项目驾驶舱
- 当前阶段主视觉：暖白底 + 米灰分层 + 冷蓝强调
- 动效原则：只在状态切换、消息进入、流式反馈时使用轻量动效

## 2. 颜色规范

### 当前亮色主题

| 语义 | 颜色 |
|------|------|
| 页面背景 | `#f8f6f1` |
| 页面渐变浅底 | `#fbfaf6 -> #f4f1ea` |
| 卡片背景 | `#fffdf9` |
| 次级背景 | `#f0ede6` |
| 侧栏背景 | `#f3efe7` |
| 边框 | `#d9d2c5` |
| 主文本 | `#1f1c17` |
| 次文本 | `#5b5348` |
| 弱文本 | `#8b8377` |
| 强调色 | `#5f7cff` |
| 成功态 | `#1d6b49` |
| 警告态 | `#8a620b` |
| 错误态 | `#a24545` |

### 预留暗色主题

当前阶段尚未落地暗色切换，但建议后续使用以下语义映射：

| 语义 | 建议颜色 |
|------|------|
| 页面背景 | `#13161d` |
| 面板背景 | `#1a1f29` |
| 次级背景 | `#222938` |
| 边框 | `#31394b` |
| 主文本 | `#f4f7fb` |
| 次文本 | `#b7c0d1` |
| 强调色 | `#7c93ff` |

## 3. 字体规范

- 中文优先：`'PingFang SC', 'Microsoft YaHei', sans-serif`
- 英文与系统兼容：`'Segoe UI', sans-serif`
- 标题：`600`
- 普通正文：`400`
- 面板标签：`500`
- 日志与技术信息：使用等宽字体区域显示

## 4. 间距与尺寸

- 页面外边距：`24px`
- 面板内边距：`16px / 24px`
- 组件垂直间距：`12px / 16px / 24px`
- 主要圆角：`20px ~ 32px`
- 图标按钮尺寸：`40px`
- 消息输入区按钮尺寸：`48px`

## 5. 阴影与边框

- 主卡片阴影：`0 18px 60px rgba(31, 28, 23, 0.08)`
- 轻面板阴影：`shadow-sm` 或弱阴影
- 默认边框：`1px solid #d9d2c5`
- 强调状态不依赖重阴影，优先通过背景色与文字色区分

## 6. 动效规范

- 页面级进入：轻微上移 + 淡入
- 消息气泡进入：`opacity + y`
- 流式文本：尾部光标呼吸动画
- 状态切换：`150ms ~ 240ms`
- 路由切换：统一通过 `PageTransition` 组件处理，并保留暖白底上的冷蓝顶部光晕
- 若系统开启“减少动态效果”，页面转场应自动降级为更轻的透明度过渡
- 禁止大幅位移和高频动画

## 7. 按钮样式

### 主按钮

- 背景：深色或强调色
- 文字：白色
- 圆角：`20px`
- 用途：登录、注册、发送、确认

### 次按钮

- 背景：浅色面板
- 边框：标准边框色
- 文字：主文本或次文本
- 用途：切换、侧栏操作、工具按钮

## 8. 卡片样式

### 面板卡片

- 圆角：`24px`
- 背景：`#fffdf9`
- 边框：`#d9d2c5`
- 适用：登录说明卡、错误卡、状态卡

### 消息卡片

- Manager 消息：白底 + 标准边框
- 用户消息：暖灰底 + 标准边框
- 日志卡片：浅米底 + 等宽文本

## 9. 组件命名指南

- 页面组件：放在 `frontend/src/pages/`
- 布局组件：放在 `frontend/src/components/layout/`
- 聊天组件：放在 `frontend/src/components/chat/`
- UI 原子组件：放在 `frontend/src/components/ui/`
- 状态容器：放在 `frontend/src/stores/`
- 数据请求：放在 `frontend/src/api/`

命名规则：

- 组件：`PascalCase`
- Hook：`useXxx`
- Store：`xxxStore`
- 类型：`PascalCase`

## 10. 当前组件状态

已落地：

- `PageTransition`
- `TopNav`
- `Sidebar`
- `MainArea`
- `ChatWindow`
- `MessageBubble`
- `StreamingText`

规划中：

- `AgentCard`
- `TaskCard`
- `CodePreviewCard`
- `FileCard`
- `LogItem`
- `RiskApprovalModal`
- `ModelSelector`
- `ToolStatusBadge`
- `TokenCounter`
