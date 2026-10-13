"""L2 验解报告 → ①dq-workbench 异常工单的桥（#26 超载告警接线）。

依赖方向纪律：桥只存在于集成层——visitmodel/plan-release 均不 import
dq-workbench（下层不知上层）。severity 统一 C2（超载=需人裁决，非阻断
发布；阻断语义由 plan-release 状态机承担）。
"""
from __future__ import annotations

from dq_workbench.models import Finding, Layer, Severity
from visit_math_api import ValidationReport


def violations_to_findings(
    report: ValidationReport,
    *,
    subject: str = "visit-plan",
) -> list[Finding]:
    """违规 → Finding：确定性排序 (constraint_id, detail)，evidence 携带语义追溯。"""
    findings: list[Finding] = []
    ordered = sorted(report.violations, key=lambda v: (v.constraint_id, v.detail))
    for i, v in enumerate(ordered):
        findings.append(
            Finding(
                finding_id=f"VISPLAN:{subject}:{v.constraint_id}:{i}",
                layer=Layer.STATISTICAL,
                rule_id=v.constraint_id,
                subject=subject,
                severity=Severity.C2,
                message=v.detail,
                evidence=[v.semantic_rule_id],
            )
        )
    return findings


def rule_ref_published(store, rule_set_ref: str) -> bool:
    """#22-24 绑定存在性闸：方案引用的规则集版本必须已发布。"""
    try:
        return store.get_version(rule_set_ref) is not None
    except Exception:
        return False
