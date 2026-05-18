---
name: auto-goo:goo-status
description: 显示当前 AutoGoo 任务执行进度 — 读取 .goo/plan.json 渲染简洁仪表盘
---

# /auto-goo:goo-status — 执行仪表盘

以 plan.json 为数据源，渲染简洁终端仪表盘。**少字，多看。**

必须优先运行插件脚本，而不是手写临时渲染逻辑：

```bash
SCRIPT="skills/auto-goo/scripts/goo-status.py"
if [ ! -f "$SCRIPT" ]; then
  SCRIPT="$(find "${AUTO_GOO_PLUGIN_DIR:-$HOME}" -path '*/skills/auto-goo/scripts/goo-status.py' -print -quit)"
fi
test -n "$SCRIPT" && python3 "$SCRIPT" --plan .goo/plan.json
```

如果 `.goo/plan.json` 中的 running step 没有更新 `heartbeat_at` 或 `progress`，必须显示告警；不要假装仍在正常执行。

## 信息密度原则

- 已完成步骤：一行一个，只放关键信息
- 执行中步骤：进度条 + 一句话状态
- 告警：只在有问题时才出现
- 不展示无信息量的空面板

## 布局

```
══════════════════════════════════════════════════════════════
  {task}    {completed}/{total}  ████████░░  86%
══════════════════════════════════════════════════════════════

▶ 执行中 (2)
  gen_p6.py         ██████████░░░░  38%   ~150行  剩余 3min
  gen_p5.py         ████░░░░░░░░░░  22%   ~100行  剩余 5min

⏳ 待执行 (2)
  update_viewer.py  就绪
  小批量验证         等待 gen_p6 gen_p5

✅ 已完成 (10)
  schemas.py  722行  bbox_utils.py  304行  constraints.py  260行
  annotation.py  492行  gen_p1.py  885行  gen_p2.py  755行
  gen_p3.py  722行  gen_p4.py  1415行  gen_p6.py  1471行
  gen_p5.py  1273行  validate_qa.py  436行  ...

⚠️ gen_p5 progress 停滞 3 轮，可能卡住
```

## 面板规则

### 顶部横幅

一行：`══════  {task}  {n}/{total}  {进度条}  {百分比}  ══════`

进度条 20 字符宽，已填充用 `█`，剩余用 `░`。

右侧附加信息（可选）：
- 有 running agent → `· 槽位 {running}/{max_concurrent}`
- 全部完成 → `· 10,018 行`

### 执行中面板

只展示 status=running 的步骤，无则跳过此面板。

每行：`{name}  {进度条 16 字符}  {progress}%  {产物预览}  剩余 {预估}`

进度条宽 16 字符（`█` 填充 + `>` 当前位置 + `░` 剩余），百分比右对齐 3 字符。

产物预览：output 文件存在就显示行数，不存在显示 `...`

### 待执行面板

只展示 status=pending 的步骤，无则跳过。

每行：`{name}  {状态词}`
- 依赖全满足 → `就绪`
- 有未完成依赖 → `等待 {缺失依赖名，最多两个}` 超过两个加 `+{n}`

### 已完成面板

status=completed 的步骤，紧凑横排，多个用 `·` 分隔。每步：`{name} {产物行数}行`。超过 8 个时只展示最近完成的，其余省略为 `... 等 {n} 步`。

### 告警面板

只在有 failed / zombie / stuck 时显示，一行一条：

```
⚠️ {name} {原因}
```

原因映射：
- zombie → `无心跳 {n}min，已死`
- stuck → `进度停滞 {n}min`
- failed → `失败，原因: {日志摘要}`
- completed 但产物缺失 → `产物 {path} 不存在`

## 示例

```
/auto-goo:goo-status
```

输出：

```
══════════════════════════════════════════════════════════════
  v4 QA 生成系统重写  12/14  ████████████████░░  86%
══════════════════════════════════════════════════════════════

▶ gen_p6.py          ██████░░░░░░░░░░  38%  150行  剩余 ~3min
▶ gen_p5.py          ████░░░░░░░░░░░░  22%  100行  剩余 ~5min

⏳ update_viewer.py  就绪
⏳ 小批量验证         等待 gen_p6 gen_p5

✅ schemas.py 722行 · bbox_utils.py 304行 · constraints.py 260行
✅ annotation.py 492行 · gen_p1.py 885行 · gen_p2.py 755行
✅ gen_p3.py 722行 · gen_p4.py 1415行 · ... 等 3 步
```
