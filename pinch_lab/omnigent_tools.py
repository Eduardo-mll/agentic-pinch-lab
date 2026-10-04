"""Compatibility import. Canonical module: pinch_lab.tools.omnigent_tools."""

from pinch_lab.tools.omnigent_tools import (
    tool_gather_evidence,
    tool_run_discovery_loop,
    tool_run_experiment,
    tool_validate_evidence_ids,
)

__all__ = [
    "tool_gather_evidence",
    "tool_validate_evidence_ids",
    "tool_run_experiment",
    "tool_run_discovery_loop",
]
