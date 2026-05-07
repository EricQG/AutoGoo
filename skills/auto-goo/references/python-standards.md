# Python 技术规范

## 代码风格

- Python 3.10+，类型注解必须完整
- 函数/方法必须有 type hints（返回值 + 参数）
- 使用 `ruff` 做 lint（默认配置 + line-length=100）
- 注释原则：只写 WHY，不写 WHAT
- 文件名：小写+下划线
- 优先使用标准库，外部依赖需在 plan.json 中声明 `[dep: <包名>]`
- 不 scope creep：不添加任务描述中未要求的功能或参数

### 常用命令

```bash
ruff check src/                    # lint 检查
ruff check src/ --fix              # 自动修复
python -m pytest tests/ -v        # 运行测试
python src/<模块>/<脚本>.py        # 运行脚本
```

## 项目结构

```
项目根/
├── CLAUDE.md
├── .goo/        # 自动生成（日志、plan、评测数据）
├── src/         # 实现代码
├── tests/       # 测试代码
```

## 核心接口约定

```python
# src/orchestrator/scheduler.py — DAG 调度
def build_schedule(steps: list[StepDef]) -> list[RoundGroup]: ...
def schedule_from_plan(plan: dict) -> list[RoundGroup]: ...

# src/orchestrator/engine.py — 执行引擎
class Engine:
    def __init__(self, plan: dict) -> None: ...
    async def run_round(self, steps: list[dict], context: dict) -> list[StepResult]: ...
    def get_context_for(self, step: dict) -> dict: ...
    def write_log(self, step: dict, result: StepResult) -> Path: ...
    def summary(self) -> str: ...

# 步骤结果
class StepResult:
    step_id: int
    step_name: str
    status: str         # "ok" | "failed"
    elapsed_s: float
    error: str | None
```
