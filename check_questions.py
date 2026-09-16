"""Guard the question set.

Structural checks (exercises.py vs QUESTIONS.md):
  * every exercise has a ledger id that exists in the ledger, plus a concept,
    a trap_sql and a note
  * no ledger id or title is used twice
  * every ledger row marked "ex N" points at an exercise that exists
  * ledger ids are unique and contiguous
  * any top-N question taking more than one row carries an ORDER BY tiebreak,
    since a tie at the boundary would otherwise make the answer ambiguous

Behavioural checks (against testdb.db, read-only):
  * every solution runs and returns at least one row
  * every trap_sql is graded WRONG -- a trap the grader accepts is a question
    that teaches nothing, and this is what catches it
  * every exercise carrying plan_requires/plan_forbids has a solution whose
    own EXPLAIN QUERY PLAN satisfies them, and a trap that violates them --
    efficiency questions return identical rows either way, so the plan is the
    only thing that can distinguish right from wrong
  * every claim a prompt makes about the data actually holds -- stated ranges,
    row counts, "these rows appear with 0". trap_sql proves a query wrong; only
    this catches a prompt that describes data the database does not contain
  * every writable (kind="script") question's reference script runs in a
    sandbox, changes the state its probe_sql reads, and its trap leaves a
    state the probe can tell apart

    py check_questions.py
"""

import re
import sqlite3
import textwrap
import sys
from pathlib import Path

import db
import exercises as ex

LEDGER = Path(__file__).resolve().parent / "QUESTIONS.md"
ROW = re.compile(r"^\|\s*(Q\d{3})\s*\|(.*?)\|(.*?)\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")
TRAILING_LIMIT = re.compile(r"\bLIMIT\s+(\d+)\s*$", re.IGNORECASE)
ORDER_BY = re.compile(r"\bORDER\s+BY\b(.*?)\s+LIMIT\b", re.IGNORECASE | re.DOTALL)


def parse_ledger():
    """Return {id: {'gui': ...}} from every markdown table in the file."""
    rows = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m:
            qid, _concept, _question, gui, _rest = m.groups()
            rows[qid] = {"gui": gui.strip()}
    return rows


def run(conn, sql):
    """(rows, error). A trap that errors counts as rejected, not as a pass.

    Time-limited: an authoring slip in a recursive step would otherwise hang
    the checker instead of reporting a broken question.
    """
    try:
        with db.time_limit(conn):
            return db.fetch_capped(conn.execute(sql)), None
    except (db.QueryTimeout, db.TooManyRows) as exc:
        return None, str(exc)
    except sqlite3.Error as exc:
        return None, str(exc)


def main():
    problems = []
    ledger = parse_ledger()
    if not ledger:
        print("could not parse any rows out of QUESTIONS.md")
        return 1

    nums = sorted(int(q[1:]) for q in ledger)
    if nums != list(range(1, len(nums) + 1)):
        problems.append(f"ledger ids are not contiguous from Q001: {nums[:3]}...{nums[-3:]}")

    seen_ids, seen_titles = {}, {}
    for e in ex.EXERCISES:
        qid = e.get("ledger")
        if not qid:
            problems.append(f"exercise {e['id']} ({e['title']}) has no ledger id")
        else:
            if qid not in ledger:
                problems.append(f"exercise {e['id']} points at {qid}, not in the ledger")
            if qid in seen_ids:
                problems.append(f"{qid} claimed by exercises {seen_ids[qid]} and {e['id']}")
            seen_ids[qid] = e["id"]
        # The GUI panel caps at QUESTION_MAX_LINES; a prompt past that would
        # have its tail hidden, and the tail is the "Return:" line.
        wrapped = sum(max(1, len(textwrap.wrap(line, 76)))
                      for line in e["prompt"].split("\n"))
        if wrapped > 14:
            problems.append(
                f"exercise {e['id']} prompt is {wrapped} lines wrapped at 76 cols; "
                f"the GUI panel would hide the tail, including the Return: line")
        # A query prompt ends by naming the columns to Return; a script prompt
        # ends by saying what the probe Checks, since it returns nothing.
        tail = "Checked:" if ex.is_script(e) else "Return:"
        if tail not in e["prompt"]:
            problems.append(f"exercise {e['id']} prompt never says {tail[:-1]}")

        for field in ("concept", "trap_sql", "note"):
            if not e.get(field):
                problems.append(f"exercise {e['id']} has no {field}")

        key = e["title"].strip().lower()
        if key in seen_titles:
            problems.append(f"duplicate title {e['title']!r} on {seen_titles[key]} and {e['id']}")
        seen_titles[key] = e["id"]

    # A top-N question ordered by a single key is ambiguous the moment two rows
    # tie at the cut-off: the engine may return either, so there is no one right
    # answer to grade against. LIMIT 1 is exempt -- verify those by hand.
    for e in ex.EXERCISES:
        sql = " ".join(e["solution"].split())
        m = TRAILING_LIMIT.search(sql)
        if not m or int(m.group(1)) <= 1:
            continue
        clause = ORDER_BY.search(sql)
        if not clause or "," not in clause.group(1):
            problems.append(
                f"exercise {e['id']} takes LIMIT {m.group(1)} with a single ORDER BY key; "
                f"a tie at the boundary would make the answer ambiguous")

    by_ex = {e["id"]: e.get("ledger") for e in ex.EXERCISES}
    for qid, row in ledger.items():
        m = re.fullmatch(r"ex\s*(\d+)", row["gui"])
        if not m:
            continue
        eid = int(m.group(1))
        if eid not in by_ex:
            problems.append(f"{qid} claims exercise {eid}, which does not exist")
        elif by_ex[eid] != qid:
            problems.append(f"{qid} claims exercise {eid}, but it points at {by_ex[eid]}")

    # --- behavioural ------------------------------------------------------
    conn = sqlite3.connect(f"file:{db.DB_PATH}?mode=ro", uri=True)
    traps_by_error = traps_by_result = claims_checked = 0
    traps_by_plan = plans_checked = starters_checked = flat_checked = 0
    scripts_checked = 0
    try:
        for e in ex.EXERCISES:
            if ex.is_script(e):
                # A writable question is graded on the database AFTER the
                # script, read through probe_sql. So: the reference must run,
                # it must CHANGE what the probe sees (or the question tests
                # nothing), and the trap must leave a different state.
                rows, err, _ = ex.script_result(e, e["solution"])
                if err:
                    problems.append(f"exercise {e['id']} solution failed: {err}")
                    continue
                # The probe may not even run on the untouched database -- a
                # table or view the script is meant to create does not exist
                # yet -- and that is itself proof the solution changes things.
                untouched, _, _ = ex.script_result(e, "")
                if untouched is not None and ex.compare(rows, untouched)[0]:
                    problems.append(
                        f"exercise {e['id']} ({e['title']}): the probe sees the"
                        f" same state whether or not the solution runs, so the"
                        f" question grades nothing")
                trap_rows, trap_err, _ = ex.script_result(e, e["trap_sql"])
                if trap_err:
                    traps_by_error += 1
                elif ex.compare(trap_rows, rows)[0]:
                    problems.append(
                        f"exercise {e['id']} ({e['title']}): trap_sql grades as"
                        f" CORRECT, so the question does not actually test its"
                        f" concept")
                else:
                    traps_by_result += 1
                # Claims see the sandbox as the solution left it.
                sb = db.sandbox()
                try:
                    db.run_script(sb, e["solution"])
                    for stmt in db.split_statements(e.get("driver_sql", "")):
                        try:
                            sb.execute(stmt)
                        except sqlite3.Error:
                            pass
                    for says, holds in e.get("claims", ()):
                        try:
                            if not holds(rows, sb):
                                problems.append(
                                    f"exercise {e['id']} ({e['title']}): prompt"
                                    f" claim is FALSE -- {says}")
                            else:
                                claims_checked += 1
                        except Exception as exc:
                            problems.append(
                                f"exercise {e['id']} claim {says!r} could not"
                                f" be evaluated: {exc}")
                finally:
                    sb.close()
                scripts_checked += 1
                continue

            rows, err = run(conn, e["solution"])
            if err:
                problems.append(f"exercise {e['id']} solution failed: {err}")
                continue
            if not rows:
                problems.append(f"exercise {e['id']} solution returns no rows")

            # A value column that is the same on every row means the question
            # cannot tell a right answer from a wrong one -- Q477 asked for the
            # last day of the month against a timetable running an identical 24
            # services every day, so asking for the 15th graded as correct. Only
            # the row count differed, which is why trap_sql alone did not catch
            # it. Two rows can legitimately tie, so this starts at three.
            if len(rows) > 2 and len(rows[0]) > 1:
                for col in range(1, len(rows[0])):
                    if len({r[col] for r in rows}) == 1:
                        problems.append(
                            f"exercise {e['id']} ({e['title']}): column {col}"
                            f" is {rows[0][col]!r} on all {len(rows)} rows, so"
                            f" the question grades nothing but the row count")
                        flat_checked += 1

            # Claims assert that what the PROMPT says about the data is actually
            # true -- a stated range, a row count, a "these appear with 0" case.
            # trap_sql proves a query is wrong; nothing else checks whether the
            # question describes reality, and prompts have drifted from the data
            # twice now.
            for says, holds in e.get("claims", ()):
                try:
                    if not holds(rows, conn):
                        problems.append(
                            f"exercise {e['id']} ({e['title']}): prompt claim is FALSE "
                            f"-- {says}")
                    else:
                        claims_checked += 1
                except Exception as exc:
                    problems.append(
                        f"exercise {e['id']} claim {says!r} could not be evaluated: {exc}")

            # An efficiency question asserts something about the query PLAN,
            # because its slow and fast forms return identical rows. Check the
            # reference actually takes the route it demands -- otherwise the
            # question is unanswerable.
            if e.get("plan_requires") or e.get("plan_forbids"):
                # These open with a slow query already in the editor. It has to
                # RETURN the right answer -- otherwise the question reads as
                # broken rather than as slow -- and it has to FAIL the plan
                # assertion, or there is nothing to improve.
                starter = e.get("starter_sql")
                if not starter:
                    problems.append(
                        f"exercise {e['id']} asserts a plan but has no "
                        f"starter_sql to open with")
                else:
                    srows, serr = run(conn, starter)
                    if serr:
                        problems.append(
                            f"exercise {e['id']} starter_sql failed: {serr}")
                    elif not ex.compare([tuple(r) for r in srows],
                                        [tuple(r) for r in rows])[0]:
                        problems.append(
                            f"exercise {e['id']} starter_sql returns the WRONG "
                            f"rows -- it should be correct but slow")
                    elif ex.plan_ok(e, ex.query_plan(conn, starter))[0]:
                        problems.append(
                            f"exercise {e['id']} starter_sql already satisfies "
                            f"the plan assertion, so there is nothing to fix")
                    else:
                        starters_checked += 1
                ok, why = ex.plan_ok(e, ex.query_plan(conn, e["solution"]))
                if not ok:
                    problems.append(
                        f"exercise {e['id']} ({e['title']}): its own solution "
                        f"fails its plan assertion -- {why}")
                else:
                    plans_checked += 1

            trap_rows, trap_err = run(conn, e["trap_sql"])
            if trap_err:
                traps_by_error += 1
                continue
            passed, _ = ex.compare([tuple(r) for r in trap_rows], [tuple(r) for r in rows])
            if passed and (e.get("plan_requires") or e.get("plan_forbids")):
                # Returning the right rows is not enough for these: the trap is
                # SUPPOSED to return them, and be rejected on its plan.
                passed, _ = ex.plan_ok(e, ex.query_plan(conn, e["trap_sql"]))
                if not passed:
                    traps_by_plan += 1
                    continue
            if passed:
                problems.append(
                    f"exercise {e['id']} ({e['title']}): trap_sql grades as CORRECT, "
                    f"so the question does not actually test its concept")
            else:
                traps_by_result += 1
    finally:
        conn.close()

    linked = sum(1 for r in ledger.values() if r["gui"].startswith("ex"))
    print(f"ledger entries : {len(ledger)}")
    print(f"exercises      : {len(ex.EXERCISES)}")
    print(f"linked to GUI  : {linked}")
    print(f"traps rejected : "
          f"{traps_by_error + traps_by_result + traps_by_plan} / {len(ex.EXERCISES)} "
          f"({traps_by_error} by SQL error, {traps_by_result} by wrong result, "
          f"{traps_by_plan} by wrong query plan)")
    print(f"plan assertions: {plans_checked} solutions take the route they demand")
    print(f"starter queries: {starters_checked} correct but rejected on their plan")
    print(f"prompt claims  : {claims_checked} verified against the data")
    print(f"script checks  : {scripts_checked} writable questions change the"
          f" state their probe reads, and reject their trap")
    print(f"answer spread  : "
          f"{len(ex.EXERCISES) - flat_checked} of {len(ex.EXERCISES)}"
          f" have no value column that is constant on every row")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
