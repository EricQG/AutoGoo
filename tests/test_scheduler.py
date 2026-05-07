"""测试 DAG 调度器 — build_schedule / validate_dag。"""

from src.orchestrator.scheduler import StepDef, build_schedule, validate_dag


def test_empty_deps_run_first() -> None:
    """depends_on 为空的步骤应该在第一轮执行。"""
    steps = [
        StepDef(1, "A", [], "exec"),
        StepDef(2, "B", [1], "exec"),
    ]
    schedule = build_schedule(steps)
    assert len(schedule) == 2
    assert [s.id for s in schedule[0].steps] == [1]
    assert [s.id for s in schedule[1].steps] == [2]


def test_parallel_steps_in_same_round() -> None:
    """相同前驱的步骤应在同一轮并行。"""
    steps = [
        StepDef(1, "A", [], "exec"),
        StepDef(2, "B1", [1], "exec"),
        StepDef(3, "B2", [1], "exec"),
    ]
    schedule = build_schedule(steps)
    assert len(schedule) == 2
    assert sorted(s.id for s in schedule[1].steps) == [2, 3]


def test_multi_layer_dag() -> None:
    """3 层 DAG：A → B1+B2(并行) → C。"""
    steps = [
        StepDef(1, "A", [], "exec"),
        StepDef(2, "B1", [1], "exec"),
        StepDef(3, "B2", [1], "exec"),
        StepDef(4, "C", [2, 3], "exec"),
    ]
    schedule = build_schedule(steps)
    assert len(schedule) == 3
    assert [s.id for s in schedule[0].steps] == [1]
    assert sorted(s.id for s in schedule[1].steps) == [2, 3]
    assert [s.id for s in schedule[2].steps] == [4]


def test_independent_steps() -> None:
    """互不依赖的步骤全在第一轮并行。"""
    steps = [
        StepDef(1, "A", [], "exec"),
        StepDef(2, "B", [], "exec"),
        StepDef(3, "C", [], "exec"),
    ]
    schedule = build_schedule(steps)
    assert len(schedule) == 1
    assert sorted(s.id for s in schedule[0].steps) == [1, 2, 3]


def test_chain_dependency() -> None:
    """链式依赖：A → B → C → D，应生成 4 轮。"""
    steps = [
        StepDef(1, "A", [], "exec"),
        StepDef(2, "B", [1], "exec"),
        StepDef(3, "C", [2], "exec"),
        StepDef(4, "D", [3], "exec"),
    ]
    schedule = build_schedule(steps)
    assert len(schedule) == 4
    for i, s in enumerate(schedule):
        assert len(s.steps) == 1
        assert s.steps[0].id == i + 1


def test_circular_dependency_raises() -> None:
    """循环依赖应抛出 ValueError。"""
    steps = [
        StepDef(1, "A", [2], "exec"),
        StepDef(2, "B", [1], "exec"),
    ]
    try:
        build_schedule(steps)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_validate_dag_missing_dep() -> None:
    """validate_dag 应检出缺失的依赖。"""
    steps = [
        StepDef(1, "A", [99], "exec"),  # 99 不存在
    ]
    warnings = validate_dag(steps)
    assert len(warnings) == 1
    assert "99" in warnings[0]
    assert "non-existent" in warnings[0]


def test_from_dict() -> None:
    """StepDef.from_dict 应正确解析字典。"""
    d = {"id": 1, "name": "test", "depends_on": [], "type": "exec", "description": "hello"}
    s = StepDef.from_dict(d)
    assert s.id == 1
    assert s.name == "test"
    assert s.description == "hello"
    assert s.type == "exec"
