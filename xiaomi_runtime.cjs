const fs = require('fs');
const http = require('http');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');

const PROJECT_URL = 'https://github.com/ZzzHe2333/xiaomi_qianbao_VIP';
const RANDOM_DELAY_ENV = 'ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi';
const DEFAULT_DELAY = '30';
const DEFAULT_REMARK = '随机延迟';

function formatDate(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function printBanner(taskName) {
  const mi = [
    '■□□□■  ■■■■■',
    '■■□■■  □□■□□',
    '■□■□■  □□■□□',
    '■□□□■  □□■□□',
    '■□□□■  ■■■■■',
  ];
  const vip = [
    '■□□□■  ■■■■■  ■■■■□',
    '■□□□■  □□■□□  ■□□□■',
    '□■□■□  □□■□□  ■■■■□',
    '□■□■□  □□■□□  ■□□□□',
    '□□■□□  ■■■■■  ■□□□□',
  ];

  console.log('\n' + '='.repeat(56));
  mi.forEach((line) => console.log(line));
  console.log('');
  vip.forEach((line) => console.log(line));
  console.log('-'.repeat(56));
  console.log(`任务名称：${taskName}`);
  console.log(`当前时间：${formatDate()}`);
  console.log(`项目地址：${PROJECT_URL}`);
  console.log('项目说明：本项目永久免费开源，欢迎学习、使用和 Star，请勿付费购买。');
  console.log('='.repeat(56) + '\n');
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

function getInternalToken() {
  const shell = `
set -e
. "${qlDir()}/shell/share.sh"
. "${qlDir()}/shell/api.sh"
get_token
printf '%s' "$__ql_token__"
`;
  return execFileSync('bash', ['-lc', shell], {
    encoding: 'utf8',
    env: process.env,
    stdio: ['ignore', 'pipe', 'pipe'],
  }).trim();
}

function requestJson(method, requestPath, token, body) {
  return new Promise((resolve, reject) => {
    const payload = body == null ? null : JSON.stringify(body);
    const req = http.request(
      {
        host: '127.0.0.1',
        port: 5600,
        method,
        path: requestPath,
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${token}`,
          ...(payload
            ? {
                'Content-Type': 'application/json;charset=UTF-8',
                'Content-Length': Buffer.byteLength(payload),
              }
            : {}),
        },
      },
      (res) => {
        let raw = '';
        res.setEncoding('utf8');
        res.on('data', (chunk) => (raw += chunk));
        res.on('end', () => {
          try {
            const parsed = raw ? JSON.parse(raw) : {};
            resolve(parsed);
          } catch (error) {
            reject(new Error(`青龙接口返回非 JSON：${raw.slice(0, 300)}`));
          }
        });
      },
    );
    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

async function ensureRandomDelayEnv() {
  const current = process.env[RANDOM_DELAY_ENV];
  if (typeof current === 'string' && current.trim()) {
    console.log(`✅ 已读取青龙环境变量：${RANDOM_DELAY_ENV}=${current.trim()}`);
    return current.trim();
  }

  try {
    const token = getInternalToken();
    const query = `/open/envs?searchValue=${encodeURIComponent(RANDOM_DELAY_ENV)}`;
    const found = await requestJson('GET', query, token, null);
    const items = Array.isArray(found.data) ? found.data : [];
    const exact = items.find((item) => item && item.name === RANDOM_DELAY_ENV);

    if (exact) {
      if (Number(exact.status || 0) === 1) {
        process.env[RANDOM_DELAY_ENV] = DEFAULT_DELAY;
        console.log(`ℹ️ 环境变量 ${RANDOM_DELAY_ENV} 已存在但被禁用，本次临时使用 ${DEFAULT_DELAY}。`);
        return DEFAULT_DELAY;
      }
      const value = String(exact.value ?? '');
      process.env[RANDOM_DELAY_ENV] = value;
      console.log(`✅ 已从青龙数据库读取环境变量：${RANDOM_DELAY_ENV}=${value || '(空值)'}`);
      return value;
    }

    const created = await requestJson(
      'POST',
      '/open/envs',
      token,
      [
        {
          name: RANDOM_DELAY_ENV,
          value: DEFAULT_DELAY,
          remarks: DEFAULT_REMARK,
        },
      ],
    );

    if (created && created.code === 200) {
      process.env[RANDOM_DELAY_ENV] = DEFAULT_DELAY;
      console.log(`✅ 未检测到环境变量，已自动创建：${RANDOM_DELAY_ENV}=${DEFAULT_DELAY}，备注=${DEFAULT_REMARK}`);
      return DEFAULT_DELAY;
    }

    console.log(`⚠️ 自动创建环境变量失败，青龙返回：${JSON.stringify(created)}`);
  } catch (error) {
    console.log(`⚠️ v2.17.12 环境变量检测/创建失败：${error.message}`);
  }

  process.env[RANDOM_DELAY_ENV] = DEFAULT_DELAY;
  console.log(`⚠️ 本次运行临时使用默认值 ${DEFAULT_DELAY} 分钟。`);
  return DEFAULT_DELAY;
}

function runPython(repoDir, mode, taskName) {
  const moduleName = mode === 'login' ? 'xiaomi_login' : 'xiaomi_daily';
  const bootstrap = [
    'import builtins',
    'import xiaomi_common',
    'orig_notify = xiaomi_common.ql_notify',
    'def _notify(title, content, qlapi=None):',
    "    return orig_notify(title, content, qlapi or getattr(builtins, 'QLAPI', None))",
    'xiaomi_common.ql_notify = _notify',
    `from ${moduleName} import main`,
    `${moduleName} = __import__('${moduleName}')`,
    `if hasattr(${moduleName}, 'ql_notify'): ${moduleName}.ql_notify = _notify`,
    'xiaomi_common.random_start_delay()',
    'raise SystemExit(main())',
  ].join('\n');

  const basePythonPath = process.env.PREV_PYTHONPATH || process.env.PYTHONPATH || '';
  const childEnv = {
    ...process.env,
    PREV_PYTHONPATH: basePythonPath,
    PYTHONPATH: [
      path.join(qlDir(), 'shell', 'preload'),
      path.join(qlDataDir(), 'config'),
      path.join(qlDataDir(), 'scripts'),
      basePythonPath,
    ]
      .filter(Boolean)
      .join(':'),
  };

  console.log(`▶ 准备调用 Python 核心：${moduleName}.py`);
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
  await ensureRandomDelayEnv();
  const repoDir = repoDirFromEntry(entryDir);
  console.log(`项目目录：${repoDir}`);
  runPython(repoDir, mode, taskName);
}

module.exports = { run };
