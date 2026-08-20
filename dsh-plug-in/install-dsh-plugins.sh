#!/usr/bin/env bash
# ============================================================================
#  DSH 插件一键批量安装脚本 (DeepSeek Harness Plugin Batch Installer)
# ============================================================================
#  基于社区推荐清单整理,分「核心 / 进阶」两档,按推荐顺序批量安装。
#
#  用法:
#    ./install-dsh-plugins.sh                  # 安装核心推荐插件(9个)
#    ./install-dsh-plugins.sh --full           # 核心 + 进阶全部推荐(24个)
#    ./install-dsh-plugins.sh --profile dev    # 指定 profile(默认 web)
#    ./install-dsh-plugins.sh --list           # 只打印清单,不安装
#    ./install-dsh-plugins.sh --yes            # 跳过确认提示
#    ./install-dsh-plugins.sh --skip-check     # 跳过 dsh 环境检查
#    ./install-dsh-plugins.sh --help           # 查看帮助
#
#  安装前须知:
#    1. 需要已安装 DeepSeek Harness(npx @deepseek-ai/dsh 可用即可)
#    2. 启动 Web UI 时务必加 --patch 参数: npx @deepseek-ai/dsh web --patch
#    3. 部分插件为 GitHub 仓库形式,需要本机可访问 GitHub
# ============================================================================

set -u

# ---------- 默认配置 ----------
PROFILE="web"
MODE="core"
DO_CHECK=1
ASSUME_YES=0

# ---------- 输出颜色 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SUCCESS=0
FAILED=0

# ---------- 帮助 ----------
show_help() {
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# ---------- 解析参数 ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="${2:-web}"; shift 2 ;;
    --full) MODE="full"; shift ;;
    --list) MODE="list"; shift ;;
    --yes) ASSUME_YES=1; shift ;;
    --skip-check) DO_CHECK=0; shift ;;
    -h|--help) show_help ;;
    *) echo -e "${RED}未知参数: $1${NC} (用 --help 查看用法)"; exit 1 ;;
  esac
done

# ---------- 插件清单 ----------
# 格式: 名称|描述|安装参数
# [核心档] 发现入口 + 基础能力 + 用量监控
CORE_PLUGINS=(
  "dshmarket|可视化插件市场(设置页搜索/一键安装)|dshmarket"
  "dsh-find-plugin|会话内搜索插件(对话里让Agent找插件)|dsh-find-plugin"
  "dsh-web-ui|界面全家桶(任务看板/Git图谱/Token统计/皮肤中心)|github:zhu1090093659/dsh-web-ui#main"
  "modlens|视觉插件,给纯文本模型装眼睛(OCR/版面/语义JSON)|@liustack/modlens@3.17.2"
  "dsh-at-file|输入框 @ 引用工作区文件|github:omdsh-dev/dsh-at-file#main"
  "dsh-paste-input|支持 Ctrl+V 粘贴/拖拽文件|dsh-paste-input"
  "dsh-office|读写 docx/pdf/pptx/xlsx 文档|dsh-office"
  "dsh-browser-panel|内嵌浏览器,Agent 可操作网页|dsh-browser-panel"
  "dsh-usage|Token 用量/缓存命中率/余额查询|github:feiyang-dev/dsh-usage-plugin"
)

# [进阶档] 体验增强 + 进阶玩法
FULL_PLUGINS=(
  "DSH-better-sidebar|侧边栏工作台(文件树/终端/Git/子代理)|github:omdsh-dev/DSH-better-sidebar#main"
  "dsh-TUI|Claude Code 风格全屏终端|github:ccch1mneyyy/dsh-TUI#main"
  "dsh-vision-toolkit|视觉进阶(图片问答/长截图OCR/UI还原)|github:Anionex/dsh-vision-toolkit"
  "dsh-genui|回复里直接渲染图表/表格/组件|dsh-genui"
  "dsh-turn-rewind|一键回退到上一步|dsh-turn-rewind"
  "dsh-message-edit|编辑已发消息/重新生成|dsh-message-edit"
  "dsh-chat-import|聊天记录无损导入(Cursor/ChatGPT/Gemini等)|dsh-chat-import"
  "dsh_workflow|多Agent工作流(成本追踪/中断恢复/权限)|dsh_workflow"
  "dsh-memory-evolve|跨会话长期记忆|dsh-memory-evolve"
  "dsh-llm-fallbacks|模型故障自动切换备用模型|dsh-llm-fallbacks"
  "dsh-deep-whale|鲸鱼娘皮肤系列|github:Small-tailqwq/dsh-deep-whale"
  "dsh-agent-teams|多Agent团队协作(需本机git读权限)|github:dsh-external/dsh-agent-teams#main"
  "dsh-plan-execute|双模型路由(规划用推理/执行用经济模型)|github:dsh-external/dsh-plan-execute#main"
  "dsh-context-doctor|上下文Token账单分析/裁剪建议|github:Zhenyu98/dsh-context-doctor#main"
  "dsh-browser|操控真实Chrome(保留登录态和Cookie)|dsh-browser"
)

# ---------- 组装安装列表 ----------
INSTALL_LIST=("${CORE_PLUGINS[@]}")
if [[ "$MODE" == "full" ]]; then
  INSTALL_LIST+=("${FULL_PLUGINS[@]}")
fi

# ---------- 打印清单 ----------
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN} DSH 插件一键批量安装脚本${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e " Profile : ${YELLOW}${PROFILE}${NC}"
echo -e " 模式    : ${YELLOW}${MODE}${NC} ($([ "$MODE" = full ] && echo 核心+进阶 || echo 仅核心))"
echo -e " 插件数  : ${YELLOW}${#INSTALL_LIST[@]}${NC}"
echo

if [[ "$MODE" == "list" ]]; then
  echo -e "${CYAN}--- 待安装清单 ---${NC}"
  for entry in "${INSTALL_LIST[@]}"; do
    IFS='|' read -r name desc spec <<< "$entry"
    printf "  %-22s %s\n" "$name" "$desc"
  done
  echo
  exit 0
fi

# ---------- 环境检查 ----------
if [[ "$DO_CHECK" == "1" ]]; then
  echo -e "${CYAN}▶ 检查 dsh 命令...${NC}"
  if ! command -v dsh >/dev/null 2>&1; then
    echo -e "${RED}✘ 未找到 dsh 命令!${NC}"
    echo -e "  请先安装 DeepSeek Harness:"
    echo -e "    ${YELLOW}npm install -g @deepseek-ai/dsh${NC}"
    echo -e "  或临时使用:"
    echo -e "    ${YELLOW}npx @deepseek-ai/dsh --version${NC}"
    echo -e "  如已安装请确认 PATH 配置,或用 --skip-check 跳过检查。"
    exit 1
  fi
  echo -e "${GREEN}✔ dsh 命令已找到: $(command -v dsh)${NC}"
  echo
fi

# ---------- 确认 ----------
if [[ "$ASSUME_YES" != "1" ]]; then
  echo -e "${YELLOW}即将安装以下 ${#INSTALL_LIST[@]} 个插件到 profile [${PROFILE}]:${NC}"
  for entry in "${INSTALL_LIST[@]}"; do
    IFS='|' read -r name desc spec <<< "$entry"
    printf "  %-22s %s\n" "$name" "$desc"
  done
  echo
  read -r -p "确认继续? [y/N] " answer
  if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}已取消。${NC}"
    exit 0
  fi
  echo
fi

# ---------- 逐个安装 ----------
for entry in "${INSTALL_LIST[@]}"; do
  IFS='|' read -r name desc spec <<< "$entry"
  echo -e "${CYAN}▶ [${name}]${NC} ${desc}"
  echo -e "  ${YELLOW}dsh plugin --profile ${PROFILE} add ${spec}${NC}"
  out=$(dsh plugin --profile "$PROFILE" add "$spec" 2>&1)
  rc=$?
  if [[ $rc -eq 0 ]]; then
    echo -e "  ${GREEN}✔ 安装成功${NC}"
    SUCCESS=$((SUCCESS+1))
  else
    echo -e "  ${RED}✘ 安装失败 (exit=$rc)${NC}"
    echo "$out" | tail -n 6 | sed 's/^/    /'
    FAILED=$((FAILED+1))
  fi
  echo
done

# ---------- 汇总 ----------
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN} 安装结果汇总${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "  成功: ${GREEN}${SUCCESS}${NC}   失败: ${RED}${FAILED}${NC}   共 ${#INSTALL_LIST[@]} 个"
echo

# ---------- 后续提醒 ----------
echo -e "${CYAN}===== 重要后续操作 =====${NC}"
echo -e " 1. 若 dsh web 正在运行,请重启并务必带上 --patch 参数:"
echo -e "    ${YELLOW}npx @deepseek-ai/dsh web --patch${NC}"
echo -e " 2. 浏览器硬刷新(Ctrl+Shift+R)让插件 UI 生效。"
echo -e " 3. 大部分插件热插拔即时生效,个别需要重启服务。"
echo
echo -e "${YELLOW}--- 额外推荐(本脚本未自动安装) ---${NC}"
echo -e " · dsh-anchored-standard : 性能优化 preset(首轮工具收敛,跑分91→99)"
echo -e "   属于 preset 而非普通插件,需手动复制,详见仓库说明。"
echo -e " · deepseek-harness-desktop : 桌面版(免Node.js,双击即用)"
echo -e "   去 GitHub Releases 下载: github.com/anywhere-labs/deepseek-harness-desktop/releases"
echo -e " · dsh-poison-guard : 安装前供应链安全扫描(建议装第三方插件前先装)"
echo -e "   npm install -g dsh-poison-guard"
echo
if [[ "$FAILED" -gt 0 ]]; then
  echo -e "${YELLOW}提示: 失败的插件多为 GitHub 仓库,请检查网络/GitHub 访问权限后重试:${NC}"
  echo -e "  ${YELLOW}dsh plugin --profile ${PROFILE} add <失败的插件名>${NC}"
fi
exit 0
