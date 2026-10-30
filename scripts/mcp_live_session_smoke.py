"""Temporary interactive smoke harness for the agent-controlled MCP browser."""

import asyncio
import json
import sys

from blindspot.mcp.server import create_mcp_server


server = create_mcp_server()


async def invoke(name: str, arguments: dict) -> None:
    result = await server.call_tool(name, arguments)
    text_blocks = [block.text for block in result.content if getattr(block, "type", None) == "text"]
    image_count = sum(1 for block in result.content if getattr(block, "type", None) == "image")
    payload = json.loads(text_blocks[0]) if text_blocks and text_blocks[0].startswith("{") else {"text": text_blocks}
    if name in ("live_browser_open", "live_browser_observe", "live_browser_action"):
        payload = {key: payload.get(key) for key in ("session_id", "url", "title", "page_text", "controls", "screenshot_path", "output_dir", "action", "next_step")}
    print(json.dumps({"tool": name, "result": payload, "images_returned_to_agent": image_count}, ensure_ascii=False), flush=True)


async def main() -> None:
    print("Send one JSON object per line with `tool` and `arguments`; type `quit` to exit.", flush=True)
    while True:
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line or line.strip().lower() == "quit":
            return
        try:
            request = json.loads(line)
            await invoke(request["tool"], request.get("arguments", {}))
        except Exception as exc:
            print(json.dumps({"error": str(exc)}), flush=True)


asyncio.run(main())
