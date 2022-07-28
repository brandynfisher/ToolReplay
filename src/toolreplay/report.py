"""Line-oriented report rendering.

Output is deterministic and diff-friendly: one finding per line, a fixed header,
and a summary count. No timestamps, no randomness.
"""

from toolreplay.findings import Finding, sort_findings

