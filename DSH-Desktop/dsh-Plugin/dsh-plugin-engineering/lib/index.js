'use strict';

/**
 * dsh-plugin-engineering / DSH 宿主插件
 * ---------------------------------------------------------
 * 作为 bundle 安装到 profile 后，DSH 启动时自动执行：
 *   1. 启动延迟 3 秒后，后台把 rules/ 目录的工程规范同步为 $DSH_HOME/AGENTS.md；
 *   2. 幂等：内容无变化不写文件；失败仅告警，不阻塞 DSH 启动；
 *   3. 提供 /engineering 命令查看同步状态与规则清单。
 *
 * 插件 id 必须与这里导出的 name 一致：plugin-engineering
 */

const core = require('./core');

const name = 'plugin-engineering';
const inject = [];

function runSync(profileName) {
  const r = core.sync({});
  if (!r.ok) {
    console.error('[dsh-plugin-engineering] 规则同步失败: ' + r.error);
    return;
  }
  const verb = r.action === 'written' ? '已写入' : r.action === 'dry-run' ? '(dry-run)' : '无需变更(幂等)';
  console.log(
    '[dsh-plugin-engineering] 工程规范同步' + verb + ': ' + r.rules.length + ' 条规则 -> ' +
    r.agentsPath + ' (' + (r.bytes / 1024).toFixed(1) + ' KB, hash ' + r.hash + ')' +
    (r.backup ? ' | 备份: ' + r.backup : '')
  );
}

function apply(ctx) {
  const profileName = process.env.DSH_PROFILE || 'web';

  // 延迟到插件树加载完成后同步，避免启动阶段互相影响
  ctx.effect(() => {
    const timer = setTimeout(() => runSync(profileName), 3000);
    return () => clearTimeout(timer);
  }, 'dsh-plugin-engineering: boot sync');

  // 命令系统通过 ctx 动态获取（不强制 inject），避免无命令服务时崩溃
  try {
    const cmd = ctx.get ? ctx.get('command', null) : (ctx.command || null);
    if (cmd) {
      cmd('engineering', '工程质量注入：查看工程规范 + Python 规范 + HOOK 文字化同步状态')
        .action(() => {
          const st = core.status({});
          if (!st.ok) return '规则状态读取失败: ' + st.error;
          const lines = [];
          lines.push('工程质量注入状态 (' + st.rules.length + ' 条规则):');
          lines.push('  AGENTS.md : ' + (st.exists ? '存在' : '不存在') + (st.managed ? ' (本插件管理)' : ''));
          lines.push('  大小      : ' + (st.totalBytes / 1024).toFixed(1) + ' KB (用户区 ' + (st.userBytes / 1024).toFixed(1) + ' KB)');
          if (st.hash) lines.push('  hash      : ' + st.hash);
          if (st.backup) lines.push('  备份      : ' + st.backup);
          lines.push('  规则:');
          for (const r of st.rules.slice(0, 50)) lines.push('    - ' + r.rel);
          if (st.rules.length > 50) lines.push('    ... 等 ' + st.rules.length + ' 条');
          return lines.join('\n');
        });
    }
  } catch (e) {
    // 命令系统不存在或不可用，静默跳过；CLI 工具仍可正常使用
  }
}

module.exports = { name, apply, inject };
