"""A minimal client for Solo's stdio MCP server, for scripts that run outside Solo.

Solo ships its MCP server as a binary inside the app. A script starts it, speaks JSON-RPC over
stdin and stdout, and identifies itself as an external actor so Solo can tell it apart from the
agents it runs.
"""
import json
import subprocess

SOLO_MCP = "/Applications/Solo.app/Contents/MacOS/mcp"


class SoloError(RuntimeError):
    pass


class Solo:
    def __init__(self, actor="improvement-loop", binary=SOLO_MCP):
        self.proc = subprocess.Popen([binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True)
        self.next_id = 0
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": actor, "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.call("identify_session", external={"name": actor, "agent_id": actor})

    def _send(self, message):
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def _rpc(self, method, params):
        self.next_id += 1
        self._send({"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params})
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise SoloError("Solo's MCP server closed the pipe during %s. Is Solo running?" % method)
            message = json.loads(line)
            if message.get("id") == self.next_id:
                if "error" in message:
                    raise SoloError("%s: %s" % (method, message["error"].get("message")))
                return message["result"]

    def call(self, tool, **arguments):
        """Call one Solo tool and return its result, parsed as JSON when it is JSON."""
        result = self._rpc("tools/call", {"name": tool, "arguments": arguments})
        text = "".join(part.get("text", "") for part in result.get("content", []))
        if result.get("isError"):
            raise SoloError("%s: %s" % (tool, text[:300]))
        try:
            return json.loads(text)
        except ValueError:
            return text

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
