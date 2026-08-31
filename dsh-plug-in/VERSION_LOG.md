# DSH 插件目录版本日志

## v1.0 (2026-08-21)

- **变更类型**: 新增功能
- **变更摘要**: 新增 dsh-plugin-guard（DSH 插件冲突监控器），支持插件扫描、冲突/启动风险检测、一键启停
- **新增文件**:
  - dsh-plugin-guard/（插件包：package.json、cordis.patch.yml、dsh.plugin.json、bin/、lib/、README.md）
  - guard.bat（Windows 启动器）
- **修改文件**:
  - README.md（补充监控工具使用说明）
- **功能详情**:
  - 扫描 profile 的 bundles + 各插件 cordis.patch.yml + profile 自身 patch，汇总插件清单与启停状态
  - 检测重复挂载、double-mount、已知风险插件（obsidian-memory 缺 vaultPath、AWiki 依赖 IM 等）
  - disable/enable 命令安全编辑 cordis.patch.yml（自动备份 .guard.bak，行级编辑保留用户注释）
  - 已用真实 web profile 验证：35 个插件条目扫描正确、启停往返一致、double-mount 检测准确
- **说明**: 内置宿主 bundle（@deepseek-ai/dsh-base、dsh-web-app）不在 node_modules，扫描时跳过；聚合包挂载多 id 属正常设计

## v1.1 (2026-08-21)

- **变更类型**: 文档补充
- **变更摘要**: 新增 DEPLOY_SOP.md（新环境完整复现 SOP），修正 README 安装命令示例
- **新增文件**:
  - DEPLOY_SOP.md（背景、文件清单、核心实现要点、从零搭建步骤、11 条踩坑记录、验收基准）
- **修改文件**:
  - dsh-plugin-guard/README.md（安装命令去掉尖括号占位符，改为真实路径示例）
- **说明**: 踩坑记录含 PowerShell ExecutionPolicy、cmd 中文乱码、pnpm minimumReleaseAge 拦截、并行启停竞态等；新环境按 SOP 第 4 节顺序执行即可

## v1.2 (2026-08-21)

- **变更类型**: bugfix
- **变更摘要**: 修复 dsh-plugin-guard 作为 DSH 宿主插件启动时报错 `cannot get property 'command' without inject`
- **修改文件**:
  - dsh-plugin-guard/lib/index.js
- **修复详情**:
  - 原代码直接访问 `ctx.command` 且 `inject = []`，违反 Cordis 注入规则导致插件树加载失败
  - 改为通过 `ctx.get('command', null)` 动态获取命令服务，并用 try/catch 包裹，命令系统不可用时静默跳过
  - 启动检测逻辑抽离为 `runCheck` 函数，保持 CLI 工具与宿主插件复用同一套检测
- **验证**: `node --check` 通过，lint 0 问题

## v1.3 (2026-08-31)

- **变更类型**: 适配上游 deepseek-harness 机制优化
- **变更摘要**: 依据上游仓库 [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) 最新机制重构 bundle 解析与 patch 层逻辑
- **修改文件**:
  - dsh-plugin-guard/lib/core.js（主要改造）
  - dsh-plugin-guard/lib/cli.js（scan/status/set 输出增强）
  - dsh-plugin-guard/lib/index.js（宿主插件生效提示动态化）
  - dsh-plugin-guard/README.md（对齐上游机制说明）
- **功能详情**:
  - 双锚点 bundle 解析 `findBundleDir`：先 profile node_modules，再回退 dsh 安装目录解析内置 bundle（`@deepseek-ai/dsh-base`、`@deepseek-ai/dsh-web-app`、`@deepseek-ai/dsh-headless`），不再跳过内置 bundle
  - patch 文件名动态化 `bundlePatchFile`：读取 bundle manifest `dsh.bundle.patch` 字段，不再硬编码 `cordis.patch.yml`
  - `patchReload` 感知：读取 profile manifest `dsh.profile.patchReload`（默认 live 热重载），CLI/宿主插件据此显示"即时生效/需重启"
  - home 级 patch 层：扫描并应用 `$DSH_HOME/cordis.patch.yml`（优先级高于 profile 自身层）
  - `workspace:` 协议支持：bundle 名规范化新增 pnpm workspace 前缀解析
- **验证**: lint 0 问题；`status` 实测显示 `reload: live` 与内置 bundle 解析来源
- **说明**: 修改前已备份 4 个文件（core.js/cli.js/index.js/README.md），同步至 dsh-plug-in 链接目录时再次备份
