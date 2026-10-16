# Continuously improve your software with Scalpels and Solo

Companion code for the guide at
[scalpels.app/guides/continuously-improve-your-software](https://scalpels.app/guides/continuously-improve-your-software).
Read the guide first; this is the part you run.

| Path | What it is |
| --- | --- |
| `ring.py` | What cron runs every hour. Makes sure the Conductor is running in Solo, then rings it. |
| `improvement_loop/solo.py` | A small client for Solo's stdio MCP server. |
| `improvement_loop/standing.py` | Spawns, checks, recycles and rings a standing agent by role. |
| `orders/conductor.md` | The Conductor's standing orders. |
| `orders/sweep.md` | What to ask Hone and Wake, and what counts as a finding. Tune it. |
| `orders/investigations.md` | How findings are filed and investigators briefed. |
| `orders/ledger.md` | The starting content for the Improvement ledger scratchpad. |
| `orders/REMEDIATION.example.md` | A starting point for each repository's remediation rules. |
| `schedule/` | A crontab line and a launchd job. Use one. |

No dependencies beyond the Python 3 that ships with macOS, and Solo.

## Set up

1. Clone this branch onto the Mac that runs Solo, and copy the config:

   ```shell
   git clone --branch continuously-improve-your-software --single-branch \
     https://github.com/artisan-build/scalpels-guides.git ~/improvement-loop
   cd ~/improvement-loop
   cp config.example.json config.json
   ```

2. In `config.json`, set `solo_project` to the name of the Solo project that holds your apps'
   repositories, and `runtime` to the Solo agent tool the Conductor should run on.

3. Create the **Improvement ledger** scratchpad in that project from `orders/ledger.md`, tagged
   `improvement-loop`, and fill in the Apps table. Each tool is its own Scalpels deployment, so
   each needs its own `app_deployment` column; write `pending` in both cells for a tool you have
   not connected yet.

4. Put a `REMEDIATION.md` at the root of every repository the loop can reach, from
   `orders/REMEDIATION.example.md`. An investigator that finds none reports what it found and
   stops without changing anything.

5. Check that everything resolves, without starting anything:

   ```shell
   python3 ring.py --check
   ```

6. Ring it once by hand and watch the Conductor in Solo:

   ```shell
   python3 ring.py
   ```

7. Once a few runs look right, schedule it with `schedule/crontab.example` or the launchd job in
   `schedule/`.

A newly connected app has nothing useful to say for about an hour: Hone's aggregates are built by
an hourly rollup, and Wake shows zero rows until the app writes a log line. Wait one rollup before
the first ring, or the first sweep files a finding about the silence.

`state/ring.log` records every decision `ring.py` makes: spawned, rang, recycled, or skipped
because the Conductor was still busy.
