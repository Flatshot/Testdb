"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q222-Q251) run on the repair-depot schema, re-seeded
again (SEED 149 -> 185) so every row, name, date and amount differs from the
last set and no remembered answer value carries over.

This set is deliberately easier than Q192-Q221, and there is no recursion in it
at all. Two rules shaped every question:

  * one concept each. No question stacks a window function on top of a
    self-join on top of a date trick. If you know the one idea being drilled,
    the query is short -- no reference solution here runs past six lines.
  * the prompt states the grain. Where the last set left you to work out what
    one row meant, these say it: "one row per depot", "one row per month".

The weighting follows where the questions have been going lately:

  window functions    9  ranking, frames, LAG/LEAD, share of total, NTILE
  aggregation         4  COUNT(*) vs COUNT(col), WHERE vs HAVING, pivots
  joins               4  outer joins that keep zeroes, self-joins, anti-joins
  subqueries/EXISTS   3  EXISTS, NOT EXISTS vs NOT IN, correlation
  dates               3  julianday arithmetic, strftime, %m versus %Y-%m
  set operations      2  EXCEPT is directional, INTERSECT is not UNION
  NULLs               2  = NULL never matches, <> silently drops rows
  grain               2  two child tables fan out; SUM(a*b) is not SUM(a)*b
  general             1  CASE is first-match-wins

Each question carries:

  concept   the mistake or technique it drills
  solution  one correct answer
  trap_sql  the tempting WRONG query -- check_questions.py asserts the grader
            rejects it, which is what proves the question actually has teeth
  note      the lesson, shown in the GUI once you get it right
  claims    optional facts about the data that the prompt asserts, re-checked
            against the live database so a prompt cannot quietly go stale

Grading compares your result against the reference as an unordered multiset of
rows, with floats rounded to 2 decimals. Row order never matters and you do not
need to remember ROUND(). Column count and values do matter -- each prompt
states exactly what to return.

Spoiler warning: the reference SQL is in this file.
"""

# The two cut-off dates the questions compare against. Fixed rather than taken
# from the clock: a question about which contracts have ended has to mean the
# same thing next month as it does today. The data ends on 2026-07-20.
CUTOFF = "2026-08-01"
WARRANTY_FROM = "2026-01-01"

EXERCISES = [
    # ---------------------------------------------------- window functions
    dict(
        id=1, ledger="Q222", concept="W1", tier="Window functions",
        title="Invoicing, month by month and so far",
        prompt=(
            "One row per calendar month in which any invoice was issued: the"
            " month, what was invoiced in it, and the running total of"
            " everything invoiced up to and including that month.\n\n"
            "Months are 'YYYY-MM'. The running total on the last month equals"
            " the total of every invoice in the table.\n\n"
            "Return: month, month_total, running_total"
        ),
        solution=(
            "WITH m AS (SELECT strftime('%Y-%m', issued_on) AS mth,"
            " SUM(amount) AS total FROM invoices GROUP BY 1)"
            " SELECT mth, ROUND(total, 2),"
            " ROUND(SUM(total) OVER (ORDER BY mth), 2) FROM m"
        ),
        trap_sql=(
            "WITH m AS (SELECT strftime('%Y-%m', issued_on) AS mth,"
            " SUM(amount) AS total FROM invoices GROUP BY 1)"
            " SELECT mth, ROUND(total, 2), ROUND(SUM(total) OVER (), 2) FROM m"
        ),
        note="ORDER BY inside OVER() is the whole difference. SUM(x) OVER ()"
             " with no ORDER BY sees every row at once and gives the same grand"
             " total on every line; SUM(x) OVER (ORDER BY mth) sees only rows up"
             " to the current one, which is what makes it accumulate.",
        claims=[
            ("one row per month invoiced, 19 of them",
             lambda rows, c: len(rows) == 19),
            ("the last running total equals every invoice added up",
             lambda rows, c: abs(max(r[2] for r in rows) - c.execute(
                 "SELECT SUM(amount) FROM invoices").fetchone()[0]) < 0.01),
        ],
    ),
    dict(
        id=2, ledger="Q223", concept="W1", tier="Window functions",
        title="Month on month",
        prompt=(
            "One row per month in which any work order was opened: the month,"
            " how many were opened, and the change from the month before.\n\n"
            "The earliest month has no month before it, so its change is"
            " NULL -- leave it NULL rather than turning it into 0.\n\n"
            "Return: month, work_orders, change"
        ),
        solution=(
            "WITH m AS (SELECT strftime('%Y-%m', opened_at) AS mth,"
            " COUNT(*) AS n FROM work_orders GROUP BY 1)"
            " SELECT mth, n, n - LAG(n) OVER (ORDER BY mth) FROM m"
        ),
        trap_sql=(
            "WITH m AS (SELECT strftime('%Y-%m', opened_at) AS mth,"
            " COUNT(*) AS n FROM work_orders GROUP BY 1)"
            " SELECT mth, n, n - LAG(n) OVER (PARTITION BY mth ORDER BY mth)"
            " FROM m"
        ),
        note="PARTITION BY mth puts every month in a window of its own, so LAG"
             " looks for a previous row inside a one-row window and finds"
             " nothing: every change comes back NULL. You partition by what the"
             " rows have in COMMON, and order by what separates them. Here"
             " nothing is in common -- there is one series -- so no PARTITION.",
        claims=[
            ("18 months, and exactly one NULL change",
             lambda rows, c: len(rows) == 18
             and sum(1 for r in rows if r[2] is None) == 1),
        ],
    ),
    dict(
        id=3, ledger="Q224", concept="W2", tier="Window functions",
        title="The latest job on each machine",
        prompt=(
            "For every machine that has ever had a work order, its most recent"
            " one. One row per machine -- machines with no work orders at all"
            " do not appear.\n\n"
            "No machine has two work orders opened on the same date, so 'most"
            " recent' is never a tie.\n\n"
            "Return: machine_id, work_order_id, opened_at"
        ),
        solution=(
            "WITH r AS (SELECT machine_id, work_order_id, opened_at,"
            " ROW_NUMBER() OVER (PARTITION BY machine_id"
            " ORDER BY opened_at DESC) AS rn FROM work_orders)"
            " SELECT machine_id, work_order_id, opened_at FROM r WHERE rn = 1"
        ),
        trap_sql=(
            "WITH r AS (SELECT machine_id, work_order_id, opened_at,"
            " ROW_NUMBER() OVER (ORDER BY opened_at DESC) AS rn"
            " FROM work_orders)"
            " SELECT machine_id, work_order_id, opened_at FROM r WHERE rn = 1"
        ),
        note="Without PARTITION BY the numbering runs straight through the"
             " whole table, so rn = 1 is the single latest work order anywhere"
             " and you get one row back instead of one per machine. PARTITION BY"
             " restarts the count for each machine -- it is the GROUP BY of the"
             " window world, except the detail rows survive.",
        claims=[
            ("one row per machine that has any work order, 71 of them",
             lambda rows, c: len(rows) == 71
             and len({r[0] for r in rows}) == len(rows)),
        ],
    ),
    dict(
        id=4, ledger="Q225", concept="W2", tier="Window functions",
        title="Busiest at each depot, ties and all",
        prompt=(
            "The busiest technician at each depot, counting work orders they"
            " are the assigned technician on.\n\n"
            "One depot has two technicians tied on the same count. Both of them"
            " must appear -- five rows in total, not four.\n\n"
            "Return: depot_id, technician_id, name, work_orders"
        ),
        solution=(
            "WITH c AS (SELECT t.depot_id, t.technician_id, t.name,"
            " COUNT(w.work_order_id) AS n FROM technicians t"
            " LEFT JOIN work_orders w ON w.technician_id = t.technician_id"
            " GROUP BY 1, 2, 3),"
            " r AS (SELECT *, RANK() OVER (PARTITION BY depot_id"
            " ORDER BY n DESC) AS rk FROM c)"
            " SELECT depot_id, technician_id, name, n FROM r WHERE rk = 1"
        ),
        trap_sql=(
            "WITH c AS (SELECT t.depot_id, t.technician_id, t.name,"
            " COUNT(w.work_order_id) AS n FROM technicians t"
            " LEFT JOIN work_orders w ON w.technician_id = t.technician_id"
            " GROUP BY 1, 2, 3),"
            " r AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY depot_id"
            " ORDER BY n DESC) AS rk FROM c)"
            " SELECT depot_id, technician_id, name, n FROM r WHERE rk = 1"
        ),
        note="ROW_NUMBER always hands out 1, 2, 3 with no repeats, so when two"
             " technicians tie it picks one of them arbitrarily and you silently"
             " lose the other. RANK gives tied rows the same number. Rule of"
             " thumb: ROW_NUMBER when you want exactly one row, RANK when you"
             " want everyone who earned the position.",
        claims=[
            ("five rows across four depots -- one depot is tied",
             lambda rows, c: len(rows) == 5 and len({r[0] for r in rows}) == 4),
        ],
    ),
    dict(
        id=5, ledger="Q226", concept="W1", tier="Window functions",
        title="Three-month rolling average",
        prompt=(
            "One row per month in which any work order was opened: the month,"
            " how many were opened, and the average over that month and the two"
            " months before it.\n\n"
            "The first month averages just itself, the second averages two"
            " months, and every month after that averages three.\n\n"
            "Return: month, work_orders, rolling_avg"
        ),
        solution=(
            "WITH m AS (SELECT strftime('%Y-%m', opened_at) AS mth,"
            " COUNT(*) AS n FROM work_orders GROUP BY 1)"
            " SELECT mth, n, ROUND(AVG(n) OVER (ORDER BY mth"
            " ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) FROM m"
        ),
        trap_sql=(
            "WITH m AS (SELECT strftime('%Y-%m', opened_at) AS mth,"
            " COUNT(*) AS n FROM work_orders GROUP BY 1)"
            " SELECT mth, n, ROUND(AVG(n) OVER (ORDER BY mth), 2) FROM m"
        ),
        note="An OVER() with ORDER BY and no ROWS clause does not mean 'no"
             " frame' -- it means the default frame, everything from the start"
             " up to the current row. That is a running average over all history,"
             " not a rolling one. ROWS BETWEEN 2 PRECEDING AND CURRENT ROW is"
             " what pins the window to three rows.",
        claims=[
            ("18 months, and the first rolling average is just that month",
             lambda rows, c: len(rows) == 18
             and abs(min(rows, key=lambda r: r[0])[2]
                     - min(rows, key=lambda r: r[0])[1]) < 0.01),
        ],
    ),
    dict(
        id=6, ledger="Q227", concept="W2", tier="Window functions",
        title="Quartiles of workload",
        prompt=(
            "Every technician who has logged any labour, with their total hours"
            " and which quarter of the workforce they fall into by hours:"
            " 1 for the busiest quarter, 4 for the quietest.\n\n"
            "Fourteen technicians split into four groups, so the first two"
            " groups get four each and the last two get three.\n\n"
            "Return: technician_id, total_hours, quartile"
        ),
        solution=(
            "SELECT technician_id, ROUND(SUM(hours), 2),"
            " NTILE(4) OVER (ORDER BY SUM(hours) DESC)"
            " FROM labor_entries GROUP BY technician_id"
        ),
        trap_sql=(
            "SELECT technician_id, ROUND(SUM(hours), 2),"
            " NTILE(4) OVER (ORDER BY SUM(hours))"
            " FROM labor_entries GROUP BY technician_id"
        ),
        note="NTILE(4) deals the rows into four groups in the order you give"
             " it, so the ORDER BY direction decides which end gets bucket 1."
             " Ascending puts the QUIETEST technician in bucket 1. Whenever a"
             " question says 'top' or 'busiest', say DESC out loud and check it"
             " is actually in the OVER clause.",
        claims=[
            ("14 technicians, bucketed 4/4/3/3",
             lambda rows, c: len(rows) == 14
             and sorted(sum(1 for r in rows if r[2] == q) for q in (1, 2, 3, 4))
             == [3, 3, 4, 4]),
            ("bucket 1 holds more hours than bucket 4",
             lambda rows, c: min(r[1] for r in rows if r[2] == 1)
             > max(r[1] for r in rows if r[2] == 4)),
        ],
    ),
    dict(
        id=7, ledger="Q228", concept="W3", tier="Window functions",
        title="Share of the invoiced total",
        prompt=(
            "One row per work-order priority: the priority, the total invoiced"
            " on work orders of that priority, and that total as a percentage"
            " of everything invoiced.\n\n"
            "Only work orders that actually have an invoice count. The four"
            " percentages add up to 100.\n\n"
            "Return: priority, invoiced, pct_of_total"
        ),
        solution=(
            "WITH p AS (SELECT w.priority, SUM(i.amount) AS amt FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " GROUP BY 1)"
            " SELECT priority, ROUND(amt, 2),"
            " ROUND(100.0 * amt / SUM(amt) OVER (), 2) FROM p"
        ),
        trap_sql=(
            "WITH p AS (SELECT w.priority, SUM(i.amount) AS amt FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " GROUP BY 1)"
            " SELECT priority, ROUND(amt, 2),"
            " ROUND(100.0 * amt / SUM(amt) OVER (PARTITION BY priority), 2)"
            " FROM p"
        ),
        note="This is the mirror image of question 1. There you needed the"
             " window narrowed and here you need it wide open: OVER () with"
             " nothing in it is every row, which is exactly the denominator a"
             " share needs. PARTITION BY priority shrinks the window to the row"
             " itself, so every share comes out as 100%.",
        claims=[
            ("four priorities, and the percentages sum to 100",
             lambda rows, c: len(rows) == 4
             and abs(sum(r[2] for r in rows) - 100) < 0.05),
        ],
    ),
    dict(
        id=8, ledger="Q229", concept="W3", tier="Window functions",
        title="How long until the machine is seen again",
        prompt=(
            "Every work order, with the number of whole days until the NEXT"
            " work order opened on the same machine.\n\n"
            "The most recent work order on each machine has nothing after it,"
            " so its gap is NULL. One row per work order -- all 180.\n\n"
            "Return: machine_id, work_order_id, opened_at, days_to_next"
        ),
        solution=(
            "SELECT machine_id, work_order_id, opened_at,"
            " CAST(julianday(LEAD(opened_at) OVER (PARTITION BY machine_id"
            " ORDER BY opened_at)) - julianday(opened_at) AS INTEGER)"
            " FROM work_orders"
        ),
        trap_sql=(
            "SELECT machine_id, work_order_id, opened_at,"
            " CAST(julianday(LEAD(opened_at) OVER (ORDER BY opened_at))"
            " - julianday(opened_at) AS INTEGER) FROM work_orders"
        ),
        note="LEAD without PARTITION BY hands you the next work order in the"
             " whole company, not the next one on that machine, and because the"
             " company is busy those gaps are almost all 0 or 1. The partition"
             " is what makes 'next' mean next-within-this-machine. Same idea as"
             " LAG in question 2, pointing forwards instead of back.",
        claims=[
            ("all 180 work orders, and 71 of them end a machine's history",
             lambda rows, c: len(rows) == 180
             and sum(1 for r in rows if r[3] is None) == 71),
        ],
    ),
    dict(
        id=9, ledger="Q230", concept="W3", tier="Window functions",
        title="Each entry against its technician's average",
        prompt=(
            "Every labour entry dated in January 2026, with the average hours"
            " of the January entries belonging to that same technician.\n\n"
            "One row per entry, not one per technician: the same average"
            " repeats down each technician's entries.\n\n"
            "Return: entry_id, technician_id, hours, tech_avg"
        ),
        solution=(
            "SELECT entry_id, technician_id, hours,"
            " ROUND(AVG(hours) OVER (PARTITION BY technician_id), 2)"
            " FROM labor_entries"
            " WHERE work_date >= '2026-01-01' AND work_date < '2026-02-01'"
        ),
        trap_sql=(
            "SELECT MIN(entry_id), technician_id, SUM(hours),"
            " ROUND(AVG(hours), 2) FROM labor_entries"
            " WHERE work_date >= '2026-01-01' AND work_date < '2026-02-01'"
            " GROUP BY technician_id"
        ),
        note="This is the difference between the two in one query. GROUP BY"
             " collapses the entries and you can never see an individual one"
             " again; the window function computes the same average but leaves"
             " every row standing beside it. When a question wants detail AND a"
             " summary in the same row, that is the signal for a window.",
        claims=[
            ("one row per January entry, and each technician's average repeats",
             lambda rows, c: len(rows) == c.execute(
                 "SELECT COUNT(*) FROM labor_entries WHERE work_date >="
                 " '2026-01-01' AND work_date < '2026-02-01'").fetchone()[0]
             and len({r[1] for r in rows}) < len(rows)),
        ],
    ),
    # -------------------------------------------------------- aggregation
    dict(
        id=10, ledger="Q231", concept="A2", tier="Aggregation",
        title="Certified and not",
        prompt=(
            "One row per depot: how many technicians it has, and how many of"
            " them have a certification level recorded.\n\n"
            "Four technicians company-wide have no cert_level, so the two"
            " counts differ at the depots those technicians work from.\n\n"
            "Return: depot_id, depot_name, technicians, certified"
        ),
        solution=(
            "SELECT d.depot_id, d.name, COUNT(*), COUNT(t.cert_level)"
            " FROM depots d JOIN technicians t ON t.depot_id = d.depot_id"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT d.depot_id, d.name, COUNT(*), COUNT(*)"
            " FROM depots d JOIN technicians t ON t.depot_id = d.depot_id"
            " GROUP BY 1, 2"
        ),
        note="COUNT(*) counts rows. COUNT(column) counts rows where that column"
             " is not NULL. That single difference is the cheapest way to count"
             " 'how many of these have a value' -- no CASE, no subquery. It also"
             " means COUNT(some_column) after a LEFT JOIN is how you get a"
             " genuine zero instead of a phantom 1.",
        claims=[
            ("four depots, 14 technicians, 10 of them certified",
             lambda rows, c: len(rows) == 4
             and sum(r[2] for r in rows) == 14
             and sum(r[3] for r in rows) == 10),
        ],
    ),
    dict(
        id=11, ledger="Q232", concept="A3", tier="Aggregation",
        title="Which priorities were busy in 2026",
        prompt=(
            "Counting only work orders opened on or after 2026-01-01, one row"
            " per priority, keeping the priorities with at least 15 of them.\n\n"
            "Two of the four priorities clear the bar.\n\n"
            "Return: priority, work_orders"
        ),
        solution=(
            "SELECT priority, COUNT(*) FROM work_orders"
            " WHERE opened_at >= '2026-01-01'"
            " GROUP BY priority HAVING COUNT(*) >= 15"
        ),
        trap_sql=(
            "SELECT priority, COUNT(*) FROM work_orders"
            " GROUP BY priority"
            " HAVING opened_at >= '2026-01-01' AND COUNT(*) >= 15"
        ),
        note="WHERE throws away ROWS before grouping; HAVING throws away GROUPS"
             " after. The date test is about a row, so it belongs in WHERE."
             " Put it in HAVING and SQLite does not complain -- it just picks"
             " one arbitrary row's opened_at to test, and every count you get"
             " back is over all history rather than 2026.",
        claims=[
            ("two priorities clear 15 in 2026",
             lambda rows, c: len(rows) == 2 and all(r[1] >= 15 for r in rows)),
        ],
    ),
    dict(
        id=12, ledger="Q233", concept="A1", tier="Aggregation",
        title="Invoice status by priority",
        prompt=(
            "One row per work-order priority, with the number of its invoices"
            " in each of three statuses side by side as columns.\n\n"
            "Every priority has at least one PAID invoice; some have zero"
            " PENDING or zero OVERDUE, and those must show as 0.\n\n"
            "Return: priority, paid, pending, overdue"
        ),
        solution=(
            "SELECT w.priority,"
            " SUM(CASE WHEN i.status = 'PAID' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN i.status = 'PENDING' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN i.status = 'OVERDUE' THEN 1 ELSE 0 END)"
            " FROM work_orders w"
            " JOIN invoices i ON i.work_order_id = w.work_order_id"
            " GROUP BY 1"
        ),
        trap_sql=(
            "SELECT w.priority,"
            " COUNT(CASE WHEN i.status = 'PAID' THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN i.status = 'PENDING' THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN i.status = 'OVERDUE' THEN 1 ELSE 0 END)"
            " FROM work_orders w"
            " JOIN invoices i ON i.work_order_id = w.work_order_id"
            " GROUP BY 1"
        ),
        note="Pick ONE of two shapes and stick to it: SUM(CASE WHEN c THEN 1"
             " ELSE 0 END) or COUNT(CASE WHEN c THEN 1 END). The mixture in the"
             " trap -- COUNT over an ELSE 0 -- counts every row, because 0 is a"
             " value and COUNT only skips NULL. All three columns come back"
             " identical to the row count, which is the tell.",
        claims=[
            ("four priorities, and the three columns total every invoice"
             " that is not VOID",
             lambda rows, c: len(rows) == 4
             and sum(r[1] + r[2] + r[3] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM invoices WHERE status <> 'VOID'"
             ).fetchone()[0]),
        ],
    ),
    dict(
        id=13, ledger="Q234", concept="A2", tier="Aggregation",
        title="Average score, where there is one",
        prompt=(
            "One row per inspection result: how many inspections had that"
            " result, how many of them carry a score, and the average of the"
            " scores that exist.\n\n"
            "Plenty of inspections have no score at all. The average must be"
            " over the scored ones only.\n\n"
            "Return: result, inspections, scored, avg_score"
        ),
        solution=(
            "SELECT result, COUNT(*), COUNT(score), ROUND(AVG(score), 2)"
            " FROM inspections GROUP BY result"
        ),
        trap_sql=(
            "SELECT result, COUNT(*), COUNT(score),"
            " ROUND(SUM(score) * 1.0 / COUNT(*), 2)"
            " FROM inspections GROUP BY result"
        ),
        note="AVG already ignores NULLs -- it divides by the number of non-NULL"
             " values, not by the number of rows. Rebuilding it as SUM/COUNT(*)"
             " quietly puts the unscored inspections into the denominator and"
             " drags every average down. If you ever do need SUM over rows"
             " rather than values, that is SUM(COALESCE(score, 0)) and say so.",
        claims=[
            ("three results, and fewer scored than inspected in each",
             lambda rows, c: len(rows) == 3 and all(r[2] < r[1] for r in rows)),
        ],
    ),
    # -------------------------------------------------------------- joins
    dict(
        id=14, ledger="Q235", concept="J2", tier="Joins",
        title="Every part, used or not",
        prompt=(
            "One row for every part in the catalogue: its id, its name, and the"
            " number of DISTINCT work orders it has been used on.\n\n"
            "Four parts have never been used on anything. They must appear"
            " with 0, so all 40 parts come back.\n\n"
            "Return: part_id, name, work_orders"
        ),
        solution=(
            "SELECT p.part_id, p.name, COUNT(DISTINCT pu.work_order_id)"
            " FROM parts p LEFT JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT p.part_id, p.name, COUNT(DISTINCT pu.work_order_id)"
            " FROM parts p JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY 1, 2"
        ),
        note="An inner join can only ever return parts that matched, so the"
             " four unused parts vanish rather than showing 0 -- and 'the ones"
             " with none' is usually exactly what the question is about. Note"
             " the pairing: LEFT JOIN plus COUNT(a column from the right side)."
             " COUNT(*) there would give the unused parts a 1.",
        claims=[
            ("all 40 parts, four of them unused",
             lambda rows, c: len(rows) == 40
             and sum(1 for r in rows if r[2] == 0) == 4),
        ],
    ),
    dict(
        id=15, ledger="Q236", concept="J2", tier="Joins",
        title="Critical jobs per technician",
        prompt=(
            "One row for every technician: id, name, and how many CRITICAL work"
            " orders they are the assigned technician on.\n\n"
            "Five technicians have never been assigned one. They must appear"
            " with 0, so all 14 technicians come back.\n\n"
            "Return: technician_id, name, critical_jobs"
        ),
        solution=(
            "SELECT t.technician_id, t.name, COUNT(w.work_order_id)"
            " FROM technicians t LEFT JOIN work_orders w"
            " ON w.technician_id = t.technician_id AND w.priority = 'critical'"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, COUNT(w.work_order_id)"
            " FROM technicians t LEFT JOIN work_orders w"
            " ON w.technician_id = t.technician_id"
            " WHERE w.priority = 'critical' GROUP BY 1, 2"
        ),
        note="A condition on the right-hand table has to go in the ON clause of"
             " a LEFT JOIN. In WHERE it runs AFTER the join has already padded"
             " the unmatched technicians with NULLs, and NULL = 'critical' is"
             " not true, so those rows are filtered straight back out and the"
             " outer join silently becomes an inner one.",
        claims=[
            ("all 14 technicians, five with none",
             lambda rows, c: len(rows) == 14
             and sum(1 for r in rows if r[2] == 0) == 5),
        ],
    ),
    dict(
        id=16, ledger="Q237", concept="J1", tier="Joins",
        title="Hired the same year, same depot",
        prompt=(
            "Pairs of technicians who work from the same depot and were hired"
            " in the same calendar year.\n\n"
            "Each pair once, not twice: Ann with Bob, never also Bob with Ann,"
            " and nobody paired with themselves. Three pairs exist.\n\n"
            "Return: depot_id, name_a, name_b"
        ),
        solution=(
            "SELECT a.depot_id, a.name, b.name FROM technicians a"
            " JOIN technicians b ON b.depot_id = a.depot_id"
            " AND strftime('%Y', b.hired_on) = strftime('%Y', a.hired_on)"
            " AND b.technician_id > a.technician_id"
        ),
        trap_sql=(
            "SELECT a.depot_id, a.name, b.name FROM technicians a"
            " JOIN technicians b ON b.depot_id = a.depot_id"
            " AND strftime('%Y', b.hired_on) = strftime('%Y', a.hired_on)"
            " AND b.technician_id <> a.technician_id"
        ),
        note="<> only stops a row pairing with itself; it still lets each pair"
             " through in both directions, so you get exactly twice as many"
             " rows as there are pairs. Use > (or <) on the id instead: it"
             " excludes the self-match AND fixes an order, so only one of the"
             " two directions survives.",
        claims=[
            ("three pairs, none of them a mirror of another",
             lambda rows, c: len(rows) == 3
             and len({frozenset((r[1], r[2])) for r in rows}) == 3),
        ],
    ),
    dict(
        id=17, ledger="Q238", concept="J2", tier="Joins",
        title="Machines nobody has touched",
        prompt=(
            "Every machine that has never had a single work order raised"
            " against it.\n\n"
            "Write it as an outer join that keeps the non-matches, rather than"
            " with NOT IN. There are 27 such machines.\n\n"
            "Return: machine_id, serial"
        ),
        solution=(
            "SELECT m.machine_id, m.serial FROM machines m"
            " LEFT JOIN work_orders w ON w.machine_id = m.machine_id"
            " WHERE w.work_order_id IS NULL"
        ),
        trap_sql=(
            "SELECT m.machine_id, m.serial FROM machines m"
            " LEFT JOIN work_orders w ON w.machine_id = m.machine_id"
            " AND w.work_order_id IS NULL"
        ),
        note="The anti-join is two halves and both matter: LEFT JOIN to keep"
             " the unmatched machines, then WHERE <right column> IS NULL to"
             " keep ONLY those. Moving that test into ON changes its meaning"
             " entirely -- it becomes part of what counts as a match, matches"
             " nothing, and hands back all 98 machines.",
        claims=[
            ("27 machines, and none of them appears in work_orders",
             lambda rows, c: len(rows) == 27
             and not {r[0] for r in rows} & {
                 x[0] for x in c.execute(
                     "SELECT DISTINCT machine_id FROM work_orders")}),
        ],
    ),
    # ------------------------------------------------- subqueries & EXISTS
    dict(
        id=18, ledger="Q239", concept="E1", tier="Subqueries & EXISTS",
        title="Customers still under warranty somewhere",
        prompt=(
            "Every customer who owns at least one machine whose warranty runs"
            " beyond " + WARRANTY_FROM + ".\n\n"
            "Machines belong to sites and sites belong to customers. One row"
            " per customer, however many qualifying machines they own --"
            " three customers own two apiece.\n\n"
            "Return: customer_id, name"
        ),
        solution=(
            "SELECT c.customer_id, c.name FROM customers c"
            " WHERE EXISTS (SELECT 1 FROM sites s"
            " JOIN machines m ON m.site_id = s.site_id"
            " WHERE s.customer_id = c.customer_id"
            " AND m.warranty_until > '" + WARRANTY_FROM + "')"
        ),
        trap_sql=(
            "SELECT c.customer_id, c.name FROM customers c"
            " JOIN sites s ON s.customer_id = c.customer_id"
            " JOIN machines m ON m.site_id = s.site_id"
            " WHERE m.warranty_until > '" + WARRANTY_FROM + "'"
        ),
        note="Joining down to machines to answer a question ABOUT customers"
             " changes the grain: you get one row per qualifying machine, so a"
             " customer with two of them appears twice. EXISTS asks the"
             " question without changing what a row is -- it returns yes or no"
             " and stops at the first hit. SELECT DISTINCT would patch the join,"
             " but EXISTS says what you meant.",
        claims=[
            ("no customer is listed twice",
             lambda rows, c: len({r[0] for r in rows}) == len(rows)),
            ("at least one customer owns two such machines, so a plain join"
             " would double up",
             lambda rows, c: c.execute(
                 "SELECT MAX(n) FROM (SELECT COUNT(*) n FROM sites s JOIN"
                 " machines m ON m.site_id = s.site_id WHERE m.warranty_until"
                 " > '" + WARRANTY_FROM + "' GROUP BY s.customer_id)").fetchone()[0] > 1),
        ],
    ),
    dict(
        id=19, ledger="Q240", concept="E1", tier="Subqueries & EXISTS",
        title="Never on a critical job",
        prompt=(
            "Every technician who has never been the assigned technician on a"
            " critical work order. Five of the fourteen qualify.\n\n"
            "Watch out: three critical work orders have no technician assigned"
            " at all, which is what makes the obvious answer wrong.\n\n"
            "Return: technician_id, name"
        ),
        solution=(
            "SELECT t.technician_id, t.name FROM technicians t"
            " WHERE NOT EXISTS (SELECT 1 FROM work_orders w"
            " WHERE w.technician_id = t.technician_id"
            " AND w.priority = 'critical')"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name FROM technicians t"
            " WHERE t.technician_id NOT IN"
            " (SELECT technician_id FROM work_orders WHERE priority ="
            " 'critical')"
        ),
        note="NOT IN over a list containing even one NULL returns no rows at"
             " all. 'Is 7 not in (3, 5, NULL)?' -- SQL cannot say no, because"
             " NULL might have been 7, so the answer is NULL and nothing"
             " passes. NOT EXISTS has no such hole. Either use NOT EXISTS, or"
             " add WHERE technician_id IS NOT NULL inside the subquery.",
        claims=[
            ("five technicians, and some critical work orders are unassigned",
             lambda rows, c: len(rows) == 5 and c.execute(
                 "SELECT COUNT(*) FROM work_orders WHERE priority = 'critical'"
                 " AND technician_id IS NULL").fetchone()[0] == 3),
        ],
    ),
    dict(
        id=20, ledger="Q241", concept="E2", tier="Subqueries & EXISTS",
        title="Dear for its own category",
        prompt=(
            "Every part costing more than the average unit_cost of the parts in"
            " ITS OWN category -- not more than the average across the whole"
            " catalogue.\n\n"
            "One row per part.\n\n"
            "Return: part_id, name, category, unit_cost"
        ),
        solution=(
            "SELECT p.part_id, p.name, p.category, p.unit_cost FROM parts p"
            " WHERE p.unit_cost > (SELECT AVG(p2.unit_cost) FROM parts p2"
            " WHERE p2.category = p.category)"
        ),
        trap_sql=(
            "SELECT p.part_id, p.name, p.category, p.unit_cost FROM parts p"
            " WHERE p.unit_cost > (SELECT AVG(unit_cost) FROM parts)"
        ),
        note="The correlation is the single line WHERE p2.category ="
             " p.category. Without it the subquery runs once and every part is"
             " compared with the same number; with it the subquery is"
             " re-evaluated per row against that row's own category. A cheap"
             " part in a cheap category can beat its own average and lose to"
             " the global one, which is why the two answers differ.",
        claims=[
            ("every category with more than one part contributes at least one",
             lambda rows, c: len({r[2] for r in rows}) == 9),
        ],
    ),
    # -------------------------------------------------------------- NULLs
    dict(
        id=21, ledger="Q242", concept="C7", tier="NULLs",
        title="Ended, running, or open-ended",
        prompt=(
            "Classify every contract into one of three states as of "
            + CUTOFF + ", and count them:\n"
            "  'open-ended' if end_date is missing entirely\n"
            "  'ended'      if end_date is before " + CUTOFF + "\n"
            "  'active'     otherwise\n\n"
            "All 34 contracts land in exactly one state.\n\n"
            "Return: state, contracts"
        ),
        solution=(
            "SELECT CASE WHEN end_date IS NULL THEN 'open-ended'"
            " WHEN end_date < '" + CUTOFF + "' THEN 'ended'"
            " ELSE 'active' END, COUNT(*) FROM contracts GROUP BY 1"
        ),
        trap_sql=(
            "SELECT CASE WHEN end_date = NULL THEN 'open-ended'"
            " WHEN end_date < '" + CUTOFF + "' THEN 'ended'"
            " ELSE 'active' END, COUNT(*) FROM contracts GROUP BY 1"
        ),
        note="= NULL is never true -- not even for a NULL. It evaluates to"
             " NULL, which CASE treats as not-matched, so that branch can never"
             " fire. Worse, the next branch is also NULL for those rows, so all"
             " eleven open-ended contracts fall through to ELSE and get"
             " mislabelled 'active'. The only test is IS NULL.",
        claims=[
            ("three states covering all 34 contracts",
             lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 34),
            ("eleven contracts are open-ended",
             lambda rows, c: dict(rows)["open-ended"] == 11),
        ],
    ),
    dict(
        id=22, ledger="Q243", concept="C7", tier="NULLs",
        title="Everyone who is not level 5",
        prompt=(
            "Count technicians by certification level, excluding level 5, and"
            " counting the ones with NO certification level as 'none'.\n\n"
            "Twelve of the fourteen technicians are not level 5 -- four of them"
            " because they have no level at all.\n\n"
            "Return: level, technicians  (level is text: '1'..'4' or 'none')"
        ),
        solution=(
            "SELECT COALESCE(CAST(cert_level AS TEXT), 'none'), COUNT(*)"
            " FROM technicians WHERE cert_level IS NOT 5 GROUP BY 1"
        ),
        trap_sql=(
            "SELECT COALESCE(CAST(cert_level AS TEXT), 'none'), COUNT(*)"
            " FROM technicians WHERE cert_level <> 5 GROUP BY 1"
        ),
        note="cert_level <> 5 drops the uncertified technicians without a"
             " word, because NULL <> 5 is NULL rather than true. Any comparison"
             " on a nullable column silently excludes the NULLs. SQLite's IS"
             " NOT is null-safe and reads the way you meant it; the portable"
             " spelling is (cert_level IS NULL OR cert_level <> 5).",
        claims=[
            ("twelve technicians in five buckets, four of them uncertified",
             lambda rows, c: sum(r[1] for r in rows) == 12
             and len(rows) == 5 and dict(rows)["none"] == 4),
        ],
    ),
    # -------------------------------------------------------------- dates
    dict(
        id=23, ledger="Q244", concept="D1", tier="Dates",
        title="The five slowest jobs to close",
        prompt=(
            "The five closed work orders that took the longest from opening to"
            " closing, longest first.\n\n"
            "Days must be a whole number. Break ties on days by work_order_id"
            " ascending, so the five are unambiguous.\n\n"
            "Return: work_order_id, opened_at, closed_at, days"
        ),
        solution=(
            "SELECT work_order_id, opened_at, closed_at,"
            " CAST(julianday(closed_at) - julianday(opened_at) AS INTEGER)"
            " AS days FROM work_orders WHERE closed_at IS NOT NULL"
            " ORDER BY days DESC, work_order_id LIMIT 5"
        ),
        trap_sql=(
            "SELECT work_order_id, opened_at, closed_at,"
            " closed_at - opened_at AS days FROM work_orders"
            " WHERE closed_at IS NOT NULL"
            " ORDER BY days DESC, work_order_id LIMIT 5"
        ),
        note="Dates in SQLite are text. Subtracting one from another does not"
             " subtract dates -- SQLite coerces each string to a number, which"
             " reads '2026-07-20' as 2026 and stops at the dash, so the answer"
             " is the difference in YEARS, usually 0. julianday() turns a date"
             " into a day number, and the difference between two of those is"
             " days.",
        claims=[
            ("five rows, all with a positive whole number of days",
             lambda rows, c: len(rows) == 5
             and all(isinstance(r[3], int) and r[3] > 0 for r in rows)),
        ],
    ),
    dict(
        id=24, ledger="Q245", concept="D1", tier="Dates",
        title="Which day of the week is busiest",
        prompt=(
            "How many work orders were opened on each day of the week, across"
            " the whole data set. Seven rows, Sunday first.\n\n"
            "Name the day rather than numbering it.\n\n"
            "Return: day_name, work_orders"
        ),
        solution=(
            "SELECT CASE strftime('%w', opened_at)"
            " WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday'"
            " WHEN '2' THEN 'Tuesday' WHEN '3' THEN 'Wednesday'"
            " WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'"
            " ELSE 'Saturday' END, COUNT(*) FROM work_orders"
            " GROUP BY strftime('%w', opened_at)"
        ),
        trap_sql=(
            "SELECT CASE strftime('%W', opened_at)"
            " WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday'"
            " WHEN '2' THEN 'Tuesday' WHEN '3' THEN 'Wednesday'"
            " WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'"
            " ELSE 'Saturday' END, COUNT(*) FROM work_orders"
            " GROUP BY strftime('%W', opened_at)"
        ),
        note="strftime's format letters are case-sensitive and %w and %W are"
             " unrelated: lowercase is day of week 0-6, uppercase is week of"
             " year 00-53. The uppercase version groups the year into 50-odd"
             " buckets and labels the first six of them with day names, which"
             " looks plausible until you count the rows. Worth knowing too:"
             " %j day of year, %d day of month.",
        claims=[
            ("seven days covering all 180 work orders",
             lambda rows, c: len(rows) == 7
             and sum(r[1] for r in rows) == 180),
        ],
    ),
    dict(
        id=25, ledger="Q246", concept="D1", tier="Dates",
        title="Inspections by month, across two years",
        prompt=(
            "One row per calendar month in which any inspection happened: the"
            " month as 'YYYY-MM', and how many inspections it held.\n\n"
            "The data spans two calendar years, so February 2025 and February"
            " 2026 are different months and must not be added together.\n\n"
            "Return: month, inspections"
        ),
        solution=(
            "SELECT strftime('%Y-%m', inspected_at), COUNT(*)"
            " FROM inspections GROUP BY 1"
        ),
        trap_sql=(
            "SELECT strftime('%m', inspected_at), COUNT(*)"
            " FROM inspections GROUP BY 1"
        ),
        note="%m alone is the month number with no year attached, so the two"
             " Februaries collapse into one row and you get at most twelve rows"
             " out of a data set that covers eighteen months. Grouping by a"
             " date always needs every component down to the level you want."
             " The quickest sanity check is the row count.",
        claims=[
            ("more than twelve months, so the two years really do overlap",
             lambda rows, c: len(rows) > 12),
            ("the counts total every inspection",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM inspections").fetchone()[0]),
        ],
    ),
    # ----------------------------------------------------- set operations
    dict(
        id=26, ledger="Q247", concept="S1", tier="Set operations",
        title="Invoiced in a month nothing opened",
        prompt=(
            "Months in which at least one invoice was issued but NO work order"
            " was opened. Months are 'YYYY-MM'.\n\n"
            "Invoices trail the work that produced them, so this catches the"
            " tail end of the data set. Exactly one month qualifies.\n\n"
            "Return: month"
        ),
        solution=(
            "SELECT DISTINCT strftime('%Y-%m', issued_on) FROM invoices"
            " EXCEPT"
            " SELECT DISTINCT strftime('%Y-%m', opened_at) FROM work_orders"
        ),
        trap_sql=(
            "SELECT DISTINCT strftime('%Y-%m', opened_at) FROM work_orders"
            " EXCEPT"
            " SELECT DISTINCT strftime('%Y-%m', issued_on) FROM invoices"
        ),
        note="EXCEPT is directional: A EXCEPT B is what is in A and not in B,"
             " and swapping the two asks the opposite question. Here the swap"
             " asks which months opened work but issued no invoice, and the"
             " answer is none -- an empty result, which is easy to mistake for"
             " 'my query is broken' rather than 'I asked it backwards'.",
        claims=[
            ("exactly one month, and it is later than every work order",
             lambda rows, c: len(rows) == 1
             and rows[0][0] > c.execute(
                 "SELECT MAX(strftime('%Y-%m', opened_at))"
                 " FROM work_orders").fetchone()[0]),
        ],
    ),
    dict(
        id=27, ledger="Q248", concept="S1", tier="Set operations",
        title="Low on stock and needed for critical work",
        prompt=(
            "Parts that are BOTH below their reorder level in at least one"
            " depot AND have been used on at least one critical work order.\n\n"
            "Only stock lines that actually have a reorder_level count. Three"
            " parts satisfy both conditions.\n\n"
            "Return: part_id, name"
        ),
        solution=(
            "SELECT p.part_id, p.name FROM parts p WHERE p.part_id IN ("
            " SELECT part_id FROM part_stock WHERE reorder_level IS NOT NULL"
            " AND quantity_on_hand < reorder_level"
            " INTERSECT"
            " SELECT pu.part_id FROM parts_used pu JOIN work_orders w"
            " ON w.work_order_id = pu.work_order_id"
            " WHERE w.priority = 'critical')"
        ),
        trap_sql=(
            "SELECT p.part_id, p.name FROM parts p WHERE p.part_id IN ("
            " SELECT part_id FROM part_stock WHERE reorder_level IS NOT NULL"
            " AND quantity_on_hand < reorder_level"
            " UNION"
            " SELECT pu.part_id FROM parts_used pu JOIN work_orders w"
            " ON w.work_order_id = pu.work_order_id"
            " WHERE w.priority = 'critical')"
        ),
        note="INTERSECT keeps rows present in BOTH sides; UNION keeps rows"
             " present in EITHER. 'And' in English means INTERSECT here even"
             " though the sentence has an 'and' in it, which is the usual place"
             " this goes wrong. Both operators dedupe, so neither needs a"
             " DISTINCT of its own.",
        claims=[
            ("three parts, and each is genuinely low somewhere",
             lambda rows, c: len(rows) == 3 and all(
                 c.execute("SELECT COUNT(*) FROM part_stock WHERE part_id = ?"
                           " AND reorder_level IS NOT NULL AND"
                           " quantity_on_hand < reorder_level",
                           (r[0],)).fetchone()[0] > 0 for r in rows)),
        ],
    ),
    # -------------------------------------------------------------- grain
    dict(
        id=28, ledger="Q249", concept="C2", tier="Grain",
        title="Parts and labour on the critical jobs",
        prompt=(
            "One row per CRITICAL work order, with what was spent on parts and"
            " what was spent on labour.\n\n"
            "Parts spend is quantity * unit_price * (1 - discount) summed;"
            " labour is hours * rate summed. A job with none of one or the"
            " other shows 0, not NULL. All 21 critical work orders appear.\n\n"
            "Return: work_order_id, parts_cost, labour_cost"
        ),
        solution=(
            "SELECT w.work_order_id,"
            " ROUND(COALESCE((SELECT SUM(quantity * unit_price *"
            " (1 - discount)) FROM parts_used pu"
            " WHERE pu.work_order_id = w.work_order_id), 0), 2),"
            " ROUND(COALESCE((SELECT SUM(hours * rate) FROM labor_entries le"
            " WHERE le.work_order_id = w.work_order_id), 0), 2)"
            " FROM work_orders w WHERE w.priority = 'critical'"
        ),
        trap_sql=(
            "SELECT w.work_order_id,"
            " ROUND(SUM(pu.quantity * pu.unit_price * (1 - pu.discount)), 2),"
            " ROUND(SUM(le.hours * le.rate), 2) FROM work_orders w"
            " LEFT JOIN parts_used pu ON pu.work_order_id = w.work_order_id"
            " LEFT JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " WHERE w.priority = 'critical' GROUP BY 1"
        ),
        note="Joining two child tables to the same parent multiplies them: a"
             " job with 3 part lines and 4 labour entries produces 12 rows, and"
             " both sums are inflated fourfold and threefold respectively. Two"
             " independent measures want two independent subqueries (or two"
             " separate CTEs joined back), never one join with both.",
        claims=[
            ("all 21 critical work orders, none NULL",
             lambda rows, c: len(rows) == 21
             and all(r[1] is not None and r[2] is not None for r in rows)),
            ("the parts total matches a straight sum over the critical jobs",
             lambda rows, c: abs(sum(r[1] for r in rows) - c.execute(
                 "SELECT COALESCE(SUM(pu.quantity * pu.unit_price *"
                 " (1 - pu.discount)), 0) FROM parts_used pu JOIN work_orders w"
                 " ON w.work_order_id = pu.work_order_id"
                 " WHERE w.priority = 'critical'").fetchone()[0]) < 0.5),
        ],
    ),
    dict(
        id=29, ledger="Q250", concept="C2", tier="Grain",
        title="Spend by part category",
        prompt=(
            "One row per part category that has ever been used, with the total"
            " spent on it.\n\n"
            "Each parts_used line is worth quantity * unit_price *"
            " (1 - discount), and every line must be priced on its own"
            " quantity, price and discount.\n\n"
            "Return: category, spend"
        ),
        solution=(
            "SELECT p.category, ROUND(SUM(pu.quantity * pu.unit_price *"
            " (1 - pu.discount)), 2) FROM parts_used pu"
            " JOIN parts p ON p.part_id = pu.part_id GROUP BY 1"
        ),
        trap_sql=(
            "SELECT p.category, ROUND(SUM(pu.quantity) * AVG(pu.unit_price) *"
            " (1 - AVG(pu.discount)), 2) FROM parts_used pu"
            " JOIN parts p ON p.part_id = pu.part_id GROUP BY 1"
        ),
        note="Do the arithmetic inside the aggregate, one row at a time, then"
             " add up: SUM(a * b), not SUM(a) * AVG(b). The two only agree if"
             " every row has the same price and discount, which is never true"
             " here -- an expensive part bought once and a cheap one bought"
             " fifty times get averaged into a price neither of them has.",
        claims=[
            ("nine categories, and the total matches the whole table",
             lambda rows, c: len(rows) == 9 and abs(
                 sum(r[1] for r in rows) - c.execute(
                     "SELECT SUM(quantity * unit_price * (1 - discount))"
                     " FROM parts_used").fetchone()[0]) < 0.5),
        ],
    ),
    # ------------------------------------------------------------ general
    dict(
        id=30, ledger="Q251", concept="general", tier="General",
        title="Machines by age band",
        prompt=(
            "Put every machine into one of three bands by installed_on and"
            " count them:\n"
            "  '2024 or later'  installed on or after 2024-01-01\n"
            "  '2021 to 2023'   installed on or after 2021-01-01\n"
            "  'before 2021'    everything else\n\n"
            "All 98 machines land in exactly one band.\n\n"
            "Return: band, machines"
        ),
        solution=(
            "SELECT CASE WHEN installed_on >= '2024-01-01' THEN '2024 or later'"
            " WHEN installed_on >= '2021-01-01' THEN '2021 to 2023'"
            " ELSE 'before 2021' END, COUNT(*) FROM machines GROUP BY 1"
        ),
        trap_sql=(
            "SELECT CASE WHEN installed_on >= '2021-01-01' THEN '2021 to 2023'"
            " WHEN installed_on >= '2024-01-01' THEN '2024 or later'"
            " ELSE 'before 2021' END, COUNT(*) FROM machines GROUP BY 1"
        ),
        note="CASE is first-match-wins, so the order of the WHEN branches is"
             " part of the logic, not a matter of taste. Test the narrowest"
             " band first. Put the 2021 test ahead of the 2024 test and every"
             " recent machine matches it on the way past -- the '2024 or later'"
             " branch is unreachable and never appears at all.",
        claims=[
            ("three bands covering all 98 machines",
             lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 98),
        ],
    ),
]

BY_ID = {ex["id"]: ex for ex in EXERCISES}
TIERS = list(dict.fromkeys(ex["tier"] for ex in EXERCISES))


def normalise(rows):
    """Canonical form for comparison: floats rounded, rows sorted, order ignored."""
    out = []
    for row in rows:
        out.append(tuple(
            round(v, 2) if isinstance(v, float) else v
            for v in row
        ))
    # Sort by a string key so mixed types and None never blow up the comparison.
    return sorted(out, key=lambda r: [(v is None, str(v)) for v in r])


def compare(user_rows, expected_rows):
    """Return (passed, message) describing how the two result sets line up."""
    got, want = normalise(user_rows), normalise(expected_rows)

    if got == want:
        return True, f"Correct - {len(want)} row(s) matched."

    if not user_rows:
        return False, f"Your query returned no rows; expected {len(want)}."

    got_cols = len(got[0]) if got else 0
    want_cols = len(want[0]) if want else 0
    if got_cols != want_cols:
        return False, (f"Wrong number of columns: you returned {got_cols}, "
                       f"expected {want_cols}. Check the 'Return:' line in the question.")

    if len(got) != len(want):
        extra = len(got) - len(want)
        direction = f"{extra} too many" if extra > 0 else f"{-extra} too few"
        return False, (f"Wrong number of rows: you returned {len(got)}, "
                       f"expected {len(want)} ({direction}).")

    missing = [r for r in want if r not in got]
    unexpected = [r for r in got if r not in want]
    detail = ""
    if missing:
        detail += f"\n  Expected but missing:  {missing[0]}"
    if unexpected:
        detail += f"\n  Returned but wrong:    {unexpected[0]}"
    return False, (f"Right row count ({len(got)}), but the values differ "
                   f"in {len(missing)} row(s).{detail}")
