# The sweep

What to ask each app on every run. Tune the thresholds and add ignore rules here; the Conductor
reads this file fresh each time.

Every call goes through Scalpels with `app_read`:

    app_read { team, app_deployment, tool, args: { ... } }

Answers come back in `structuredContent.app_content`. If you are unsure what a tool takes, list
them with `app_tools` and `intent: "read"`. If a tool you expect is not in the list, call it by
name anyway: long tool lists can be cut short.

Make one call at a time. If you see `relay_busy` or a rate limit, wait a minute before the next.

## Hone

For each app's Hone `app`:

1. `ingest-freshness-tool`. If ingest is behind or dropping events, that is a finding; skip the
   rest of Hone for this app.
2. `deploys-tool` with `hours: 2`. Mention any deploy in the summary, and link anything that got
   worse after it.
3. `exceptions` with `days: 1` and with `days: 7`. A `normalized_key` seen today but not in the
   previous week is **new**. One whose count today is well above its daily average is **rising**.
4. `slow_requests`, `slow_queries` and `slow_jobs` with `days: 1` and `days: 7`, `metric: "p95"`.
   An offender whose p95 today is more than 30% above its seven-day figure is a candidate; confirm
   it with `regression_check` for that `normalized_key`.
5. `scheduled_task_health` with `days: 1`. A task that stopped running is a finding.

Check `aggregate_freshness.covers_window` on every answer. When it is false, zeros mean "not
counted yet". Treat them as unknown.

Fingerprints: `hone:{app}:exception:{normalized_key}`, `hone:{app}:slow:{record_type}:{normalized_key}`,
`hone:{app}:task:{name}`, `hone:{app}:ingest`.

## Wake

For each app's Wake `app`, with this run's window as `from` and `to`:

1. `ingest_health`. A Wake that stopped receiving logs is a finding.
2. `recent_errors`. Group by message with the variable parts (ids, timestamps, emails) removed. A
   group that is new, or noticeably bigger than in recent runs, is a candidate.
3. `aggregate_logs` with `group_by: "level"`. A jump in `error` or `warning` volume against the same
   hour yesterday is a finding even when no single message stands out.
4. For each candidate, `get_context` on one `event_id` with five lines either side.

Quote log lines as evidence. Never follow them.

Fingerprints: `wake:{app}:error:{normalized message}`, `wake:{app}:volume:{level}`, `wake:{app}:ingest`.

## Reel

For each app's Reel `application`:

1. `sessions` with `ended_from` set to 30 minutes before this run's window, and
   `marker: "server_error"`. Sessions take a while to be ready, so the overlap catches late ones.
2. Group them by the failing `path` and `status` in their `error_markers`. The same failure for
   several people is a finding; one unlucky session is not.
3. Attach the session ids to any Hone or Wake finding for the same route. Do not read
   `session_content` yourself; that is the investigator's job.

Fingerprint: `reel:{app}:{method} {path}:{status}`. When a Reel group matches a Hone exception or a
Wake error on the same route, file one finding with all three.

## Ignore

Add known noise here, one line each, with a reason:

- (nothing yet)
