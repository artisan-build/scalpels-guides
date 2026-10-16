"""Standing agents: long-lived Solo agents that a script outside Solo can ring.

A standing agent is known by its role, never by a fixed process id. Solo assigns a new id every
time an agent starts, so the live id is kept in a small state file. Every caller goes through
ensure(), which checks that the recorded agent is still running, spawns and briefs a fresh one
when it is not, and recycles one that has been idle long enough to have built up a heavy context.
"""
import datetime
import json
import os
import re
import time


class Registry:
    """The state file that maps each role to the Solo process currently holding it."""

    def __init__(self, path):
        self.path = path

    def load(self):
        try:
            with open(self.path) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def get(self, role):
        return self.load().get(role)

    def put(self, role, record):
        data = self.load()
        data[role] = record
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=1, sort_keys=True)
            f.write("\n")
        os.replace(tmp, self.path)


def agent_status(solo, process_id, project_id):
    """The status of a running agent, or None if the process is gone, stopped or not an agent."""
    try:
        status = solo.call("get_process_status", process_id=process_id, project_id=project_id)
    except RuntimeError:
        return None
    if not isinstance(status, dict) or status.get("kind") != "agent" or status.get("status") != "Running":
        return None
    return status


def is_idle(status):
    return bool((status.get("agent_state") or {}).get("idle"))


def agent_tool_id(solo, runtime):
    """The id of the Solo agent tool matching the configured runtime, looked up fresh every time."""
    for tool in solo.call("list_agent_tools"):
        if tool.get("name") == runtime["name"] and tool.get("tool_type") == runtime["tool_type"] \
                and tool.get("enabled", True):
            return tool["id"]
    raise RuntimeError("Solo has no enabled agent tool named %s (%s)" % (runtime["name"], runtime["tool_type"]))


def wait_until_ready(solo, process_id, project_id, timeout=120):
    """Wait for a freshly spawned agent to show its input prompt, accepting a folder-trust question.

    The patterns below match Claude Code and Codex. Another runtime may need its own.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        output = solo.call("get_process_output", process_id=process_id, project_id=project_id, lines=30)
        text = output.get("output", output.get("text", "")) if isinstance(output, dict) else str(output)
        if re.search(r"(trust this folder|Quick safety check)", text, re.I):
            solo.call("send_input", process_id=process_id, project_id=project_id, bytes=[27, 91, 66])
            solo.call("send_input", process_id=process_id, project_id=project_id, bytes=[13])
        elif re.search(r"^\s*[│|]?\s*[❯›>]\s*$", text, re.M) or "? for shortcuts" in text:
            return True
        time.sleep(3)
    return False


def ring(solo, process_id, project_id, text, attempts=4):
    """Send a short message, then keep pressing Enter until the agent is actually working on it.

    A freshly started agent can show its prompt before it accepts input, so an Enter sent too early
    leaves the message sitting in the input box and the agent idle. After each Enter, wait and check:
    once the agent stops being idle, the message was taken.

    Keep the text short: Solo clips long input from the front. Put anything long in a file and
    tell the agent where it is.
    """
    solo.call("send_input", process_id=process_id, project_id=project_id, input=text, wait_ms=1500)
    for _ in range(attempts):
        solo.call("send_input", process_id=process_id, project_id=project_id, bytes=[13])
        time.sleep(5)
        status = agent_status(solo, process_id, project_id)
        if status is None or not is_idle(status):
            return True
    return False


def ensure(solo, registry, role, project_id, runtime, brief, max_idle_age_s=None, log=print):
    """Return (process_id, status, fresh) for a live agent holding the role, spawning one if needed."""
    record = registry.get(role)
    if record:
        status = agent_status(solo, record["process_id"], project_id)
        if status is None:
            log("%s: agent %s is gone, spawning a new one" % (role, record["process_id"]))
        elif max_idle_age_s and is_idle(status) and status.get("uptime_seconds", 0) > max_idle_age_s:
            log("%s: recycling agent %s after %ss" % (role, record["process_id"], status["uptime_seconds"]))
            solo.call("close_process", process_id=record["process_id"], project_id=project_id)
        else:
            return record["process_id"], status, False

    spawned = solo.call("spawn_agent", agent_tool_id=agent_tool_id(solo, runtime), project_id=project_id,
                        name=role, extra_args=runtime.get("extra_args", []))
    process_id = int(spawned["process_id"]) if isinstance(spawned, dict) \
        else int(re.search(r"process_id\W+(\d+)", spawned).group(1))
    registry.put(role, {"process_id": process_id, "project_id": project_id,
                        "spawned_at": datetime.datetime.now().isoformat(timespec="seconds")})
    log("%s: spawned agent %s" % (role, process_id))

    if not wait_until_ready(solo, process_id, project_id):
        log("%s: agent %s never showed a prompt, briefing it anyway" % (role, process_id))
    if not ring(solo, process_id, project_id, brief):
        log("%s: agent %s never started on its brief; check it in Solo" % (role, process_id))
    return process_id, agent_status(solo, process_id, project_id), True
