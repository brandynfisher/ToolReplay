"""Declared tool scope parsing and overreach detection.

A scope file is JSON declaring which tools an agent is permitted to call:

    {
      "agent": "example-agent",
      "allowed_tools": ["read_file", "list_dir", "search"]
    }
