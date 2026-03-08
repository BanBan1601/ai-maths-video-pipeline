from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LayoutIssue:
    issue_type: str
    object_id: str
    message: str


class LayoutGuard:
    def static_checks(self, scene_metrics: dict) -> list[LayoutIssue]:
        issues: list[LayoutIssue] = []
        for obj in scene_metrics.get("objects", []):
            if obj.get("overlap", False):
                issues.append(LayoutIssue("overlap", obj["id"], "Object overlaps another object"))
            if obj.get("too_dense", False):
                issues.append(LayoutIssue("dense", obj["id"], "Object spacing is too compact"))
        return issues

    def repair_instructions(self, issues: list[LayoutIssue]) -> list[str]:
        instructions: list[str] = []
        for issue in issues:
            if issue.issue_type == "overlap":
                instructions.append(f"Increase buffer around {issue.object_id} and reflow nearby group.")
            elif issue.issue_type == "dense":
                instructions.append(f"Increase vertical spacing around {issue.object_id} by 15%.")
        return instructions
