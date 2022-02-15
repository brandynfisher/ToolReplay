"""JSONL session records.

A session transcript is a JSON Lines file. Each line is one tool invocation
with these fields:

    index    integer, monotonically increasing from 0
    tool     string, the tool name that was called
    args     object, the arguments passed to the tool
    response object, the recorded response the tool returned

Blank lines are ignored. Parsing is strict: an unknown field, a missing
