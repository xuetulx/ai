'use strict';

/**
 * dsh-plugin-guard / core
 * ---------------------------------------------------------
 * DSH 插件冲突监控与一键启停核心逻辑（零外部依赖）。
 *
 * 职责：
 *   1. 扫描一个 DSH profile，解析 bundles + 各插件的 cordis.patch.yml
 *      + profile 自身的 cordis.patch.yml，汇总出插件清单与启停状态；
 *   2. 冲突 / 启动风险检测（重复 id、重复挂载同一包、已知风险插件、
 *      必需配置缺失等）；
 *   3. 安全编辑 profile 的 cordis.patch.yml，实现一键禁用 / 启用
 *      （自动备份，行级编辑，保留用户原有注释与配置）。
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

/* ------------------------------------------------------------------ *
 * 路径解析（对齐上游 deepseek-harness 语义）
 *   - DSH_HOME（或 ~/.dsh）是 Harness home；
 *   - profiles 位于 <home>/profiles/<name>；
 *   - home 级用户 patch 层位于 <home>/cordis.patch.yml，
 *     应用在"每个 profile 自身层"之上。
 * ------------------------------------------------------------------ */

/**
 * 计算 DSH Harness home 目录。
 * 优先环境变量 DSH_HOME，其次 ~/.dsh。
 */
function dshHome() {
  if (process.env.DSH_HOME) return path.resolve(process.env.DSH_HOME);
  return path.join(os.homedir(), '.dsh');
}

/**
 * 计算 DSH profiles 根目录（<home>/profiles）。
 */
function profilesRoot() {
  return path.join(dshHome(), 'profiles');
}

/**
 * 获取指定 profile 的目录（默认 web）。
 */
function profileDir(profile = 'web') {
  return path.join(profilesRoot(), profile);
}

/**
 * home 级用户 patch 文件（$DSH_HOME/cordis.patch.yml）。
 * 上游在 bundle 层 + profile 自身层之后、CLI --patch 覆盖层之前应用。
 */
function homePatchFile() {
  return path.join(dshHome(), 'cordis.patch.yml');
}

/* ------------------------------------------------------------------ *
 * bundle 解析（对齐上游 resolveBundleDir 双锚点）
 *   锚点 1：profile 目录（第三方 bundle / link 安装的插件）；
 *   锚点 2：dsh 安装（内置 bundle，如 @deepseek-ai/dsh-base）。
 * patch 文件名不硬编码，读取 bundle manifest 的 dsh.bundle.patch 字段。
 * ------------------------------------------------------------------ */

/**
 * 收集候选"node_modules 根"列表：
 *   profile 自身、profiles 根、~/.dsh、DSH_HOME、npm 全局根。
 */
function candidateNodeModulesRoots(profileDirPath) {
  const roots = new Set();
  roots.add(path.join(profileDirPath, 'node_modules'));
  roots.add(path.join(path.dirname(profileDirPath), 'node_modules'));
  roots.add(path.join(dshHome(), 'node_modules'));
  if (process.env.DSH_HOME) roots.add(path.join(process.env.DSH_HOME, 'node_modules'));
  try {
    const g = execSync('npm root -g', { encoding: 'utf8', windowsHide: true }).trim();
    if (g) roots.add(g);
  } catch {
    // 无 npm 时静默降级
  }
  return [...roots];
}

/**
 * 查找内置 bundle 的包目录（从候选根 + dsh 安装嵌套两层解析）。
 */
function findBuiltinBundle(profileDirPath, pkgName) {
  for (const root of candidateNodeModulesRoots(profileDirPath)) {
    // 直接 node_modules/<pkg>
    const direct = path.join(root, pkgName);
    if (fs.existsSync(path.join(direct, 'package.json'))) return direct;
    // 嵌套于 @deepseek-ai/dsh 内（全局安装形态）
    const nested = path.join(root, '@deepseek-ai', 'dsh', 'node_modules', pkgName);
    if (fs.existsSync(path.join(nested, 'package.json'))) return nested;
    // 扁平 node_modules/<pkg>（pnpm 全局依赖提升形态）
    const hoisted = path.join(root, pkgName.replace(/^@[^/]+\//, ''));
    if (fs.existsSync(path.join(hoisted, 'package.json'))) return hoisted;
  }
  return null;
}

/**
 * 双锚点解析 bundle 目录：profile node_modules -> dsh 安装。
 */
function findBundleDir(profileDirPath, pkgName) {
  const local = path.join(profileDirPath, 'node_modules', pkgName);
  if (fs.existsSync(path.join(local, 'package.json'))) return local;
  return findBuiltinBundle(profileDirPath, pkgName);
}

/**
 * 计算 bundle 的 patch 文件路径。
 * 优先 bundle package.json 的 dsh.bundle.patch 声明，回退 cordis.patch.yml。
 */
function bundlePatchFile(bundleDir) {
  const manifest = readJson(path.join(bundleDir, 'package.json'));
  const declared = manifest && manifest.dsh && manifest.dsh.bundle && manifest.dsh.bundle.patch;
  const name = declared && typeof declared === 'string' ? declared.replace(/^\.\//, '') : 'cordis.patch.yml';
  return path.join(bundleDir, name);
}

/**
 * 读取 profile manifest 的 patchReload（'live' | 'startup'，默认 'live'）。
 */
function patchReloadOf(pkgJson) {
  const v = pkgJson && pkgJson.dsh && pkgJson.dsh.profile && pkgJson.dsh.profile.patchReload;
  return v === 'startup' ? 'startup' : 'live';
}

/* ------------------------------------------------------------------ *
 * 迷你 YAML（数组）解析
 * ---------------------------------------------------------
 * 仅支持本工具需要的 YAML 子集：
 *   - 顶层 / 嵌套数组项（"- key: value"）
 *   - 缩进键值对
 *   - 单双引号字符串、数字、布尔、null
 *   - 注释行（# 开头）
 *   - !!js 表达式（原样保留为字符串）
 * 足以解析 cordis.patch.yml 的常见形态。
 * ------------------------------------------------------------------ */

function parseScalar(raw) {
  const s = String(raw).trim();
  if (s === '') return '';
  if (s.startsWith('!!js')) return s;
  if (
    (s.startsWith('"') && s.endsWith('"')) ||
    (s.startsWith("'") && s.endsWith("'"))
  ) {
    return s.slice(1, -1);
  }
  if (s === 'true') return true;
  if (s === 'false') return false;
  if (s === 'null' || s === '~') return null;
  if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s);
  return s;
}

/**
 * 解析一段 YAML 文本为 JS 值（仅数组/对象/标量子集）。
 *
 * 支持 cordis.patch.yml 常见形态：
 *   - 数组项："- key: value" / "- value"
 *   - 键值对："key: value"
 *   - 嵌套（更深的缩进）：子数组、子对象
 *   - 注释（# 开头）与空行自动忽略
 *   - "!!js ..." 表达式原样保留为字符串
 */
function parseYaml(text) {
  // 预处理：去掉注释与空行，记录缩进
  const lines = String(text)
    .split(/\r?\n/)
    .map((l) => {
      const m = l.match(/^(\s*)(.*)$/);
      return { indent: m[1].length, text: m[2] };
    })
    .filter((l) => l.text !== '' && !/^#/.test(l.text));

  /**
   * 递归解析 [start, end) 区间内的兄弟块。
   * 兄弟块共享同一缩进 base；第一个行决定块类型（数组或对象）。
   */
  function parseBlock(start, end) {
    if (start >= end) return null;
    const base = lines[start].indent;
    const isArray = /^-\s/.test(lines[start].text);
    const result = isArray ? [] : {};

    let i = start;
    while (i < end) {
      const line = lines[i];
      if (line.indent !== base) {
        i++;
        continue;
      }

      if (isArray) {
        // ---- 数组项 ----
        const rest = line.text.replace(/^-\s*/, '');
        const kv = rest.match(/^([A-Za-z0-9_./@-]+):\s*(.*)$/);
        // 子块范围：后续缩进 > base 的行
        let j = i + 1;
        while (j < end && lines[j].indent > base) j++;
        const hasChild = i + 1 < j;
        const child = hasChild ? parseBlock(i + 1, j) : null;

        if (kv) {
          const key = kv[1];
          const inline = kv[2].trim();
          const item = {};
          if (child !== null && inline === '') {
            item[key] = child; // "key:" + 嵌套块
          } else {
            item[key] = inline === '' ? null : parseScalar(inline);
            // 若还有子块且为对象，合并进同一 item（如 "- id: x" + "  disabled: true"）
            if (child && typeof child === 'object' && !Array.isArray(child)) {
              Object.assign(item, child);
            }
          }
          result.push(item);
        } else {
          result.push(child !== null ? child : parseScalar(rest));
        }
        i = j;
      } else {
        // ---- 对象键值对 ----
        const kv = line.text.match(/^([A-Za-z0-9_./@-]+):\s*(.*)$/);
        if (!kv) {
          i++;
          continue;
        }
        let j = i + 1;
        while (j < end && lines[j].indent > base) j++;
        const hasChild = i + 1 < j;
        const key = kv[1];
        const inline = kv[2].trim();
        if (hasChild) {
          result[key] = parseBlock(i + 1, j);
        } else {
          result[key] = inline === '' ? null : parseScalar(inline);
        }
        i = j;
      }
    }
    return result;
  }

  if (lines.length === 0) return [];
  return parseBlock(0, lines.length);
}

/**
 * 解析 cordis.patch.yml，返回顶层数组项列表。
 * 每项结构形如：
 *   { insert: [ {id,name,config,inject,disabled} ... ] }
 *   { id: 'xxx', name: 'yyy', config: {...}, disabled: true }
 */
function parsePatch(text) {
  const root = parseYaml(text);
  if (!Array.isArray(root)) return [];
  return root;
}

/**
 * 把顶层条目对象序列化为 YAML 行（用于新增/展示）。
 */
function serializeEntry(entry) {
  const lines = [];
  const pushObj = (obj, indent, inArray) => {
    for (const [k, v] of Object.entries(obj)) {
      if (v === null || v === undefined) {
        lines.push(' '.repeat(indent) + (inArray ? '- ' : '') + k + ':');
        inArray = false;
      } else if (Array.isArray(v)) {
        if (inArray) {
          lines.push(' '.repeat(indent) + k + ':');
          indent += 2;
        }
        for (const it of v) {
          if (typeof it === 'object') pushObj(it, indent + (inArray ? 0 : 2), true);
          else lines.push(' '.repeat(indent) + '- ' + String(it));
        }
        inArray = false;
      } else if (typeof v === 'object') {
        if (inArray) {
          lines.push(' '.repeat(indent) + k + ':');
          pushObj(v, indent + 2, false);
        } else {
          lines.push(' '.repeat(indent) + k + ':');
          pushObj(v, indent + 2, false);
        }
        inArray = false;
      } else {
        lines.push(' '.repeat(indent) + (inArray ? '- ' : '') + k + ': ' + yamlScalar(v));
        inArray = false;
      }
    }
  };
  if (entry.insert && Array.isArray(entry.insert)) {
    lines.push('- insert:');
    for (const it of entry.insert) pushObj(it, 4, true);
  } else {
    pushObj(entry, 0, true);
  }
  return lines;
}

function yamlScalar(v) {
  if (typeof v === 'string') {
    if (/^[A-Za-z0-9_./@:-]+$/.test(v) && !/^(true|false|null|~)$/.test(v)) return v;
    return JSON.stringify(v);
  }
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  if (v === null) return 'null';
  return String(v);
}

/* ------------------------------------------------------------------ *
 * profile 扫描
 * ------------------------------------------------------------------ */

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return null;
  }
}

function readText(file) {
  try {
    return fs.readFileSync(file, 'utf8');
  } catch {
    return null;
  }
}

/**
 * 内置宿主 bundle：由 dsh 安装提供（不在 profile node_modules），
 * 提供基础插件行（base layer）。对齐上游 INSTALLATION_OWNED_PROFILE_TUPLES。
 * 通过双锚点解析从 dsh 安装目录读取其 patch 文件。
 */
const BUILTIN_BUNDLES = ['@deepseek-ai/dsh-base', '@deepseek-ai/dsh-web-app', '@deepseek-ai/dsh-headless'];

/**
 * 扫描一个 profile，返回：
 * {
 *   profile, profileDir, packageJson,
 *   bundles: [包名...],
 *   patchReload: 'live' | 'startup',
 *   bundleSources: [ { name, pkgName, dir, patchFile, builtin } ],
 *   patchEntries: [ profile 自身 cordis.patch.yml 顶层条目 ],
 *   homePatchFile?, homePatchEntries?,
 *   plugins: [ { id, name, pkg, source, enabled, disabled, config, inject, entryIds } ],
 *   errors: [string]
 * }
 */
function scanPlugins(profile = 'web') {
  const dir = profileDir(profile);
  const result = {
    profile,
    profileDir: dir,
    packageJson: null,
    bundles: [],
    patchReload: 'live',
    bundleSources: [],
    patchEntries: [],
    plugins: [],
    errors: [],
  };

  if (!fs.existsSync(dir)) {
    result.errors.push(`profile 目录不存在: ${dir}`);
    return result;
  }

  const pkgJson = readJson(path.join(dir, 'package.json'));
  result.packageJson = pkgJson;
  if (!pkgJson) {
    result.errors.push(`无法读取 ${dir}/package.json`);
    return result;
  }

  const bundles = pkgJson.dsh?.profile?.bundles || pkgJson.bundles || [];
  result.bundles = Array.isArray(bundles) ? bundles : [];

  // 收集每个 bundle 包插入的插件行
  const byId = new Map(); // id -> plugin 汇总
  const byName = new Map(); // 包名(name) -> [{id, source, bundle}]

  const register = (bundle, entry, source) => {
    const id = entry.id;
    if (!id) return;
    const name = entry.name || id;
    const mount = { id, source, bundle };
    let rec = byId.get(id);
    if (!rec) {
      rec = { id, name, pkg: name, source, bundle, config: entry.config || {}, inject: entry.inject || [], disabled: !!entry.disabled, enabled: !entry.disabled, entryIds: [] };
      byId.set(id, rec);
    } else {
      // 同一 id 被多个位置插入 => 重复挂载
      rec.entryIds.push(`${bundle}(${source})`);
    }
    rec.entryIds.push(`${bundle}(${source})`);
    if (!byName.has(name)) byName.set(name, []);
    byName.get(name).push(mount);
  };

  result.patchReload = patchReloadOf(pkgJson);
  result.bundleSources = []; // 每个 bundle 的解析信息 { name, pkgName, dir, patchFile, builtin }

  for (const bundle of result.bundles) {
    const pkgName = normalizeBundleName(bundle);
    if (!pkgName) continue; // 过滤空字符串
    const bundleDir = findBundleDir(dir, pkgName);
    if (!bundleDir) {
      result.errors.push(`bundle [${bundle}] 未安装（profile node_modules 与 dsh 安装均未找到 ${pkgName}）`);
      continue;
    }
    const patchFile = bundlePatchFile(bundleDir);
    const text = readText(patchFile);
    if (text === null) {
      result.errors.push(`bundle [${bundle}] 未找到 patch 文件（${path.basename(patchFile)}）`);
      continue;
    }
    const builtin = BUILTIN_BUNDLES.includes(pkgName);
    result.bundleSources.push({ name: bundle, pkgName, dir: bundleDir, patchFile, builtin });
    const entries = parsePatch(text);
    for (const e of entries) {
      if (e.insert && Array.isArray(e.insert)) {
        for (const it of e.insert) register(bundle, it, 'insert');
      } else if (e.id) {
        // 非 insert 的顶层条目：通常是对既有插件行的 config 覆盖 /
        // 禁用（如 modsearch 覆盖 web.searchProvider）。若 id 已存在则
        // 应用为覆盖；否则记录为"对内置插件行的补丁"。
        if (byId.has(e.id)) {
          applyOverride(byId, e);
        } else {
          const rec = {
            id: e.id,
            name: e.name || e.id,
            pkg: e.name || e.id,
            source: 'patch-config',
            bundle,
            config: e.config || {},
            inject: e.inject || [],
            disabled: !!e.disabled,
            enabled: !e.disabled,
            entryIds: [`${bundle}(patch-config)`],
          };
          byId.set(e.id, rec);
        }
      }
    }
  }

  // 应用 profile 自身 cordis.patch.yml 的禁用/配置覆盖
  const ownPatchFile = path.join(dir, 'cordis.patch.yml');
  const ownText = readText(ownPatchFile);
  if (ownText !== null) {
    result.patchEntries = parsePatch(ownText);
    for (const e of result.patchEntries) {
      if (e.insert && Array.isArray(e.insert)) {
        for (const it of e.insert) applyOverride(byId, it);
      } else {
        applyOverride(byId, e);
      }
    }
  }

  // 应用 home 级用户 patch 层（$DSH_HOME/cordis.patch.yml），优先级最高
  const homeFile = homePatchFile();
  const homeText = readText(homeFile);
  if (homeText !== null) {
    result.homePatchFile = homeFile;
    result.homePatchEntries = parsePatch(homeText);
    for (const e of result.homePatchEntries) {
      if (e.insert && Array.isArray(e.insert)) {
        for (const it of e.insert) applyOverride(byId, it);
      } else {
        applyOverride(byId, e);
      }
    }
  }

  result.plugins = [...byId.values()];

  // 附加信息：同一包名被多个不同 id 挂载（double-mount 信号）
  for (const [name, mounts] of byName) {
    const uniqIds = [...new Set(mounts.map((m) => m.id))];
    if (uniqIds.length > 1) {
      for (const m of mounts) {
        const rec = byId.get(m.id);
        if (rec) {
          rec.doubleMountInfo = rec.doubleMountInfo || [];
          rec.doubleMountInfo.push(`${name}(${uniqIds.join(',')})`);
        }
      }
    }
  }

  return result;
}

function normalizeBundleName(bundle) {
  let s = String(bundle).trim();
  if (!s) return '';
  // workspace:../pkg 或 workspace:pkg -> 取包名（pnpm workspace 协议）
  if (s.startsWith('workspace:')) {
    s = s.slice(10).replace(/\\/g, '/').replace(/\/+$/, '');
    const seg = s.split('/');
    s = seg[seg.length - 1];
  }
  // github:owner/repo#branch -> repo
  if (s.startsWith('github:')) {
    s = s.slice(7).split('#')[0].replace(/\/+$/, '');
    const seg = s.split('/');
    s = seg[seg.length - 1];
  }
  // git+https://github.com/owner/repo.git -> repo
  if (s.startsWith('git+')) {
    const m = s.match(/([^/]+)\.git/);
    if (m) s = m[1];
  }
  // link:/abs/path 或 ~/path -> 取包名（最后一段）
  if (s.startsWith('link:')) {
    s = s.slice(5).replace(/\\/g, '/').replace(/\/+$/, '');
    const seg = s.split('/');
    s = seg[seg.length - 1];
  }
  return s.trim();
}

function applyOverride(byId, entry) {
  if (!entry.id) return;
  const rec = byId.get(entry.id);
  if (!rec) {
    // profile patch 里引用了未知 id（可能是运行时动态 id），记录
    byId.set(entry.id, {
      id: entry.id,
      name: entry.name || entry.id,
      pkg: '(profile patch)',
      source: 'profile',
      config: entry.config || {},
      inject: entry.inject || [],
      disabled: !!entry.disabled,
      enabled: !entry.disabled,
      entryIds: [],
    });
    return;
  }
  if (entry.disabled !== undefined) {
    rec.disabled = !!entry.disabled;
    rec.enabled = !rec.disabled;
  }
  if (entry.config && typeof entry.config === 'object') {
    rec.config = { ...rec.config, ...entry.config };
  }
}

/* ------------------------------------------------------------------ *
 * 冲突 / 风险检测
 * ------------------------------------------------------------------ */

/**
 * 内置风险规则：已知会导致 DSH 启动失败或行为异常的插件。
 * 支持按 id 或按包名匹配；check 返回 { severity, msg } 或 null。
 */
const RISK_RULES = [
  {
    ids: ['ui-obsidian-memory'],
    pkg: ['dsh-client-ui-obsidian-memory'],
    reason: 'Obsidian Memory 需要 vaultPath 配置，缺失时启动直接崩溃',
    check: (p) => {
      if (!p.config || !p.config.vaultPath) {
        return { severity: 'critical', msg: `缺少 config.vaultPath，启动会报 "Cannot read properties of undefined (reading 'vaultPath')"` };
      }
      return null;
    },
  },
  {
    ids: ['awiki', 'awiki-provider', 'awiki-summary-provider'],
    pkg: ['@awiki/dsh-plugin'],
    reason: 'AWiki 依赖 IM Core（@awiki/im-core-node）外部服务，初始化失败会中断 webServer 注册',
    check: (p) => {
      return { severity: 'warning', msg: '依赖 IM 外部服务，初始化失败会导致 webServer 无法注册、网页打不开；如不使用可禁用' };
    },
  },
  {
    ids: ['better-sidebar'],
    pkg: ['dsh-better-sidebar'],
    reason: '与 @linxin666/dsh-web-ui-all 等聚合包存在 double-mount 风险（重复注册 /sidebar/api 导致整树启动失败）',
    check: (p, scan) => {
      // 若同时存在聚合包挂载了同一包名，则提示
      const aggIds = scan.plugins.filter((x) => x.pkg.includes('dsh-web-ui-all') && x.enabled);
      if (aggIds.length > 0) {
        return { severity: 'warning', msg: '可能与 @linxin666/dsh-web-ui-all 重复挂载同一包（double-mount）；确认聚合包在前且其 !!js 防护表达式生效' };
      }
      return null;
    },
  },
];

/**
 * 运行全部检测，返回风险列表：
 * [ { type, severity: 'critical'|'warning'|'info', msg, pluginId? } ]
 */
function runChecks(scan) {
  const issues = [];

  // 1) 重复 id
  const idCount = new Map();
  for (const p of scan.plugins) {
    idCount.set(p.id, (idCount.get(p.id) || 0) + 1);
    if (p.entryIds.length > 1 && new Set(p.entryIds).size > 1) {
      issues.push({
        type: 'duplicate-id',
        severity: 'critical',
        msg: `插件 id "${p.id}" 被多个位置挂载: ${[...new Set(p.entryIds)].join(', ')}`,
        pluginId: p.id,
      });
    }
  }

  // 2) double-mount：同一包名被多个不同 id 挂载（重复注册路由风险）
  for (const p of scan.plugins) {
    if (p.doubleMountInfo && p.doubleMountInfo.length) {
      const uniq = [...new Set(p.doubleMountInfo)];
      issues.push({
        type: 'double-mount',
        severity: 'warning',
        msg: `插件 "${p.id}" 的包被多个 id 同时挂载 (${uniq.join(', ')})，可能重复注册路由导致启动失败；请确认聚合包在前且 !!js 防护表达式生效`,
        pluginId: p.id,
      });
    }
  }

  // 3) 已知风险规则
  for (const p of scan.plugins) {
    for (const rule of RISK_RULES) {
      const matchId = rule.ids.includes(p.id);
      const matchPkg = (rule.pkg || []).some((pk) => p.pkg.includes(pk));
      if (matchId || matchPkg) {
        if (!p.disabled) {
          const r = rule.check(p, scan);
          if (r) {
            issues.push({ type: 'known-risk', severity: r.severity, msg: `[${p.id}] ${r.msg}`, pluginId: p.id });
          }
        } else {
          issues.push({
            type: 'known-risk',
            severity: 'info',
            msg: `[${p.id}] 已知风险插件（已禁用，不影响启动）: ${rule.reason}`,
            pluginId: p.id,
          });
        }
      }
    }
  }

  // 4) 配置覆盖但插件未启用
  for (const p of scan.plugins) {
    if (!p.disabled && !p.enabled && p.source === 'profile') {
      issues.push({
        type: 'config-orphan',
        severity: 'info',
        msg: `[${p.id}] profile patch 中引用了未启用插件`,
        pluginId: p.id,
      });
    }
  }

  return issues;
}

/* ------------------------------------------------------------------ *
 * 一键启停（安全编辑 cordis.patch.yml）
 * ------------------------------------------------------------------ */

/**
 * 读取并解析 profile 自身的 cordis.patch.yml 行结构。
 *
 * 仅关心"顶层条目"（缩进 0 的 `- id: xxx`），它们是对插件行的
 * 禁用 / 配置覆盖。返回：
 * {
 *   lines,
 *   entries: [{
 *     start,            // 条目起始行（- id 行）
 *     end,              // 条目结束行（下一个条目前的最后一行）
 *     id, disabledIdx,  // disabled 字段所在行，-1 表示无
 *     hasOtherFields,   // 除 id/disabled 外是否还有其他字段
 *     trailingBlank,    // 条目后跟随的连续空行数量（用于整条删除时清理）
 *   }]
 * }
 */
function analyzePatchFile(profile = 'web') {
  const dir = profileDir(profile);
  const file = path.join(dir, 'cordis.patch.yml');
  const text = readText(file);
  const result = { file, exists: text !== null, lines: [], entries: [] };
  if (text === null) return result;

  const lines = String(text).split(/\r?\n/);
  result.lines = lines;

  // 定位所有顶层条目的起始行（缩进 0 的 "- id: xxx"）
  const starts = [];
  for (let i = 0; i < lines.length; i++) {
    if (/^- id:\s*["']?[A-Za-z0-9_./@-]+/.test(lines[i])) {
      starts.push(i);
    }
  }

  for (let s = 0; s < starts.length; s++) {
    const start = starts[s];
    const end = s + 1 < starts.length ? starts[s + 1] - 1 : lines.length - 1;
    const entry = { start, end, id: null, disabledIdx: -1, hasOtherFields: false };
    for (let i = start; i <= end; i++) {
      const line = lines[i];
      const idm = line.match(/^- id:\s*["']?([A-Za-z0-9_./@-]+)["']?\s*$/);
      if (idm) entry.id = idm[1];
      const dism = line.match(/^\s{2,}disabled:\s*(true|false)\s*$/);
      if (dism) entry.disabledIdx = i;
      // 判断是否有其他字段（name/config/inject 等非注释、非空行）
      if (
        line.trim() !== '' &&
        !/^#/.test(line.trim()) &&
        !idm &&
        !dism &&
        !/^-\s+id:/.test(line.trim())
      ) {
        entry.hasOtherFields = true;
      }
    }
    // 计算条目后的连续空行/注释行（清理用）
    let trailingBlank = 0;
    for (let i = end + 1; i < lines.length; i++) {
      if (lines[i].trim() === '') trailingBlank++;
      else break;
    }
    entry.trailingBlank = trailingBlank;
    result.entries.push(entry);
  }

  return result;
}

/**
 * 设置某个插件的启用状态。
 * 修改 profile 的 cordis.patch.yml（自动备份为 .guard.bak）。
 */
function setPluginEnabled(profile, id, enabled) {
  const dir = profileDir(profile);
  if (!fs.existsSync(dir)) return { ok: false, error: `profile 目录不存在: ${dir}` };

  const file = path.join(dir, 'cordis.patch.yml');
  const bak = file + '.guard.bak';
  const existed = fs.existsSync(file);
  if (existed) {
    fs.copyFileSync(file, bak); // 备份
  }

  const a = analyzePatchFile(profile);
  let lines = a.lines.length ? [...a.lines] : [];
  if (lines.length === 0 || !existed) {
    // 新建文件：写入头注释
    lines = [
      '# Your patch layer for this dsh profile, applied after every bundle layer:',
      '# a top-level YAML array of loader patch entries (id-targeted config',
      '# overrides, disables, and insert lists; `!!js` expressions allowed).',
      '',
    ];
  }

  // 查找已有条目
  const target = a.entries.find((e) => e.id === id);

  if (enabled) {
    // ---------------- 启用 ----------------
    if (target && target.disabledIdx >= 0) {
      if (!target.hasOtherFields) {
        // 纯禁用条目（只有 id + disabled）：整条删除，连同尾随空行
        let delStart = target.start;
        // 若条目前有空行则一并删除（保留文件结构整洁）
        if (delStart > 0 && lines[delStart - 1].trim() === '') delStart--;
        const delEnd = target.end + 1 + target.trailingBlank;
        lines.splice(delStart, Math.min(delEnd, lines.length) - delStart);
      } else {
        // 有其他配置字段：仅移除 disabled 行
        lines.splice(target.disabledIdx, 1);
      }
    }
    // 若不存在该条目，说明它本来就没被禁用，无需修改
  } else {
    // ---------------- 禁用 ----------------
    if (target) {
      if (target.disabledIdx >= 0) {
        // 已有 disabled 行：确保值为 true
        if (lines[target.disabledIdx].indexOf('disabled: true') === -1) {
          lines[target.disabledIdx] = lines[target.disabledIdx].replace(/(disabled:\s*)(true|false)/, '$1true');
        }
      } else {
        // 有 id 条目但无 disabled 行：在条目块末尾插入
        const insertAt = target.end + 1;
        lines.splice(insertAt, 0, '  disabled: true');
      }
    } else {
      // 无该条目：追加
      // 确保文件末尾有空行分隔
      if (lines.length && lines[lines.length - 1].trim() !== '') lines.push('');
      lines.push(`- id: ${id}`);
      lines.push('  disabled: true');
    }
  }

  fs.writeFileSync(file, lines.join('\r\n') + '\r\n', 'utf8');

  // 读取 profile 的 patchReload（live 热重载 / startup 需重启），供 CLI 提示
  let patchReload = 'live';
  try {
    const mf = path.join(dir, 'package.json');
    if (fs.existsSync(mf)) {
      const manifest = JSON.parse(fs.readFileSync(mf, 'utf8'));
      patchReload = patchReloadOf(manifest);
    }
  } catch {
    // 忽略
  }
  return { ok: true, file, backup: existed ? bak : null, enabled, patchReload };
}

/* ------------------------------------------------------------------ *
 * 输出工具
 * ------------------------------------------------------------------ */

function fmtPlugin(p) {
  const status = p.disabled ? 'DISABLED' : 'enabled ';
  const src = p.pkg || p.source || '';
  return `  [${status}] ${p.id.padEnd(28)} <- ${src}`;
}

function fmtIssues(issues) {
  if (issues.length === 0) return '  (无)';
  const out = [];
  for (const it of issues) {
    const tag = it.severity === 'critical' ? 'CRIT' : it.severity === 'warning' ? 'WARN' : 'INFO';
    out.push(`  [${tag}] ${it.msg}`);
  }
  return out.join('\n');
}

module.exports = {
  dshHome,
  profilesRoot,
  profileDir,
  homePatchFile,
  findBundleDir,
  bundlePatchFile,
  patchReloadOf,
  scanPlugins,
  runChecks,
  setPluginEnabled,
  analyzePatchFile,
  parsePatch,
  serializeEntry,
  fmtPlugin,
  fmtIssues,
  RISK_RULES,
};
