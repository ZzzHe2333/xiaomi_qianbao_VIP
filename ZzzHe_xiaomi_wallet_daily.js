/*
name: ZzzHe_小米钱包每日任务
cron: 1 6 * * *

说明：
- 仅用于首次由青龙订阅自动创建任务时的默认时间：每天 06:01。
- 如果青龙中已存在该任务，则不主动修改用户已有的定时规则。
- 如果青龙中该任务已被禁用，则不主动解除禁用状态。
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
    mode: 'daily',
    taskName: 'ZzzHe_小米钱包每日任务',
  })
  .catch((error) => {
    console.error(`❌ ZzzHe_小米钱包每日任务启动失败：${error.stack || error.message}`);
    process.exit(1);
  });
