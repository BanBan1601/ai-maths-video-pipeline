from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# QA thresholds
MIN_OBJECT_GAP_PX = 16
MIN_LINE_GAP_RATIO = 1.2
EDGE_PADDING_RATIO = 0.05
MAX_WORDS_ON_SCREEN = 25
MIN_FONT_SIZE_PT = 18


@dataclass
class LayoutIssue:
    issue_type: str
    object_id: str
    message: str
    severity: str = "warning"  # warning / error
    suggested_fix: str = ""


class LayoutGuard:
    def static_checks(self, scene_metrics: dict) -> list[LayoutIssue]:
        issues: list[LayoutIssue] = []
        objects = scene_metrics.get("objects", [])
        frame_w = scene_metrics.get("frame_width", 1080)
        frame_h = scene_metrics.get("frame_height", 1920)
        edge_pad = min(frame_w, frame_h) * EDGE_PADDING_RATIO

        for obj in objects:
            # Overlap check
            if obj.get("overlap", False):
                issues.append(
                    LayoutIssue(
                        "overlap",
                        obj["id"],
                        "Object overlaps another object",
                        severity="error",
                        suggested_fix="increase_buff",
                    )
                )
            # Density check
            if obj.get("too_dense", False):
                issues.append(
                    LayoutIssue(
                        "dense",
                        obj["id"],
                        "Object spacing is too compact",
                        severity="warning",
                        suggested_fix="increase_vertical_gap",
                    )
                )
            # Edge check
            bbox = obj.get("bbox")
            if bbox:
                x0, y0, x1, y1 = bbox
                if (
                    x0 < edge_pad
                    or y0 < edge_pad
                    or x1 > frame_w - edge_pad
                    or y1 > frame_h - edge_pad
                ):
                    issues.append(
                        LayoutIssue(
                            "edge_clip",
                            obj["id"],
                            f"Object too close to frame edge (pad={edge_pad:.0f}px)",
                            severity="warning",
                            suggested_fix="shift_inward",
                        )
                    )
            # Font size check
            font_size = obj.get("font_size")
            if font_size and font_size < MIN_FONT_SIZE_PT:
                issues.append(
                    LayoutIssue(
                        "small_font",
                        obj["id"],
                        f"Font size {font_size}pt is below minimum {MIN_FONT_SIZE_PT}pt",
                        severity="error",
                        suggested_fix="increase_font_size",
                    )
                )
            # Word count check
            word_count = obj.get("word_count")
            if word_count and word_count > MAX_WORDS_ON_SCREEN:
                issues.append(
                    LayoutIssue(
                        "text_overload",
                        obj["id"],
                        f"Too many words on screen ({word_count} > {MAX_WORDS_ON_SCREEN})",
                        severity="warning",
                        suggested_fix="split_scene_or_abbreviate",
                    )
                )
            # Caption zone check
            if obj.get("in_caption_zone", False):
                issues.append(
                    LayoutIssue(
                        "caption_overlap",
                        obj["id"],
                        "Object enters subtitle-safe bottom area",
                        severity="error",
                        suggested_fix="move_above_caption_zone",
                    )
                )
        return issues

    def repair_instructions(self, issues: list[LayoutIssue]) -> list[str]:
        fix_map = {
            "increase_buff": "Increase VGroup buff to at least 0.4 and reflow adjacent objects.",
            "increase_vertical_gap": "Add .arrange(DOWN, buff=0.5) or increase existing buff by 50%.",
            "shift_inward": "Apply keep_above_caption_zone() and fit_to_frame() helpers.",
            "increase_font_size": "Set minimum font size to 24pt; use auto_shrink_text() helper.",
            "split_scene_or_abbreviate": (
                "Split dense text into two scenes or shorten on-screen text while keeping narration."
            ),
            "move_above_caption_zone": (
                "Apply keep_above_caption_zone() helper to all bottom elements."
            ),
        }
        seen: set[str] = set()
        instructions: list[str] = []
        for issue in issues:
            fix = fix_map.get(
                issue.suggested_fix, f"Fix {issue.issue_type} on {issue.object_id}."
            )
            if fix not in seen:
                seen.add(fix)
                instructions.append(f"[{issue.severity.upper()}] {issue.message}: {fix}")
        return instructions

    def compute_scene_metrics(
        self, objects: list[dict], frame_width: int = 1080, frame_height: int = 1920
    ) -> dict:
        """Compute overlap metrics for a list of rendered objects with bounding boxes."""
        metrics: dict = {
            "overlap_count": 0,
            "min_gap": float("inf"),
            "edge_violations": 0,
        }
        bboxes = [(o["id"], o.get("bbox", [])) for o in objects if o.get("bbox")]
        for i in range(len(bboxes)):
            for j in range(i + 1, len(bboxes)):
                id1, b1 = bboxes[i]
                id2, b2 = bboxes[j]
                if len(b1) == 4 and len(b2) == 4:
                    iou = self._compute_iou(b1, b2)
                    if iou > 0.01:
                        metrics["overlap_count"] += 1
                    gap = self._compute_gap(b1, b2)
                    metrics["min_gap"] = min(metrics["min_gap"], gap)
        # Replace infinity with None for JSON serialisation
        if metrics["min_gap"] == float("inf"):
            metrics["min_gap"] = None
        return metrics

    def _compute_iou(self, b1: list, b2: list) -> float:
        x0 = max(b1[0], b2[0])
        y0 = max(b1[1], b2[1])
        x1 = min(b1[2], b2[2])
        y1 = min(b1[3], b2[3])
        inter = max(0, x1 - x0) * max(0, y1 - y0)
        if inter == 0:
            return 0.0
        area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
        area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
        return inter / (area1 + area2 - inter)

    def _compute_gap(self, b1: list, b2: list) -> float:
        dx = max(0, max(b1[0], b2[0]) - min(b1[2], b2[2]))
        dy = max(0, max(b1[1], b2[1]) - min(b1[3], b2[3]))
        return (dx**2 + dy**2) ** 0.5


class QAService:
    def __init__(self):
        self.layout_guard = LayoutGuard()

    def run_render_qa(self, scene_metrics: dict) -> dict:
        issues = self.layout_guard.static_checks(scene_metrics)
        repair_actions = self.layout_guard.repair_instructions(issues)
        passed = not any(i.severity == "error" for i in issues)
        return {
            "passed": passed,
            "issues": [
                {
                    "type": i.issue_type,
                    "object_id": i.object_id,
                    "message": i.message,
                    "severity": i.severity,
                }
                for i in issues
            ],
            "repair_actions": repair_actions,
            "metrics": self.layout_guard.compute_scene_metrics(
                scene_metrics.get("objects", [])
            ),
        }
