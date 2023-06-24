"""Line-oriented report rendering.

Output is deterministic and diff-friendly: one finding per line, a fixed header,
and a summary count. No timestamps, no randomness.
"""

from toolreplay.findings import Finding, sort_findings


def render_report(findings: list[Finding], divergence_index: int | None, call_count: int) -> str:
    """Render the audit report as line-oriented text."""
    ordered = sort_findings(findings)
    lines = []
    lines.append(f"calls: {call_count}")
    if divergence_index is None:
        lines.append("divergence: none")
    else:
        lines.append(f"divergence: index {divergence_index}")
    lines.append(f"findings: {len(ordered)}")
    for finding in ordered:
        lines.append(finding.line())
    return "\n".join(lines) + "\n"


def render_scope_report(findings: list[Finding], call_count: int) -> str:
    """Render just the scope overreach findings."""
    ordered = sort_findings(findings)
    lines = []
    lines.append(f"calls: {call_count}")
    lines.append(f"findings: {len(ordered)}")
    for finding in ordered:
        lines.append(finding.line())
    return "\n".join(lines) + "\n"


def render_verify_report(ok: bool, broken_index, expected, found) -> str:
    """Render the chain verification result."""
    if ok:
        return "chain: intact\n"
    lines = [
        "chain: broken",
        f"first broken link: index {broken_index}",
        f"expected: {expected}",
        f"found: {found}",
    ]
    return "\n".join(lines) + "\n"
