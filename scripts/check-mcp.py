"""Проверка MCP-сервера 1С: initialize + tools/list.

Использование:
    python scripts/check-mcp.py [url]
"""

import json
import sys
import urllib.request

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:6003/mcp"


def post(payload: dict, sid: str | None) -> tuple[str, str | None]:
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), method="POST")
    req.add_header("content-type", "application/json")
    req.add_header("accept", "application/json, text/event-stream")
    if sid:
        req.add_header("mcp-session-id", sid)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace"), resp.headers.get("mcp-session-id")


def sse_json(body: str) -> dict:
    chunk = "\n".join(line[5:].lstrip() for line in body.splitlines() if line.startswith("data:"))
    return json.loads(chunk or body)


def main() -> int:
    try:
        body, sid = post({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "check-mcp", "version": "1"}},
        }, None)
        init = sse_json(body)["result"]
        post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
        body, _ = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, sid)
        tools = sse_json(body)["result"]["tools"]
    except Exception as exc:  # noqa: BLE001
        print(f"ОШИБКА: {exc}")
        return 1

    print(f"сервер: {init['serverInfo']['name']} {init['serverInfo']['version']}")
    print(f"протокол: {init['protocolVersion']}")
    print(f"инструментов: {len(tools)}")
    for tool in tools:
        print("  -", tool["name"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
