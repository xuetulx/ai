'use strict';

/**
 * dsh-plugin-guard / CLI
 * ---------------------------------------------------------
 * 命令行入口。用法：
 *   node cli.js scan|check [--profile web] [--json]
 *   node cli.js status [--profile web]
 *   node cli.js disable <id> [--profile web]
 *   node cli.js enable  <id> [--profile web]
 *   node cli.js list    [--profile web]   (仅列出插件 id)
 */

const core = require('./core');

function parseArgs(argv) {
  const args = { cmd: null, profile: 'web', json: false, ids: [] };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--profile') {
      args.profile = argv[++i] || 'web';
    } else if (a === '--json') {
      args.json = true;
    } else if (a.startsWith('--')) {
      // ignore unknown
    } else if (args.cmd === null) {
      args.cmd = a;
    } else {
      rest.push(a);
    }
  }
  args.ids = rest;
  return args;
}

function printHeader(profile) {
  console.log('');
  console.log('  === dsh-plugin-guard ===');
  console.log(`  profile : ${profile}`);
  console.log(`  目录     : ${core.profileDir(profile)}`);
  console.log('');
}

function cmdScan(args) {
  const scan = core.scanPlugins(args.profile);
  printHeader(args.profile);
  for (const e of scan.errors) console.log('  [ERR] ' + e);
  if (scan.skipped && scan.skipped.length) {
    console.log('  [SKIP] 内置宿主 bundle（无需安装）: ' + scan.skipped.join(', '));
  }
  console.log(`  bundles : ${scan.bundles.length}  插件条目 : ${scan.plugins.length}`);
  console.log('');
  for (const p of scan.plugins) {
    console.log(core.fmtPlugin(p));
  }
  if (args.json) {
    console.log(JSON.stringify(scan, null, 2));
  }
}

function cmdCheck(args) {
  const scan = core.scanPlugins(args.profile);
  const issues = core.runChecks(scan);
  printHeader(args.profile);
  for (const e of scan.errors) console.log('  [ERR] ' + e);
  console.log(`  插件条目 : ${scan.plugins.length}  检测项 : ${issues.length}`);
  console.log('');
  console.log(core.fmtIssues(issues));
  if (args.json) {
    console.log(JSON.stringify({ scan, issues }, null, 2));
  }
  const crit = issues.filter((i) => i.severity === 'critical').length;
  return crit > 0 ? 2 : 0;
}

function cmdStatus(args) {
  const scan = core.scanPlugins(args.profile);
  const issues = core.runChecks(scan);
  printHeader(args.profile);
  for (const e of scan.errors) console.log('  [ERR] ' + e);
  if (scan.skipped && scan.skipped.length) {
    console.log('  [SKIP] 内置宿主 bundle: ' + scan.skipped.join(', '));
  }
  const enabled = scan.plugins.filter((p) => !p.disabled).length;
  const disabled = scan.plugins.length - enabled;
  console.log(`  已启用 : ${enabled}  已禁用 : ${disabled}`);
  console.log('');
  if (issues.some((i) => i.severity === 'critical' || i.severity === 'warning')) {
    console.log('  ⚠ 检测到潜在问题：');
    console.log(core.fmtIssues(issues.filter((i) => i.severity !== 'info')));
    console.log('');
  } else {
    console.log('  ✓ 未检测到冲突或启动风险。');
    console.log('');
  }
  return 0;
}

function cmdList(args) {
  const scan = core.scanPlugins(args.profile);
  for (const p of scan.plugins) {
    console.log(`${p.disabled ? '#' : ''}${p.id}`);
  }
}

function cmdSet(args, enabled) {
  const id = args.ids[0];
  if (!id) {
    console.error(`用法: node cli.js ${enabled ? 'enable' : 'disable'} <plugin-id> [--profile web]`);
    return 1;
  }
  const r = core.setPluginEnabled(args.profile, id, enabled);
  if (!r.ok) {
    console.error('  [ERR] ' + r.error);
    return 1;
  }
  printHeader(args.profile);
  console.log(`  ✓ ${enabled ? '已启用' : '已禁用'} 插件 "${id}"`);
  console.log(`  文件  : ${r.file}`);
  if (r.backup) console.log(`  备份  : ${r.backup}`);
  console.log('');
  console.log('  注意：需要重启 dsh web（npx @deepseek-ai/dsh web --patch）才会生效。');
  console.log('');
  return 0;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  switch (args.cmd) {
    case 'scan':
      cmdScan(args);
      return 0;
    case 'check':
      return cmdCheck(args);
    case 'status':
      return cmdStatus(args);
    case 'list':
      cmdList(args);
      return 0;
    case 'disable':
      return cmdSet(args, false);
    case 'enable':
      return cmdSet(args, true);
    case 'help':
    case '--help':
    case '-h':
    case undefined:
      console.log(`用法:
  node cli.js scan               扫描并列出所有插件及状态
  node cli.js check              检测冲突与启动风险
  node cli.js status             概览状态
  node cli.js list               仅列出插件 id
  node cli.js disable <id>       一键禁用插件
  node cli.js enable  <id>       一键启用插件
  --profile <name>  指定 profile（默认 web）
  --json            输出 JSON`);
      return 0;
    default:
      console.error(`未知命令: ${args.cmd} （用 help 查看用法）`);
      return 1;
  }
}

if (require.main === module) {
  process.exit(main());
}

module.exports = { main };
