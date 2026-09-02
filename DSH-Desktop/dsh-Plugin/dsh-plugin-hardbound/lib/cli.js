'use strict';

/**
 * dsh-plugin-hardbound / CLI
 * ---------------------------------------------------------
 * 命令行入口。用法：
 *   node cli.js status                查看规则与 AGENTS.md 状态
 *   node cli.js sync                  同步规则到 $DSH_HOME/AGENTS.md
 *   node cli.js sync --dry-run        只预览将写入的内容摘要（不写文件）
 *   node cli.js list                  仅列出规则文件
 *   node cli.js check                 检查 AGENTS.md 完整性（用户区保留/管理标记）
 *
 * 常用参数：
 *   --dsh-home <path>   指定 DSH home（默认 $DSH_HOME 或 ~/.dsh，测试用）
 *   --rules-dir <path>  指定规则目录（默认 <插件>/rules）
 */

const core = require('./core');

function parseArgs(argv) {
  const args = { cmd: null, dshHome: null, rulesDir: null, dryRun: false };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dsh-home') args.dshHome = argv[++i];
    else if (a === '--rules-dir') args.rulesDir = argv[++i];
    else if (a === '--dry-run') args.dryRun = true;
    else if (a.startsWith('--')) { /* ignore unknown */ }
    else if (args.cmd === null) args.cmd = a;
    else rest.push(a);
  }
  args.rest = rest;
  return args;
}

function opts(args) {
  const o = {};
  if (args.dshHome) o.dshHome = args.dshHome;
  if (args.rulesDir) o.rulesDir = args.rulesDir;
  return o;
}

function printHeader() {
  console.log('');
  console.log('  === dsh-plugin-hardbound ===');
  console.log('  dsh home  : ' + core.dshHomeDir());
  console.log('  rules dir : ' + core.rulesRootDir());
  console.log('');
}

function cmdStatus(args) {
  const st = core.status(opts(args));
  printHeader();
  if (!st.ok) {
    console.error('  [ERR] ' + st.error);
    return 1;
  }
  console.log('  规则数    : ' + st.rules.length + ' 条');
  console.log('  AGENTS.md : ' + st.agentsPath);
  console.log('    存在    : ' + (st.exists ? '是' : '否'));
  console.log('    插件管理: ' + (st.managed ? '是' : '否'));
  console.log('    大小    : ' + (st.totalBytes / 1024).toFixed(1) + ' KB (用户区 ' + (st.userBytes / 1024).toFixed(1) + ' KB)');
  console.log('    hash    : ' + (st.hash || '-'));
  console.log('    备份    : ' + (st.backup || '无'));
  console.log('');
  console.log('  规则文件:');
  for (const r of st.rules) console.log('    - ' + r.rel + ' (' + (r.content.length / 1024).toFixed(1) + ' KB)');
  console.log('');
  return 0;
}

function cmdSync(args) {
  const o = opts(args);
  o.dryRun = args.dryRun;
  const r = core.sync(o);
  printHeader();
  if (!r.ok) {
    console.error('  [ERR] ' + r.error);
    return 1;
  }
  const verb = r.action === 'written' ? '已写入' : r.action === 'dry-run' ? '(dry-run, 未写入)' : '无需变更(幂等)';
  console.log('  规则同步  : ' + verb);
  console.log('  规则数    : ' + r.rules.length + ' 条');
  console.log('  目标      : ' + r.agentsPath);
  console.log('  大小      : ' + (r.bytes / 1024).toFixed(1) + ' KB');
  console.log('  hash      : ' + r.hash);
  if (r.backup) console.log('  备份      : ' + r.backup);
  console.log('');
  return 0;
}

function cmdList(args) {
  const st = core.status(opts(args));
  if (!st.ok) {
    console.error('[ERR] ' + st.error);
    return 1;
  }
  for (const r of st.rules) console.log(r.rel);
  return 0;
}

function cmdCheck(args) {
  const st = core.status(opts(args));
  printHeader();
  if (!st.ok) {
    console.error('  [ERR] ' + st.error);
    return 1;
  }
  let bad = 0;
  if (!st.exists) {
    console.log('  [WARN] AGENTS.md 不存在，规则尚未注入。运行: node cli.js sync');
    bad++;
  } else {
    if (st.managed) console.log('  ✓ AGENTS.md 含本插件管理标记，规则区由插件维护');
    else {
      console.log('  [WARN] AGENTS.md 无本插件管理标记，首次 sync 将备份并接管');
      bad++;
    }
    if (st.userBytes > 0) console.log('  ✓ 用户自定义区已保留 (' + (st.userBytes / 1024).toFixed(1) + ' KB)');
    console.log('  hash  : ' + st.hash);
  }
  console.log('');
  return bad ? 2 : 0;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  switch (args.cmd) {
    case 'status': return cmdStatus(args);
    case 'sync': return cmdSync(args);
    case 'list': return cmdList(args);
    case 'check': return cmdCheck(args);
    case 'help':
    case '--help':
    case '-h':
    case undefined:
      console.log(`用法:
  node cli.js status                查看规则与 AGENTS.md 状态
  node cli.js sync                  同步规则到 $DSH_HOME/AGENTS.md
  node cli.js sync --dry-run        预览将写入内容（不写文件）
  node cli.js list                  列出规则文件
  node cli.js check                 检查 AGENTS.md 完整性
  --dsh-home <path>   指定 DSH home（默认 $DSH_HOME 或 ~/.dsh）
  --rules-dir <path>  指定规则目录（默认 <插件>/rules）
  --dry-run           仅预览不写入`);
      return 0;
    default:
      console.error('未知命令: ' + args.cmd + ' （用 help 查看用法）');
      return 1;
  }
}

if (require.main === module) {
  process.exit(main());
}

module.exports = { main };
