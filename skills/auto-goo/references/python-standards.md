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
ruff check .                    # lint 检查
ruff check . --fix              # 自动修复
python -m pytest -v             # 运行测试
python <脚本>.py                # 运行脚本
```

## 项目结构

```
项目根/
├── .goo/        # 自动生成（日志、plan、评测数据）
├── CLAUDE.md    # 项目专属指引
└── <实现文件>    # 由 Subagent 按需创建
```
