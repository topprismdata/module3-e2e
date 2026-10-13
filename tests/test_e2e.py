"""WP22 起步门禁：visit-plan 六态链 / 超载→工作台桥 / 规则绑定存在性。"""

from datetime import date

import pytest
from dq_workbench import Workbench
from dq_workbench.models import IssueStatus
from module3_e2e.bridge import rule_ref_published, violations_to_findings
from plan_release import IllegalTransition, PlanReleaseService
from service_rules import Rule, RuleSetVersion, RuleStore, RuleType, Severity
from visit_ir import ISO_WEEK_V1, AnchorBoundaryError, assert_horizon_safe
from visit_math_api import ValidationReport, Violation

VISIT_PLAN = {
    "doc_type": "visit-plan",
    "spec": {"horizon": "2026-11", "weekday_slots": [["C001", 0], ["C002", 1]]},
    "rule_set_ref": "rs-2026-11-v1",
    "capacity": {"reps": 4, "max_visits_per_rep_day": 12},
}


@pytest.fixture
def env(tmp_path):
    return {
        "plans": PlanReleaseService(":memory:"),
        "wb": Workbench(tmp_path / "w.db"),
        "rules": RuleStore(tmp_path / "r.db"),
    }


def test_g1_visit_plan六态全链可发布(env):
    plans = env["plans"]
    pv = plans.new_iteration("VP", VISIT_PLAN, actor="planner")
    plans.transition(pv.ref, "simulate", actor="analyst")
    plans.transition(pv.ref, "submit", actor="planner")
    plans.transition(pv.ref, "approve", actor="manager")
    act = plans.transition(pv.ref, "activate", actor="ops")
    assert plans.active("VP").ref == act.ref
    assert act.payload == VISIT_PLAN  # 冻结字节不变
    assert plans.verify_audit_chain()


def test_g2_visit_plan形状fail_fast(env):
    bad = {k: v for k, v in VISIT_PLAN.items() if k != "capacity"}
    with pytest.raises(IllegalTransition, match="capacity"):
        env["plans"].new_iteration("VP", bad, actor="planner")


def test_g3_超载违规桥入工作台(env):
    """L2 验解报告(C2 走廊超载) → Finding → ingest → 工单 OPEN。"""
    report = ValidationReport(
        ok=False,
        violations=(
            Violation("C2_CORRIDOR", "workload_corridor", "周三 14 店 > k_max=12"),
            Violation("C2_CORRIDOR", "workload_corridor", "周五 15 店 > k_max=12"),
        ),
    )
    findings = violations_to_findings(report, subject="VP#1")
    assert [f.subject for f in findings] == ["VP#1", "VP#1"]
    # 确定性排序：按 (constraint_id, detail)
    assert [f.message for f in findings] == sorted(
        f.message for f in findings
    )
    wb = env["wb"]
    ids = wb.ingest(findings)
    assert len(ids) == 2
    issue = wb.open_issue(ids, title="visit-plan 超载 VP#1")
    assert issue.status is IssueStatus.OPEN
    # 幂等：重复 ingest 不炸（INSERT OR REPLACE 语义）
    assert wb.ingest(findings) == ids


def test_g4_规则绑定存在性闸(env):
    store = env["rules"]
    assert not rule_ref_published(store, "rs-2026-11-v1")  # 未发布 → 闸关
    rs = RuleSetVersion(
        "rs-2026-11-v1",
        (
            Rule("R1", RuleType.VISIT_FREQUENCY, Severity.C2, False, visits_per_week=2),
            # 频次须配节拍槽位（F2 fail-closed——本测试发布时即被闸强制）
            Rule("R2", RuleType.CADENCE_SLOTS, Severity.C1, True,
                 weekday_slots={1: [0, 1], 3: [0]}),
        ),
    )
    store.publish(rs, activated_by="ops")
    assert rule_ref_published(store, "rs-2026-11-v1")  # 发布后 → 闸开
    assert not rule_ref_published(store, "rs-ghost")


def test_g5_三层import链与D2贯通(env):
    """七仓 pin 共存：L1 D2 假设注册表在集成环境可用。"""
    assert_horizon_safe([date(2026, 12, 21)], ISO_WEEK_V1)  # 不跨界放行
    with pytest.raises(AnchorBoundaryError):
        assert_horizon_safe([date(2026, 12, 28), date(2027, 1, 4)], ISO_WEEK_V1)
