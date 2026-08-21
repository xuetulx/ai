#!/usr/bin/env node
'use strict';

// dsh-plugin-guard CLI 入口（npm bin / 全局命令）
const cli = require('../lib/cli');
process.exit(cli.main());
