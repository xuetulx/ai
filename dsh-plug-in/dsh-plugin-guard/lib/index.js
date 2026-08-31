'use strict';

/**
 * dsh-plugin-guard / DSH 宿主插件
 * ---------------------------------------------------------
 * 作为 bundle 安装到 profile 后，DSH 启动时会自动执行：
 *   1. 扫描全部已加载插件，检测重复挂载 / 已知风险 / 配置缺失；
 *   2. 发现问题时向控制台输出 CRIT/WARN 告警；
 *   3. 通过命令（/guard）查看插件状态并一键启停。
 *
 * 插件 id 必须与这里导出的 name 一致：plugin-guard
 */

const core = require('./core');

const name = 'plugin-guard';
const inject = [];

function runCheck(profileName) {
  try {
    const scan = core.scanPlugins(profileName);
    const issues = core.runChecks(scan);
    const severe = issues.filter((i) => i.severity !== 'info');
    if (severe.length > 0) {
      console.log('\n[dsh-plugin-guard] 检测到 ' + severe.length + ' 个插件冲突/风险项：');
      for (const it of severe) {
        console.log('  [' + it.severity.toUpperCase() + '] ' + it.msg);
      }
      let effectNote = '修改后需重启生效';
      try {
        if (core.patchReloadOf(scan.packageJson) === 'live') effectNote = '该 profile 为 live 热重载，修改后即时生效';
      } catch {
        // 忽略
      }
      console.log('  提示：用 guard.bat status/check 查看详情或一键启停插件，' + effectNote + '。\n');
    } else {
      console.log('[dsh-plugin-guard] 插件树检查通过，未发现冲突或启动风险。');
    }
  } catch (e) {
    console.error('[dsh-plugin-guard] 检测失败: ' + (e && e.message));
  }
}

function apply(ctx) {
  const profileName = process.env.DSH_PROFILE || 'web';

  // 延迟到插件树加载完成后检测，避免启动阶段互相影响
  ctx.effect(() => {
    const timer = setTimeout(() => runCheck(profileName), 3000);
    return () => clearTimeout(timer);
  }, 'dsh-plugin-guard: boot check');

  // 命令系统通过 ctx 动态获取（不强制 inject），避免无命令服务时崩溃
  try {
    const cmd = ctx.get ? ctx.get('command', null) : (ctx.command || null);
    if (cmd) {
      cmd('guard', '插件监控：查看状态 / 一键启停')
        .action((argv) => {
          const scan = core.scanPlugins(profileName);
          const issues = core.runChecks(scan);
          const lines = [];
          lines.push('插件监控状态 (' + scan.plugins.length + ' 个条目):');
          for (const p of scan.plugins) {
            lines.push('  [' + (p.disabled ? 'X' : ' ') + '] ' + p.id);
          }
          if (issues.length) {
            lines.push('');
            lines.push('检测项:');
            for (const it of issues) lines.push('  [' + it.severity.toUpperCase() + '] ' + it.msg);
          }
          return lines.join('\n');
        });
    }
  } catch (e) {
    // 命令系统不存在或不可用，静默跳过；CLI 工具仍可正常使用
  }
}

module.exports = { name, apply, inject };
