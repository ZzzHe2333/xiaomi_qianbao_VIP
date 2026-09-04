/*
name: ZzzHe_小米钱包扫码登录
cron: 0 0 29 2 *
*/

const fs = require('fs');
const path = require('path');

function findRuntime() {
  const qlDir = process.env.QL_DIR || '/ql';
  const qlData = process.env.QL_DATA_DIR || path.join(qlDir, 'data');
  const uniqueName = path.basename(__dirname);
  const candidates = [
    path.join(qlData, 'repo', uniqueName, 'xiaomi_runtime.cjs'),
    path.join(qlData, 'repo', 'ZzzHe2333_xiaomi_qianbao_VIP', 'xiaomi_runtime.cjs'),
    path.join(__dirname, 'xiaomi_runtime.cjs'),
  ];
  const found = candidates.find((item) => fs.existsSync(item));
  if (!found) throw new Error(`找不到 xiaomi_runtime.cjs：${candidates.join(', ')}`);
  return found;
}

require(findRuntime())
  .run({
    entryDir: __dirname,
    mode: 'login',
    taskName: 'ZzzHe_小米钱包扫码登录',
  })
  .catch((error) => {
    console.error(`❌ ZzzHe_小米钱包扫码登录启动失败：${error.stack || error.message}`);
    process.exit(1);
  });
