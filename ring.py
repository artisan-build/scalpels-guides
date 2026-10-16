#!/usr/bin/env python3
"""Ring the conductor: the one thing cron runs every hour.

It makes sure a standing conductor agent is running in Solo (spawning and briefing one if not),
then asks it to run the improvement loop. If the conductor is still busy with the last run, it
leaves it alone. Every decision is logged to state/ring.log.

    python3 ring.py              ring the conductor
    python3 ring.py --check      show what would happen, without spawning or ringing anything
"""
import argparse
import datetime
import fcntl
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from improvement_loop.solo import Solo, SoloError
from improvement_loop.standing import Registry, agent_tool_id, ensure, is_idle, ring

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
ROLE = "Conductor"
RUN = "Run the improvement loop. Read the Improvement ledger first."


def log(message):
    line = "%s %s" % (datetime.datetime.now().isoformat(timespec="seconds"), message)
    print(line)
    with open(os.path.join(STATE, "ring.log"), "a") as f:
        f.write(line + "\n")


def project_id(solo, name):
    for project in solo.call("list_projects"):
        if name in (project.get("name"), project.get("display_name")):
            return project["id"]
    raise SystemExit("Solo has no project named %r. Check solo_project in config.json." % name)


def brief():
    orders = os.path.join(HERE, "orders", "conductor.md")
    return ("You are the %s for the improvement loop. Read your standing orders in %s and follow them "
            "from now on. Then run the improvement loop once." % (ROLE, orders))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report what would happen and change nothing")
    args = parser.parse_args()

    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(HERE, "config.json")) as f:
        config = json.load(f)

    lock = open(os.path.join(STATE, "ring.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("another ring.py is still running; skipping")
        return 0

    try:
        with Solo(actor="improvement-loop") as solo:
            pid = project_id(solo, config["solo_project"])
            registry = Registry(os.path.join(STATE, "standing-agents.json"))

            if args.check:
                tool = agent_tool_id(solo, config["runtime"])
                record = registry.get(ROLE)
                log("check: project %s, agent tool %s, recorded %s %s"
                    % (pid, tool, ROLE, record["process_id"] if record else "none"))
                return 0

            process_id, status, fresh = ensure(
                solo, registry, ROLE, pid, config["runtime"], brief(),
                max_idle_age_s=config.get("recycle_after_hours", 24) * 3600, log=log)

            if fresh:
                log("briefed new %s %s, which runs the loop as its first task" % (ROLE, process_id))
            elif status and not is_idle(status):
                log("%s %s is still busy; not ringing this hour" % (ROLE, process_id))
            else:
                if ring(solo, process_id, pid, RUN):
                    log("rang %s %s" % (ROLE, process_id))
                else:
                    log("rang %s %s, but it never started working; check it in Solo" % (ROLE, process_id))
    except SoloError as error:
        log("could not reach Solo: %s" % error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
