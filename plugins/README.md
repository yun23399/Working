# 本地插件目录

该目录用于放置本地插件。阶段五当前实现采用“仓库内插件自动加载”模式：

1. 在 `plugins/` 或 `plugins/examples/` 下新增插件目录
2. 每个插件目录至少包含：
   - `plugin.py`
   - `plugin.json`
3. `plugin.py` 需要导出 `build_plugin()`，并返回 `PluginBase`

## 插件能力边界

- `tools`：当前阶段为声明式展示字段，用于设置页展示插件宣称的工具能力
- `agent_templates`：当前阶段的真实生效能力，启用后会并入工作流规划器的选角链路
- 执行阶段仍复用现有节点模板快照与工具体系，不直接热插拔新的执行引擎

## 最小结构示例

```text
plugins/
└── examples/
    └── research_helper/
        ├── plugin.json
        └── plugin.py
```
