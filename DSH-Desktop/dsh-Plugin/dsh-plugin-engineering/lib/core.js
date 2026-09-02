'use strict';

/**
 * dsh-plugin-engineering / core
 * ---------------------------------------------------------
 * DSH 工程质量规则注入插件核心逻辑（零外部依赖）。
 *
 * 原理：DSH 内置 @deepseek-ai/dsh-agent-instructions 会自动发现并加载
 *   - 用户全局：$DSH_HOME/AGENTS.md（即 ~/.dsh/AGENTS.md）
 *   - 项目级：从项目根到 cwd 逐级的 AGENTS.md / CLAUDE.md / *.local.md
 *
 * 本插件职责：把插件内 rules/ 目录下的工程规范 + Python 规范 + HOOK 文字化
 * 合并为 $DSH_HOME/AGENTS.md。
 * 特性：
 *   - 多插件共存协议：识别任意 `dsh-plugin-*` 管理块，只重建自己的块，
 *     其他插件块原样保留，多个规则插件可同时挂载互不覆盖；
 *   - 保留用户区：AGENTS.md 中"所有插件管理块之外"的内容原样保留；
 *   - 首次接管自动备份：AGENTS.md.pre-plugin-engineering.bak（幂等，仅一次）；
 *   - 幂等同步：内容哈希无变化时不写文件；
 *   - 安全：失败不抛致命错，不阻塞 DSH 启动。
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

/* ------------------------------------------------------------------ *
 * 常量
 * ------------------------------------------------------------------ */

/** 插件 id：与 package.json name / cordis.patch.yml id 一致 */
const PLUGIN_ID = 'dsh-plugin-engineering';

/** 插件管理标记：同步区由两个标记夹住，用户勿改 */
const MARK_OPEN = '<!-- ===== ' + PLUGIN_ID + ' MANAGED SECTION (do not edit) ===== -->';
const MARK_CLOSE = '<!-- ===== end ' + PLUGIN_ID + ' ===== -->';

/** 首次接管时对既有 AGENTS.md 的备份文件名 */
const BACKUP_NAME = 'AGENTS.md.pre-plugin-engineering.bak';

/** 插件规则目录（相对本文件：<plugin>/rules） */
function rulesRootDir() {
  return path.join(__dirname, '..', 'rules');
}

/** DSH Harness home：优先 DSH_HOME 环境变量，其次 ~/.dsh */
function dshHomeDir() {
  if (process.env.DSH_HOME) return path.resolve(process.env.DSH_HOME);
  return path.join(os.homedir(), '.dsh');
}

/** 目标 AGENTS.md 路径 */
function agentsPath(homeDir) {
  return path.join(homeDir || dshHomeDir(), 'AGENTS.md');
}

/* ------------------------------------------------------------------ *
 * 规则扫描
 * ------------------------------------------------------------------ */

/**
 * 递归扫描规则目录，收集所有 .md 文件。
 * 返回按相对路径排序的 [{ rel, name, content }]。
 */
function scanRules(rulesDir) {
  const out = [];
  if (!fs.existsSync(rulesDir)) return out;
  const walk = (dir) => {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch (e) {
      console.warn('[' + PLUGIN_ID + '] 读取目录失败: ' + dir + ' - ' + e.message);
      return;
    }
    for (const ent of entries) {
      const full = path.join(dir, ent.name);
      try {
        if (ent.isDirectory()) {
          walk(full);
        } else if (ent.isFile() && ent.name.toLowerCase().endsWith('.md')) {
          const content = fs.readFileSync(full, 'utf8');
          const rel = path.relative(rulesDir, full).split(path.sep).join('/');
          out.push({ rel, name: ent.name, content });
        }
      } catch (e) {
        console.warn('[' + PLUGIN_ID + '] 跳过文件: ' + full + ' - ' + e.message);
      }
    }
  };
  walk(rulesDir);
  out.sort((a, b) => (a.rel < b.rel ? -1 : a.rel > b.rel ? 1 : 0));
  return out;
}

/* ------------------------------------------------------------------ *
 * 多插件共存协议
 * ------------------------------------------------------------------ */

/** 识别任意 `dsh-plugin-*` 管理块（含 id 捕获） */
const ANY_BLOCK_RE = /<!-- ===== (dsh-plugin-[\w-]+) MANAGED SECTION \(do not edit\) ===== -->[\s\S]*?<!-- ===== end \1 ===== -->/g;

/**
 * 从现有 AGENTS.md 拆分为用户区 + 其他插件块。
 * 自己的旧块会被剔除（渲染时重建），其他插件的块原样保留。
 * @returns {{ user: string, others: Array<{id: string, block: string}> }}
 */
function splitSections(existing) {
  if (!existing) return { user: '', others: [] };
  const others = [];
  const user = existing.replace(ANY_BLOCK_RE, (m, id) => {
    if (id !== PLUGIN_ID) others.push({ id, block: m });
    return '';
  }).trim();
  return { user, others };
}

/* ------------------------------------------------------------------ *
 * 渲染与合并
 * ------------------------------------------------------------------ */

/**
 * 生成 AGENTS.md 全文 = 用户区 + 所有插件管理块（按插件 id 稳定排序）。
 */
function renderAgents(userSection, others, rules) {
  const head = [
    '# DSH 工程质量（自动生成，来源: ai-configuration/02-RULE + 01-HOOK）',
    '',
    '> 本文件由 dsh-plugin-engineering 自动维护。两个管理标记之间的内容每次同步会重建，请勿手改；',
    '> 标记之外的内容为用户自定义区与其他插件区，原样保留。',
    ''
  ].join('\n');

  const body = rules.map((r) => {
    return '## ' + r.rel + '\n\n' + r.content.replace(/\s+$/, '') + '\n';
  }).join('\n---\n\n');

  const user = (userSection || '').trim();
  const parts = [];
  if (user) parts.push(user);
  // 自己的块按 id 与其他插件块一起稳定排序，保证任意插件先 sync 结果一致（幂等）
  const blocks = others.slice();
  blocks.push({ id: PLUGIN_ID, block: MARK_OPEN + '\n\n' + head + body + '\n\n' + MARK_CLOSE });
  blocks.sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  for (const b of blocks) parts.push(b.block);
  return parts.join('\n\n') + '\n';
}

/* ------------------------------------------------------------------ *
 * 同步与状态
 * ------------------------------------------------------------------ */

/**
 * 同步规则到 $DSH_HOME/AGENTS.md。
 * @param {object} opts { dshHome?, rulesDir?, dryRun? }
 * @returns {{ ok, action, agentsPath, rules, bytes, hash, backup?, error? }}
 */
function sync(opts) {
  const home = (opts && opts.dshHome) || dshHomeDir();
  const rulesDir = (opts && opts.rulesDir) || rulesRootDir();
  const dryRun = !!(opts && opts.dryRun);
  const target = agentsPath(home);

  const rules = scanRules(rulesDir);
  if (rules.length === 0) {
    return { ok: false, action: 'noop', agentsPath: target, rules: [], error: '规则目录无 .md 文件: ' + rulesDir };
  }

  let existing = '';
  if (fs.existsSync(target)) {
    try {
      existing = fs.readFileSync(target, 'utf8');
    } catch (e) {
      return { ok: false, action: 'noop', agentsPath: target, rules, error: '读取 AGENTS.md 失败: ' + e.message };
    }
  }

  // 首次接管（文件存在但无任何插件管理标记）→ 备份一次（幂等）
  let backup = null;
  if (existing && !ANY_BLOCK_RE.test(existing)) {
    const bakPath = path.join(home, BACKUP_NAME);
    if (!fs.existsSync(bakPath)) {
      try {
        fs.mkdirSync(home, { recursive: true });
        fs.copyFileSync(target, bakPath);
        backup = bakPath;
      } catch (e) {
        return { ok: false, action: 'noop', agentsPath: target, rules, error: '备份 AGENTS.md 失败: ' + e.message };
      }
    } else {
      backup = bakPath + ' (已存在，跳过)';
    }
  }

  const { user, others } = splitSections(existing);
  const content = renderAgents(user, others, rules);
  const hash = crypto.createHash('sha256').update(content).digest('hex').slice(0, 16);

  // 幂等：内容无变化则跳过写入
  const currentHash = existing
    ? crypto.createHash('sha256').update(existing).digest('hex').slice(0, 16)
    : null;
  if (currentHash === hash) {
    return { ok: true, action: 'noop', agentsPath: target, rules, bytes: Buffer.byteLength(content), hash, backup };
  }

  if (dryRun) {
    return { ok: true, action: 'dry-run', agentsPath: target, rules, bytes: Buffer.byteLength(content), hash, backup };
  }

  try {
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, content, 'utf8');
  } catch (e) {
    return { ok: false, action: 'noop', agentsPath: target, rules, bytes: Buffer.byteLength(content), hash, error: '写入 AGENTS.md 失败: ' + e.message };
  }
  return { ok: true, action: 'written', agentsPath: target, rules, bytes: Buffer.byteLength(content), hash, backup };
}

/**
 * 状态总览。
 */
function status(opts) {
  const home = (opts && opts.dshHome) || dshHomeDir();
  const rulesDir = (opts && opts.rulesDir) || rulesRootDir();
  const target = agentsPath(home);
  const rules = scanRules(rulesDir);

  let exists = false;
  let managed = false;
  let userBytes = 0;
  let totalBytes = 0;
  let hash = null;
  try {
    if (fs.existsSync(target)) {
      const raw = fs.readFileSync(target, 'utf8');
      exists = true;
      totalBytes = Buffer.byteLength(raw);
      managed = raw.includes(MARK_OPEN);
      userBytes = Buffer.byteLength(splitSections(raw).user);
      hash = crypto.createHash('sha256').update(raw).digest('hex').slice(0, 16);
    }
  } catch (e) {
    return { ok: false, rules, agentsPath: target, error: '读取 AGENTS.md 失败: ' + e.message };
  }

  const bakPath = path.join(home, BACKUP_NAME);
  const backup = fs.existsSync(bakPath) ? bakPath : null;

  return { ok: true, rules, agentsPath: target, exists, managed, userBytes, totalBytes, hash, backup };
}

module.exports = {
  PLUGIN_ID,
  MARK_OPEN,
  MARK_CLOSE,
  BACKUP_NAME,
  rulesRootDir,
  dshHomeDir,
  agentsPath,
  scanRules,
  splitSections,
  renderAgents,
  sync,
  status
};
