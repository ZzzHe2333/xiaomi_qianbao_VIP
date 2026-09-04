const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const PROJECT_URL = 'https://github.com/ZzzHe2333/xiaomi_qianbao_VIP';

const FONT = {
  X: ['10001', '01010', '00100', '01010', '10001'],
  I: ['11111', '00100', '00100', '00100', '11111'],
  A: ['01110', '10001', '11111', '10001', '10001'],
  O: ['01110', '10001', '10001', '10001', '01110'],
  M: ['10001', '11011', '10101', '10001', '10001'],
  Q: ['01110', '10001', '10101', '10010', '01101'],
  N: ['10001', '11001', '10101', '10011', '10001'],
  B: ['11110', '10001', '11110', '10001', '11110'],
};

function formatDate(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function renderWord(word) {
  const letters = [...word].map((char) => FONT[char]);
  for (let row = 0; row < 5; row += 1) {
    console.log(
      letters
        .map((letter) => letter[row].replace(/1/g, '■').replace(/0/g, '□'))
        .join('  '),
    );
  }
}

function printBanner(taskName) {
  console.log('\n' + '='.repeat(92));
  renderWord('XIAOMI');
  console.log('');
  renderWord('QIANBAO');
  console.log('-'.repeat(92));
  console.log(`任务名称：${taskName}`);
  console.log(`当前时间：${formatDate()}`);
  console.log(`项目地址：${PROJECT_URL}`);
  console.log('项目说明：本项目永久免费开源，欢迎学习、使用和 Star，请勿付费购买。');
  console.log('='.repeat(92) + '\n');
}

function qlDir() {
  return process.env.QL_DIR || '/ql';
}

function qlDataDir() {
  return process.env.QL_DATA_DIR || path.join(qlDir(), 'data');
}

function repoDirFromEntry(entryDir) {
  const uniqueName = path.basename(entryDir);
  const candidates = [
    path.join(qlDataDir(), 'repo', uniqueName),
    path.join(qlDataDir(), 'repo', 'ZzzHe2333_xiaomi_qianbao_VIP'),
    entryDir,
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, 'xiaomi_common.py'))) {
      return candidate;
    }
  }
  throw new Error(`无法定位项目仓库目录，已检查：${candidates.join(', ')}`);
}

function runPython(repoDir, mode, taskName) {
  const moduleName = mode === 'login' ? 'xiaomi_login' : 'xiaomi_daily';
  const lines = [
    'import builtins',
    'import xiaomi_common',
    'orig_notify = xiaomi_common.ql_notify',
    'def _notify(title, content, qlapi=None):',
    "    return orig_notify(title, content, qlapi or getattr(builtins, 'QLAPI', None))",
    'xiaomi_common.ql_notify = _notify',
    `from ${moduleName} import main`,
    `${moduleName} = __import__('${moduleName}')`,
    `if hasattr(${moduleName}, 'ql_notify'): ${moduleName}.ql_notify = _notify`,
  ];

  // 扫码登录必须立即执行；只有每日任务才执行启动随机延迟。
  if (mode === 'daily') {
    lines.push('xiaomi_common.random_start_delay()');
  }
  lines.push('raise SystemExit(main())');
  const bootstrap = lines.join('\n');

  const basePythonPath = process.env.PREV_PYTHONPATH || process.env.PYTHONPATH || '';
  const childEnv = {
    ...process.env,
    PREV_PYTHONPATH: basePythonPath,
    PYTHONPATH: [
      path.join(qlDir(), 'shell', 'preload'),
      path.join(qlDataDir(), 'config'),
      path.join(qlDataDir(), 'scripts'),
      repoDir,
      basePythonPath,
    ]
      .filter(Boolean)
      .join(':'),
  };

  console.log(`▶ 准备调用 Python 核心：${moduleName}.py`);
  if (mode === 'login') {
    console.log('▶ 扫码登录模式：不执行随机延迟，立即获取二维码。');
  }

  const result = spawnSync('python3', ['-c', bootstrap], {
    cwd: repoDir,
    env: childEnv,
    stdio: 'inherit',
  });

  if (result.error) throw result.error;
  const status = typeof result.status === 'number' ? result.status : 1;
  if (status !== 0) {
    throw new Error(`${taskName} 执行失败，Python 退出码：${status}`);
  }
}

async function run({ entryDir, mode, taskName }) {
  printBanner(taskName);
  const repoDir = repoDirFromEntry(entryDir);
  console.log(`项目目录：${repoDir}`);
  runPython(repoDir, mode, taskName);
}

module.exports = { run };
