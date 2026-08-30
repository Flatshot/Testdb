"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q162-Q191) run on the repair-depot schema, re-seeded
again (SEED 77 -> 113) so every row, name, date and amount differs from the last
set and no remembered answer value carries over.

The previous set gave recursion two questions and it was the tier that hurt.
This one spends six on it, ordered so the mechanism builds: carry a value down,
walk the chain upward, close the whole hierarchy into pairs, roll a subtree up
into a count, and then the half of recursion that is not a hierarchy at all --
generating rows that are not in any table, so a report can show the buckets and
months where nothing happened.

The rest keeps the breadth of the last set: set operations, correlated
subqueries, conditional aggregation, date arithmetic, window frames, self-joins,
grain, and NULLs. Two questions still drill the bare column under GROUP BY,
where SQLite silently samples one arbitrary row rather than raising an error.

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

EXERCISES = [
    # ---------------------------------------------------------- recursive CTEs
    dict(
        id=1, ledger="Q162", concept="R1", tier="Recursive CTEs",
        title="The whole chain, written out",
        prompt=(
            "For every technician, their reporting path from the very top down"
            " to them, as one string joined with ' > '.\n\n"
            "The technician at the top is just their own name. Everyone else is"
            " their supervisor's path with their own name on the end -- so a"
            " third-level technician shows all three names.\n\n"
            "Return: technician_id, name, path"
        ),
        solution=(
            "WITH RECURSIVE p AS ("
            " SELECT technician_id, name, name AS path FROM technicians"
            " WHERE supervisor_id IS NULL"
            " UNION ALL"
            " SELECT t.technician_id, t.name, p.path || ' > ' || t.name"
            " FROM technicians t JOIN p ON t.supervisor_id = p.technician_id)"
            " SELECT technician_id, name, path FROM p"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name,"
            " COALESCE(s.name || ' > ' || t.name, t.name)"
            " FROM technicians t"
            " LEFT JOIN technicians s ON s.technician_id = t.supervisor_id"
        ),
        note="The path is built by APPENDING to what the previous row already"
             " carried: p.path || ' > ' || t.name, not s.name || t.name. One"
             " self-join can only ever show two names, which is right for the"
             " second level and silently short for everyone below it.",
        claims=[
            ("every technician appears exactly once",
             lambda rows, c: len(rows) == c.execute(
                 "SELECT COUNT(*) FROM technicians").fetchone()[0]),
            ("the deepest path names three people",
             lambda rows, c: max(r[2].count(">") for r in rows) == 2),
        ],
    ),
    dict(
        id=2, ledger="Q163", concept="R1", tier="Recursive CTEs",
        title="Everyone above Nadia Kaur",
        prompt=(
            "Nadia Kaur and every technician above her in the reporting chain,"
            " up to the one who reports to nobody, with how many steps up each"
            " one is.\n\n"
            "Nadia herself is 0 steps, her supervisor is 1, and so on.\n\n"
            "Return: technician_id, name, steps_up"
        ),
        solution=(
            "WITH RECURSIVE up AS ("
            " SELECT technician_id, name, supervisor_id, 0 AS steps"
            " FROM technicians WHERE name = 'Nadia Kaur'"
            " UNION ALL"
            " SELECT s.technician_id, s.name, s.supervisor_id, up.steps + 1"
            " FROM technicians s JOIN up ON s.technician_id = up.supervisor_id)"
            " SELECT technician_id, name, steps FROM up"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, 0 FROM technicians t"
            " WHERE t.name = 'Nadia Kaur'"
            " UNION ALL"
            " SELECT s.technician_id, s.name, 1 FROM technicians t"
            " JOIN technicians s ON s.technician_id = t.supervisor_id"
            " WHERE t.name = 'Nadia Kaur'"
        ),
        note="Walking UP reverses the join: s.technician_id = up.supervisor_id,"
             " where walking down was t.supervisor_id = c.technician_id. Same"
             " machine, opposite direction. Adding one self-join per level works"
             " only while you know the depth, which is the thing recursion"
             " exists to stop you needing.",
        claims=[
            ("the chain above Nadia reaches the top in 2 steps",
             lambda rows, c: max(r[2] for r in rows) == 2 and len(rows) == 3),
        ],
    ),
    dict(
        id=3, ledger="Q164", concept="R1", tier="Recursive CTEs",
        title="Every manager, everyone under them",
        prompt=(
            "Every pair of technicians where the first supervises the second,"
            " directly or through any number of levels, with how many levels"
            " apart they are.\n\n"
            "A direct report is 1 level. Nobody is paired with themselves.\n\n"
            "Return: supervisor_id, subordinate_id, levels"
        ),
        solution=(
            "WITH RECURSIVE d AS ("
            " SELECT technician_id AS boss, technician_id AS sub, 0 AS levels"
            " FROM technicians"
            " UNION ALL"
            " SELECT d.boss, t.technician_id, d.levels + 1"
            " FROM technicians t JOIN d ON t.supervisor_id = d.sub)"
            " SELECT boss, sub, levels FROM d WHERE levels > 0"
        ),
        trap_sql=(
            "SELECT s.technician_id, t.technician_id, 1"
            " FROM technicians s JOIN technicians t"
            " ON t.supervisor_id = s.technician_id"
        ),
        note="This is the transitive closure: not just who reports to whom, but"
             " who is under whom at any distance. The anchor pairs everyone with"
             " THEMSELVES at level 0 so the step can extend from any starting"
             " point, and the 0-level rows are filtered out at the end. A plain"
             " self-join returns only the direct pairs.",
        claims=[
            ("indirect pairs exist, so the closure is larger than the direct set",
             lambda rows, c: len(rows) > c.execute(
                 "SELECT COUNT(*) FROM technicians WHERE supervisor_id IS NOT NULL"
             ).fetchone()[0]),
            ("no pair is more than 2 levels apart",
             lambda rows, c: max(r[2] for r in rows) == 2),
        ],
    ),
    dict(
        id=4, ledger="Q165", concept="R1", tier="Recursive CTEs",
        title="How many people are under you",
        prompt=(
            "For every technician, how many people sit below them in the chain"
            " at any depth -- their direct reports, plus those people's reports,"
            " and so on.\n\n"
            "Technicians who supervise nobody appear with 0.\n\n"
            "Return: technician_id, name, headcount_below"
        ),
        solution=(
            "WITH RECURSIVE d AS ("
            " SELECT technician_id AS boss, technician_id AS sub FROM technicians"
            " UNION ALL"
            " SELECT d.boss, t.technician_id"
            " FROM technicians t JOIN d ON t.supervisor_id = d.sub)"
            " SELECT t.technician_id, t.name, COUNT(d.sub) - 1"
            " FROM technicians t JOIN d ON d.boss = t.technician_id"
            " GROUP BY t.technician_id, t.name"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name,"
            " (SELECT COUNT(*) FROM technicians s"
            "  WHERE s.supervisor_id = t.technician_id)"
            " FROM technicians t"
        ),
        note="Counting direct reports is one join; counting everyone underneath"
             " is the closure. The '- 1' removes each technician's own 0-level"
             " row, which is also what makes the people who supervise nobody"
             " come out at 0 rather than dropping off the report entirely.",
        claims=[
            ("everyone appears, including those supervising nobody",
             lambda rows, c: len(rows) == c.execute(
                 "SELECT COUNT(*) FROM technicians").fetchone()[0]
             and sum(1 for r in rows if r[2] == 0) == 10),
            ("the person at the top has everyone else below them",
             lambda rows, c: max(r[2] for r in rows) == c.execute(
                 "SELECT COUNT(*) - 1 FROM technicians").fetchone()[0]),
        ],
    ),
    dict(
        id=5, ledger="Q166", concept="R2", tier="Recursive CTEs",
        title="Score bands, including the empty ones",
        prompt=(
            "Inspection scores bucketed into bands of ten -- 0-9, 10-19, and so"
            " on up to 90-99 -- with how many inspections fall in each band.\n\n"
            "All ten bands must appear, including the ones no inspection"
            " reached. Inspections with no score recorded belong to no band.\n\n"
            "Return: band_low, inspections"
        ),
        solution=(
            "WITH RECURSIVE b(lo) AS ("
            " SELECT 0 UNION ALL SELECT lo + 10 FROM b WHERE lo < 90)"
            " SELECT b.lo, COUNT(i.inspection_id) FROM b"
            " LEFT JOIN inspections i ON i.score >= b.lo AND i.score < b.lo + 10"
            " GROUP BY b.lo"
        ),
        trap_sql=(
            "SELECT (score / 10) * 10 AS lo, COUNT(*) FROM inspections"
            " WHERE score IS NOT NULL GROUP BY lo"
        ),
        note="A GROUP BY can only return bands the data already contains, so"
             " empty bands vanish and the report quietly claims they do not"
             " exist. Recursion here is not walking a hierarchy -- it is"
             " GENERATING rows that are in no table, which you then LEFT JOIN"
             " the real data onto.",
        claims=[
            ("all ten bands appear",
             lambda rows, c: len(rows) == 10),
            ("some bands are empty, so a plain GROUP BY would be short",
             lambda rows, c: sum(1 for r in rows if r[1] == 0) > 0),
            ("the counted inspections are exactly those with a score",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM inspections WHERE score IS NOT NULL"
             ).fetchone()[0]),
        ],
    ),
    dict(
        id=6, ledger="Q167", concept="R2", tier="Recursive CTEs",
        title="Critical months, including the quiet ones",
        prompt=(
            "For every calendar month from 2025-02 to 2026-07 inclusive, how"
            " many critical work orders were opened in it.\n\n"
            "Every month in that window appears, including the many where no"
            " critical job was opened at all -- those show 0.\n\n"
            "Return: month, critical_work_orders"
        ),
        solution=(
            "WITH RECURSIVE months(m) AS ("
            " SELECT '2025-02'"
            " UNION ALL"
            " SELECT strftime('%Y-%m', date(m || '-01', '+1 month'))"
            " FROM months WHERE m < '2026-07')"
            " SELECT months.m, COUNT(w.work_order_id) FROM months"
            " LEFT JOIN work_orders w"
            " ON strftime('%Y-%m', w.opened_at) = months.m"
            " AND w.priority = 'critical'"
            " GROUP BY months.m"
        ),
        trap_sql=(
            "SELECT strftime('%Y-%m', opened_at), COUNT(*) FROM work_orders"
            " WHERE priority = 'critical' GROUP BY 1"
        ),
        note="The step does date arithmetic on the value it just produced:"
             " date(m || '-01', '+1 month') rebuilds a real date, adds a month"
             " and reformats it, and the WHERE is what stops the loop. Filtering"
             " work_orders instead can only ever return months that HAVE a"
             " critical job -- the quiet months are the answer here, and they"
             " exist in no table.",
        claims=[
            ("the window is 18 months and all of them appear",
             lambda rows, c: len(rows) == 18),
            ("most months had no critical work order at all",
             lambda rows, c: sum(1 for r in rows if r[1] == 0) > len(rows) / 2),
        ],
    ),

    # ------------------------------------------------------- set operations
    dict(
        id=7, ledger="Q168", concept="S1", tier="Set operations",
        title="Stocked in Leeds, not in Coventry",
        prompt=(
            "Parts that Leeds Central holds a stock line for and Coventry Hub"
            " does not.\n\n"
            "This compares two SETS of parts. A part stocked at both depots must"
            " not appear, and it makes no difference how many are on hand.\n\n"
            "Return: part_id, name"
        ),
        solution=(
            "SELECT p.part_id, p.name FROM parts p WHERE p.part_id IN ("
            " SELECT s.part_id FROM part_stock s JOIN depots d"
            " ON d.depot_id = s.depot_id WHERE d.name = 'Leeds Central'"
            " EXCEPT"
            " SELECT s.part_id FROM part_stock s JOIN depots d"
            " ON d.depot_id = s.depot_id WHERE d.name = 'Coventry Hub')"
        ),
        trap_sql=(
            "SELECT DISTINCT p.part_id, p.name FROM parts p"
            " JOIN part_stock s ON s.part_id = p.part_id"
            " JOIN depots d ON d.depot_id = s.depot_id"
            " WHERE d.name = 'Leeds Central' AND d.name <> 'Coventry Hub'"
        ),
        note="A stock line names one depot, so 'Leeds AND not Coventry' on the"
             " same row is just 'Leeds' -- the second test never removes"
             " anything. Excluding parts that appear in ANOTHER set is a set"
             " difference: EXCEPT, or NOT EXISTS.",
    ),
    dict(
        id=8, ledger="Q169", concept="S1", tier="Set operations",
        title="Both kinds of contract",
        prompt=(
            "Customers who hold at least one contract that agreed a response"
            " time and at least one that did not.\n\n"
            "Return: customer_id, name"
        ),
        solution=(
            "SELECT c.customer_id, c.name FROM customers c WHERE c.customer_id IN ("
            " SELECT customer_id FROM contracts WHERE response_hours IS NOT NULL"
            " INTERSECT"
            " SELECT customer_id FROM contracts WHERE response_hours IS NULL)"
        ),
        trap_sql=(
            "SELECT DISTINCT c.customer_id, c.name FROM customers c"
            " JOIN contracts k ON k.customer_id = c.customer_id"
            " WHERE k.response_hours IS NOT NULL AND k.response_hours IS NULL"
        ),
        note="One contract row cannot be both, so testing both conditions on a"
             " single row returns nothing. The customer is what has to satisfy"
             " both, which means intersecting two sets of customer ids -- or two"
             " EXISTS clauses.",
        claims=[
            ("some customers hold both kinds",
             lambda rows, c: len(rows) > 0),
        ],
    ),
    # --------------------------------------------------- subqueries & EXISTS
    dict(
        id=9, ledger="Q170", concept="X1", tier="Subqueries & EXISTS",
        title="Machines nobody has touched",
        prompt=(
            "Machines that have never had a work order raised against them,"
            " with the site they stand on.\n\n"
            "Return: machine_id, model, site_name"
        ),
        solution=(
            "SELECT m.machine_id, m.model, s.name FROM machines m"
            " JOIN sites s ON s.site_id = m.site_id"
            " WHERE NOT EXISTS (SELECT 1 FROM work_orders w"
            " WHERE w.machine_id = m.machine_id)"
        ),
        trap_sql=(
            "SELECT m.machine_id, m.model, s.name FROM machines m"
            " JOIN sites s ON s.site_id = m.site_id"
            " LEFT JOIN work_orders w ON w.machine_id = m.machine_id"
        ),
        note="A LEFT JOIN keeps the unmatched machines but keeps every matched"
             " one too, and multiplies machines that have several work orders."
             " The anti-join needs its WHERE w.machine_id IS NULL; NOT EXISTS"
             " says the same thing without the risk of forgetting it.",
        claims=[
            ("some machines have never been worked on",
             lambda rows, c: len(rows) > 0 and len(rows) < c.execute(
                 "SELECT COUNT(*) FROM machines").fetchone()[0]),
        ],
    ),
    dict(
        id=10, ledger="Q171", concept="X1", tier="Subqueries & EXISTS",
        title="Never failed an inspection",
        prompt=(
            "Machines that have been inspected at least once and passed every"
            " time -- no 'fail' and no 'conditional' among their"
            " inspections.\n\n"
            "Machines never inspected at all do not qualify.\n\n"
            "Return: machine_id, model"
        ),
        solution=(
            "SELECT m.machine_id, m.model FROM machines m"
            " WHERE EXISTS (SELECT 1 FROM work_orders w"
            "   JOIN inspections i ON i.work_order_id = w.work_order_id"
            "   WHERE w.machine_id = m.machine_id)"
            " AND NOT EXISTS (SELECT 1 FROM work_orders w"
            "   JOIN inspections i ON i.work_order_id = w.work_order_id"
            "   WHERE w.machine_id = m.machine_id AND i.result <> 'pass')"
        ),
        trap_sql=(
            "SELECT DISTINCT m.machine_id, m.model FROM machines m"
            " JOIN work_orders w ON w.machine_id = m.machine_id"
            " JOIN inspections i ON i.work_order_id = w.work_order_id"
            " WHERE i.result = 'pass'"
        ),
        note="'Has a passing inspection' and 'has only passing inspections' are"
             " different questions, and the join answers the first. Proving"
             " something about EVERY row means looking for a counterexample and"
             " finding none: NOT EXISTS over the rows that would break it.",
        claims=[
            ("the answer is smaller than the set with any passing inspection",
             lambda rows, c: len(rows) < c.execute(
                 "SELECT COUNT(DISTINCT m.machine_id) FROM machines m"
                 " JOIN work_orders w ON w.machine_id = m.machine_id"
                 " JOIN inspections i ON i.work_order_id = w.work_order_id"
                 " WHERE i.result = 'pass'").fetchone()[0]),
        ],
    ),
    dict(
        id=11, ledger="Q172", concept="X2", tier="Subqueries & EXISTS",
        title="Costlier than its category average",
        prompt=(
            "Parts whose unit cost is above the average unit cost of the parts"
            " in their OWN category -- not the average across all parts.\n\n"
            "Return: part_id, name, category, unit_cost"
        ),
        solution=(
            "SELECT p.part_id, p.name, p.category, p.unit_cost FROM parts p"
            " WHERE p.unit_cost > (SELECT AVG(q.unit_cost) FROM parts q"
            " WHERE q.category = p.category)"
        ),
        trap_sql=(
            "SELECT p.part_id, p.name, p.category, p.unit_cost FROM parts p"
            " WHERE p.unit_cost > (SELECT AVG(unit_cost) FROM parts)"
        ),
        note="Dropping the WHERE that ties the subquery to the outer row turns a"
             " correlated subquery into a single global number. It still runs"
             " and still returns plausible rows -- it just answers a different"
             " question, and no error tells you so.",
    ),
    # ---------------------------------------------- conditional aggregation
    dict(
        id=12, ledger="Q173", concept="A1", tier="Conditional aggregation",
        title="Counted and uncounted stock",
        prompt=(
            "For each depot: how many stock lines it holds, how many have ever"
            " been counted, and how many never have.\n\n"
            "The last two must add up to the first.\n\n"
            "Return: depot_id, name, stock_lines, counted, never_counted"
        ),
        solution=(
            "SELECT d.depot_id, d.name, COUNT(*),"
            " SUM(CASE WHEN s.last_counted_at IS NOT NULL THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN s.last_counted_at IS NULL THEN 1 ELSE 0 END)"
            " FROM depots d JOIN part_stock s ON s.depot_id = d.depot_id"
            " GROUP BY d.depot_id, d.name"
        ),
        trap_sql=(
            "SELECT d.depot_id, d.name, COUNT(*),"
            " COUNT(CASE WHEN s.last_counted_at IS NOT NULL THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN s.last_counted_at IS NULL THEN 1 ELSE 0 END)"
            " FROM depots d JOIN part_stock s ON s.depot_id = d.depot_id"
            " GROUP BY d.depot_id, d.name"
        ),
        note="COUNT counts non-NULL values, and 0 is not NULL -- so COUNT(CASE"
             " ... ELSE 0 END) counts every row in the group and both columns"
             " come back equal to the total. Use SUM(CASE ... THEN 1 ELSE 0 END)"
             " or COUNT(CASE ... THEN 1 END) with no ELSE.",
        claims=[
            ("the two counts add up to the total for every depot",
             lambda rows, c: all(r[3] + r[4] == r[2] for r in rows)),
            ("every depot has some of each",
             lambda rows, c: all(r[3] > 0 and r[4] > 0 for r in rows)),
        ],
    ),
    dict(
        id=13, ledger="Q174", concept="C9", tier="Conditional aggregation",
        title="Close rate by priority",
        prompt=(
            "For each priority: how many work orders carry it, how many of those"
            " are closed, and the closed share as a fraction between 0 and 1.\n\n"
            "Return: priority, work_orders, closed, close_rate"
        ),
        solution=(
            "SELECT priority, COUNT(*),"
            " SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)"
            " FROM work_orders GROUP BY priority"
        ),
        trap_sql=(
            "SELECT priority, COUNT(*),"
            " SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) / COUNT(*)"
            " FROM work_orders GROUP BY priority"
        ),
        note="Two integers divide to an integer in SQLite, so a share that"
             " should read 0.69 comes back as 0 -- and 0 is plausible enough to"
             " survive a glance. Multiply one side by 1.0, or CAST it, to force"
             " real division. The conditional count itself is the easy half.",
        claims=[
            ("every close rate is a genuine fraction, neither 0 nor 1",
             lambda rows, c: all(0 < r[3] < 1 for r in rows)),
        ],
    ),
    dict(
        id=14, ledger="Q175", concept="A1", tier="Conditional aggregation",
        title="Every status in one row",
        prompt=(
            "For each technician who has been assigned any work order: how many"
            " of their work orders are open, how many closed, and how many"
            " cancelled -- three counts on one row.\n\n"
            "A technician with none of a given status shows 0 for it.\n\n"
            "Return: technician_id, name, open, closed, cancelled"
        ),
        solution=(
            "SELECT t.technician_id, t.name,"
            " SUM(CASE WHEN w.status = 'open' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN w.status = 'closed' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN w.status = 'cancelled' THEN 1 ELSE 0 END)"
            " FROM technicians t JOIN work_orders w"
            " ON w.technician_id = t.technician_id"
            " GROUP BY t.technician_id, t.name"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name,"
            " CASE WHEN w.status = 'open' THEN COUNT(*) ELSE 0 END,"
            " CASE WHEN w.status = 'closed' THEN COUNT(*) ELSE 0 END,"
            " CASE WHEN w.status = 'cancelled' THEN COUNT(*) ELSE 0 END"
            " FROM technicians t JOIN work_orders w"
            " ON w.technician_id = t.technician_id"
            " GROUP BY t.technician_id, t.name"
        ),
        note="An aggregate in the THEN branch does not protect the WHEN test."
             " COUNT(*) runs over the whole group while 'w.status = open' is"
             " evaluated against one arbitrary row SQLite happened to scan. The"
             " condition belongs INSIDE the aggregate.",
        claims=[
            ("the three counts add up to each technician's work order total",
             lambda rows, c: all(
                 r[2] + r[3] + r[4] == c.execute(
                     "SELECT COUNT(*) FROM work_orders WHERE technician_id = ?",
                     (r[0],)).fetchone()[0] for r in rows)),
        ],
    ),
    # ------------------------------------------------------------ dates & gaps
    dict(
        id=15, ledger="Q176", concept="D1", tier="Dates & gaps",
        title="The jobs that dragged",
        prompt=(
            "Work orders that took more than 14 days to close, with how many"
            " days they took.\n\n"
            "Only jobs that actually closed count. The gap is closed_at minus"
            " opened_at, in days.\n\n"
            "Return: work_order_id, opened_at, closed_at, days_open"
        ),
        solution=(
            "SELECT work_order_id, opened_at, closed_at,"
            " julianday(closed_at) - julianday(opened_at)"
            " FROM work_orders WHERE closed_at IS NOT NULL"
            " AND julianday(closed_at) - julianday(opened_at) > 14"
        ),
        trap_sql=(
            "SELECT work_order_id, opened_at, closed_at,"
            " julianday(closed_at) - julianday(opened_at)"
            " FROM work_orders WHERE status = 'closed'"
            " AND closed_at - opened_at > 14"
        ),
        note="Subtracting two ISO date STRINGS does not measure days -- SQLite"
             " coerces '2025-06-14' to the number 2025 and the comparison"
             " becomes nonsense that still runs. julianday() turns a date into a"
             " number of days, which is what makes the arithmetic mean anything.",
        claims=[
            ("some jobs took longer than 14 days, but not most of them",
             lambda rows, c: 0 < len(rows) < c.execute(
                 "SELECT COUNT(*) FROM work_orders WHERE closed_at IS NOT NULL"
             ).fetchone()[0] / 2),
        ],
    ),
    dict(
        id=16, ledger="Q177", concept="D2", tier="Dates & gaps",
        title="Out of warranty when it broke",
        prompt=(
            "Work orders opened after the machine's warranty had already"
            " expired.\n\n"
            "Machines with no warranty date recorded are not known to be out of"
            " warranty, so they do not count.\n\n"
            "Return: work_order_id, machine_id, opened_at, warranty_until"
        ),
        solution=(
            "SELECT w.work_order_id, m.machine_id, w.opened_at, m.warranty_until"
            " FROM work_orders w JOIN machines m ON m.machine_id = w.machine_id"
            " WHERE m.warranty_until IS NOT NULL"
            " AND w.opened_at > m.warranty_until"
        ),
        trap_sql=(
            "SELECT w.work_order_id, m.machine_id, w.opened_at, m.warranty_until"
            " FROM work_orders w JOIN machines m ON m.machine_id = w.machine_id"
            " WHERE w.opened_at > m.warranty_until OR m.warranty_until IS NULL"
        ),
        note="An unrecorded warranty date is not evidence that the warranty had"
             " expired -- it is the absence of evidence, and OR IS NULL asserts"
             " something the data never said. Note the other half: opened_at >"
             " warranty_until already excludes those rows by itself, because any"
             " comparison with NULL is unknown rather than true. The IS NOT NULL"
             " is there to say so deliberately instead of by accident.",
        claims=[
            ("some machines have no warranty date at all",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM machines WHERE warranty_until IS NULL"
             ).fetchone()[0] > 0),
        ],
    ),
    dict(
        id=17, ledger="Q178", concept="D1", tier="Dates & gaps",
        title="How long invoices take to pay",
        prompt=(
            "Across the invoices that have been paid, the average number of days"
            " between being issued and being paid, and the longest such gap.\n\n"
            "Return: invoices_paid, avg_days_to_pay, max_days_to_pay"
        ),
        solution=(
            "SELECT COUNT(*),"
            " AVG(julianday(paid_on) - julianday(issued_on)),"
            " MAX(julianday(paid_on) - julianday(issued_on))"
            " FROM invoices WHERE paid_on IS NOT NULL"
        ),
        trap_sql=(
            "SELECT COUNT(*),"
            " AVG(julianday(paid_on) - julianday(issued_on)),"
            " MAX(julianday(paid_on) - julianday(issued_on))"
            " FROM invoices"
        ),
        note="AVG and MAX skip NULLs on their own, so those two columns come out"
             " right either way -- but COUNT(*) counts every invoice including"
             " the unpaid ones, so the row says the average was taken over more"
             " invoices than it was. Filter the population once, in WHERE, and"
             " every column then describes the same set.",
        claims=[
            ("not every invoice has been paid",
             lambda rows, c: rows[0][0] < c.execute(
                 "SELECT COUNT(*) FROM invoices").fetchone()[0]),
        ],
    ),
    # ------------------------------------------------------------ window frames
    dict(
        id=18, ledger="Q179", concept="W1", tier="Window frames",
        title="Invoiced so far this year",
        prompt=(
            "Invoice value per calendar month, with a running total that"
            " accumulates from the first month onwards.\n\n"
            "The running total on the last month equals the whole invoice"
            " book.\n\n"
            "Return: month, invoiced, running_total"
        ),
        solution=(
            "WITH m AS (SELECT strftime('%Y-%m', issued_on) AS mth,"
            " SUM(amount) AS total FROM invoices GROUP BY mth)"
            " SELECT mth, total, SUM(total) OVER (ORDER BY mth) FROM m"
        ),
        trap_sql=(
            "SELECT strftime('%Y-%m', issued_on) AS mth, SUM(amount),"
            " SUM(SUM(amount)) OVER () FROM invoices GROUP BY mth"
        ),
        note="An OVER clause with ORDER BY and no frame accumulates from the"
             " start of the partition to the current row, which is exactly a"
             " running total. Leave the ORDER BY out and the window covers every"
             " row, so the same number repeats down the column.",
        claims=[
            ("the last running total is the whole invoice book",
             lambda rows, c: abs(max(r[2] for r in rows) - c.execute(
                 "SELECT SUM(amount) FROM invoices").fetchone()[0]) < 0.01),
        ],
    ),
    dict(
        id=19, ledger="Q180", concept="C3", tier="Window frames",
        title="Ranked inside your own depot",
        prompt=(
            "Every technician who has logged labour, with their total hours and"
            " their rank by hours WITHIN their own depot -- the busiest"
            " technician at each depot is rank 1.\n\n"
            "Break ties on technician_id ascending.\n\n"
            "Return: depot_id, technician_id, name, hours, rank_in_depot"
        ),
        solution=(
            "WITH h AS (SELECT t.depot_id, t.technician_id, t.name,"
            " SUM(l.hours) AS hrs FROM technicians t"
            " JOIN labor_entries l ON l.technician_id = t.technician_id"
            " GROUP BY t.depot_id, t.technician_id, t.name)"
            " SELECT depot_id, technician_id, name, hrs,"
            " RANK() OVER (PARTITION BY depot_id ORDER BY hrs DESC, technician_id)"
            " FROM h"
        ),
        trap_sql=(
            "WITH h AS (SELECT t.depot_id, t.technician_id, t.name,"
            " SUM(l.hours) AS hrs FROM technicians t"
            " JOIN labor_entries l ON l.technician_id = t.technician_id"
            " GROUP BY t.depot_id, t.technician_id, t.name)"
            " SELECT depot_id, technician_id, name, hrs,"
            " RANK() OVER (ORDER BY hrs DESC, technician_id) FROM h"
        ),
        note="Without PARTITION BY the ranking runs across every technician in"
             " the company, so only one person anywhere gets rank 1. The"
             " partition is what makes 'within their own depot' mean anything.",
        claims=[
            ("every depot has a rank 1",
             lambda rows, c: len({r[0] for r in rows}) ==
             len({r[0] for r in rows if r[4] == 1})),
        ],
    ),
    dict(
        id=20, ledger="Q181", concept="C3", tier="Window frames",
        title="Share of the category",
        prompt=(
            "For each part that has ever been fitted: its total spend, and what"
            " fraction of its CATEGORY's total spend that represents, as a value"
            " between 0 and 1.\n\n"
            "Spend on a part is quantity * unit_price * (1 - discount), summed"
            " over every time it was fitted.\n\n"
            "Return: category, part_id, name, spend, share_of_category"
        ),
        solution=(
            "WITH s AS (SELECT p.category, p.part_id, p.name,"
            " SUM(u.quantity * u.unit_price * (1 - u.discount)) AS spend"
            " FROM parts p JOIN parts_used u ON u.part_id = p.part_id"
            " GROUP BY p.category, p.part_id, p.name)"
            " SELECT category, part_id, name, spend,"
            " spend / SUM(spend) OVER (PARTITION BY category) FROM s"
        ),
        trap_sql=(
            "WITH s AS (SELECT p.category, p.part_id, p.name,"
            " SUM(u.quantity * u.unit_price * (1 - u.discount)) AS spend"
            " FROM parts p JOIN parts_used u ON u.part_id = p.part_id"
            " GROUP BY p.category, p.part_id, p.name)"
            " SELECT category, part_id, name, spend,"
            " spend / SUM(spend) OVER () FROM s"
        ),
        note="A window aggregate with PARTITION BY gives every row its group's"
             " total WITHOUT collapsing the rows -- the thing a GROUP BY cannot"
             " do and a self-join to a totals subquery does the long way around."
             " Drop the partition and you divide by the company total instead.",
        claims=[
            ("the shares within each category add up to 1",
             lambda rows, c: all(
                 abs(sum(r[4] for r in rows if r[0] == cat) - 1.0) < 1e-9
                 for cat in {r[0] for r in rows})),
        ],
    ),
    dict(
        id=21, ledger="Q182", concept="W1", tier="Window frames",
        title="Against the best in the depot",
        prompt=(
            "Every technician who has logged labour, with their total hours, the"
            " highest total logged by anyone at their depot, and the difference"
            " between the two.\n\n"
            "The busiest technician at each depot shows a difference of 0.\n\n"
            "Return: depot_id, technician_id, name, hours, depot_best, behind_by"
        ),
        solution=(
            "WITH h AS (SELECT t.depot_id, t.technician_id, t.name,"
            " SUM(l.hours) AS hrs FROM technicians t"
            " JOIN labor_entries l ON l.technician_id = t.technician_id"
            " GROUP BY t.depot_id, t.technician_id, t.name)"
            " SELECT depot_id, technician_id, name, hrs,"
            " MAX(hrs) OVER (PARTITION BY depot_id),"
            " MAX(hrs) OVER (PARTITION BY depot_id) - hrs FROM h"
        ),
        trap_sql=(
            "WITH h AS (SELECT t.depot_id, t.technician_id, t.name,"
            " SUM(l.hours) AS hrs FROM technicians t"
            " JOIN labor_entries l ON l.technician_id = t.technician_id"
            " GROUP BY t.depot_id, t.technician_id, t.name)"
            " SELECT depot_id, technician_id, name, hrs,"
            " MAX(hrs) OVER (), MAX(hrs) OVER () - hrs FROM h"
        ),
        note="OVER () is a single window over every row, so the comparison"
             " silently becomes 'against the busiest technician in the company'"
             " and only one person anywhere shows 0. PARTITION BY is what scopes"
             " the peak to each depot. Watch the other direction too: adding"
             " ORDER BY to a window aggregate turns MAX into a RUNNING maximum,"
             " which is a third answer again.",
        claims=[
            ("each depot has exactly one technician level with its best",
             lambda rows, c: all(
                 sum(1 for r in rows if r[0] == d and r[5] == 0) == 1
                 for d in {r[0] for r in rows})),
        ],
    ),
    # ----------------------------------------------------------- silent sampling
    dict(
        id=22, ledger="Q183", concept="B1", tier="Silent sampling",
        title="What the labour cost each depot",
        prompt=(
            "For each depot, the total cost of all labour logged by the"
            " technicians based there.\n\n"
            "A visit costs hours * rate, and technicians are not all on the same"
            " rate.\n\n"
            "Return: depot_id, name, labour_cost"
        ),
        solution=(
            "SELECT d.depot_id, d.name, SUM(l.hours * l.rate)"
            " FROM depots d JOIN technicians t ON t.depot_id = d.depot_id"
            " JOIN labor_entries l ON l.technician_id = t.technician_id"
            " GROUP BY d.depot_id, d.name"
        ),
        trap_sql=(
            "SELECT d.depot_id, d.name, SUM(l.hours) * l.rate"
            " FROM depots d JOIN technicians t ON t.depot_id = d.depot_id"
            " JOIN labor_entries l ON l.technician_id = t.technician_id"
            " GROUP BY d.depot_id, d.name"
        ),
        note="SUM(hours) * rate totals the hours and then multiplies by ONE"
             " arbitrary row's rate -- a bare column under GROUP BY. It equals"
             " SUM(hours * rate) only when every rate in the group is identical,"
             " which is an assumption about the data, not about SQL. When a"
             " per-row expression feeds an aggregate, the arithmetic goes"
             " inside.",
        claims=[
            ("technicians are on many different rates, so the two forms diverge",
             lambda rows, c: c.execute(
                 "SELECT COUNT(DISTINCT rate) FROM labor_entries").fetchone()[0] > 1),
        ],
    ),
    dict(
        id=23, ledger="Q184", concept="B1", tier="Silent sampling",
        title="Spend by category, after discount",
        prompt=(
            "For each part category, the total spent on its parts across every"
            " work order.\n\n"
            "A line costs quantity * unit_price * (1 - discount), and lines are"
            " not all discounted the same.\n\n"
            "Return: category, spend"
        ),
        solution=(
            "SELECT p.category, SUM(u.quantity * u.unit_price * (1 - u.discount))"
            " FROM parts p JOIN parts_used u ON u.part_id = p.part_id"
            " GROUP BY p.category"
        ),
        trap_sql=(
            "SELECT p.category, SUM(u.quantity * u.unit_price) * (1 - u.discount)"
            " FROM parts p JOIN parts_used u ON u.part_id = p.part_id"
            " GROUP BY p.category"
        ),
        note="The same mistake as the depot labour question wearing different"
             " clothes: factoring the discount out of the sum applies one"
             " arbitrary row's discount to the whole category. Anything that"
             " varies per row has to stay inside the aggregate. Watch for it"
             " whenever a rate, a discount or a price sits next to a SUM.",
        claims=[
            ("more than one discount is in use, so the two forms diverge",
             lambda rows, c: c.execute(
                 "SELECT COUNT(DISTINCT discount) FROM parts_used").fetchone()[0] > 1),
        ],
    ),
    # ------------------------------------------------------------------ self-joins
    dict(
        id=24, ledger="Q185", concept="J1", tier="Self-joins",
        title="Same region, same tier",
        prompt=(
            "Every pair of customers in the same region holding the same account"
            " tier, with the region name and the tier.\n\n"
            "Each pair once, not twice, and nobody paired with themselves. List"
            " the lower customer_id first. Customers with no tier recorded do"
            " not pair up.\n\n"
            "Return: region_name, account_tier, customer_a, customer_b"
        ),
        solution=(
            "SELECT g.name, a.account_tier, a.name, b.name"
            " FROM customers a"
            " JOIN customers b ON b.region_id = a.region_id"
            " AND b.account_tier = a.account_tier"
            " AND b.customer_id > a.customer_id"
            " JOIN regions g ON g.region_id = a.region_id"
        ),
        trap_sql=(
            "SELECT g.name, a.account_tier, a.name, b.name"
            " FROM customers a"
            " JOIN customers b ON b.region_id = a.region_id"
            " AND b.account_tier = a.account_tier"
            " AND b.customer_id <> a.customer_id"
            " JOIN regions g ON g.region_id = a.region_id"
        ),
        note="'<>' keeps both (A, B) and (B, A), so every pair comes back twice."
             " '>' picks one of the two orderings and drops the other, which"
             " also rules out self-pairs for free. Note the untiered customers"
             " never appear: account_tier = account_tier is NULL, not true, when"
             " both sides are NULL.",
        claims=[
            ("untiered customers exist and are excluded",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM customers WHERE account_tier IS NULL"
             ).fetchone()[0] > 0),
        ],
    ),
    dict(
        id=25, ledger="Q186", concept="J1", tier="Self-joins",
        title="Same depot, same certification",
        prompt=(
            "Every pair of technicians working out of the same depot who hold"
            " the same certification level, with the depot name and that"
            " level.\n\n"
            "Each pair once. List the lower technician_id first.\n\n"
            "Return: depot_name, cert_level, technician_a, technician_b"
        ),
        solution=(
            "SELECT d.name, a.cert_level, a.name, b.name"
            " FROM technicians a"
            " JOIN technicians b ON b.depot_id = a.depot_id"
            " AND b.cert_level = a.cert_level"
            " AND b.technician_id > a.technician_id"
            " JOIN depots d ON d.depot_id = a.depot_id"
        ),
        trap_sql=(
            "SELECT d.name, a.cert_level, a.name, b.name"
            " FROM technicians a"
            " JOIN technicians b ON b.depot_id = a.depot_id"
            " AND b.cert_level IS NOT DISTINCT FROM a.cert_level"
            " AND b.technician_id > a.technician_id"
            " JOIN depots d ON d.depot_id = a.depot_id"
        ),
        note="IS NOT DISTINCT FROM treats two NULLs as a match, which pairs up"
             " the technicians whose certification is simply unrecorded as"
             " though they shared a level. '=' is the right operator here"
             " precisely because it refuses to match unknowns.",
        claims=[
            ("technicians with no certification recorded exist",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM technicians WHERE cert_level IS NULL"
             ).fetchone()[0] > 0),
        ],
    ),
    # ---------------------------------------------------------------------- grain
    dict(
        id=26, ledger="Q187", concept="C2", tier="Grain",
        title="Parts and labour on one job",
        prompt=(
            "For each closed work order that has both parts fitted and labour"
            " logged: the parts total, the labour total, and the two added"
            " together.\n\n"
            "Parts total is quantity * unit_price * (1 - discount) summed over"
            " the parts. Labour total is hours * rate summed over the visits.\n\n"
            "Return: work_order_id, parts_total, labour_total, job_total"
        ),
        solution=(
            "WITH p AS (SELECT work_order_id,"
            " SUM(quantity * unit_price * (1 - discount)) AS parts"
            " FROM parts_used GROUP BY work_order_id),"
            " l AS (SELECT work_order_id, SUM(hours * rate) AS labour"
            " FROM labor_entries GROUP BY work_order_id)"
            " SELECT w.work_order_id, p.parts, l.labour, p.parts + l.labour"
            " FROM work_orders w JOIN p ON p.work_order_id = w.work_order_id"
            " JOIN l ON l.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed'"
        ),
        trap_sql=(
            "SELECT w.work_order_id,"
            " SUM(u.quantity * u.unit_price * (1 - u.discount)),"
            " SUM(e.hours * e.rate),"
            " SUM(u.quantity * u.unit_price * (1 - u.discount))"
            " + SUM(e.hours * e.rate)"
            " FROM work_orders w"
            " JOIN parts_used u ON u.work_order_id = w.work_order_id"
            " JOIN labor_entries e ON e.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' GROUP BY w.work_order_id"
        ),
        note="Joining a job to BOTH its parts and its labour multiplies them"
             " together -- 3 parts and 4 visits become 12 rows, and every sum is"
             " inflated by the other table's row count. Aggregate each side to"
             " one row per job FIRST, then join the totals.",
        claims=[
            ("some jobs have several parts and several visits, so the fan-out is real",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM (SELECT w.work_order_id FROM work_orders w"
                 " JOIN parts_used u ON u.work_order_id = w.work_order_id"
                 " JOIN labor_entries e ON e.work_order_id = w.work_order_id"
                 " GROUP BY w.work_order_id"
                 " HAVING COUNT(DISTINCT u.part_id) > 1"
                 " AND COUNT(DISTINCT e.entry_id) > 1)").fetchone()[0] > 0),
        ],
    ),
    dict(
        id=27, ledger="Q188", concept="C2", tier="Grain",
        title="Contracts and sites per customer",
        prompt=(
            "For each customer: how many contracts they hold and how many sites"
            " they run.\n\n"
            "Only customers who have at least one of each.\n\n"
            "Return: customer_id, name, contracts, sites"
        ),
        solution=(
            "SELECT c.customer_id, c.name,"
            " (SELECT COUNT(*) FROM contracts k WHERE k.customer_id = c.customer_id),"
            " (SELECT COUNT(*) FROM sites s WHERE s.customer_id = c.customer_id)"
            " FROM customers c"
            " WHERE EXISTS (SELECT 1 FROM contracts k WHERE k.customer_id = c.customer_id)"
            " AND EXISTS (SELECT 1 FROM sites s WHERE s.customer_id = c.customer_id)"
        ),
        trap_sql=(
            "SELECT c.customer_id, c.name, COUNT(k.contract_id), COUNT(s.site_id)"
            " FROM customers c"
            " JOIN contracts k ON k.customer_id = c.customer_id"
            " JOIN sites s ON s.customer_id = c.customer_id"
            " GROUP BY c.customer_id, c.name"
        ),
        note="Two independent one-to-many joins off the same customer form a"
             " cross product: 3 contracts and 4 sites give 12 rows, and both"
             " counts read 12. COUNT(DISTINCT ...) patches the symptom; counting"
             " each side separately -- correlated subqueries, or two"
             " pre-aggregated CTEs -- removes the fan-out itself.",
        claims=[
            ("at least one customer has several of both, so the counts really diverge",
             lambda rows, c: any(r[2] > 1 and r[3] > 1 for r in rows)),
        ],
    ),
    # ---------------------------------------------------------------------- NULLs
    dict(
        id=28, ledger="Q189", concept="C7", tier="NULLs",
        title="Still running, or merely undated",
        prompt=(
            "For each account tier: how many contracts those customers hold, and"
            " how many of them have no end date recorded and so are still"
            " running.\n\n"
            "Customers who were never graded have no tier. That is a tier in its"
            " own right here and gets its own row.\n\n"
            "Return: account_tier, contracts, still_running"
        ),
        solution=(
            "SELECT c.account_tier, COUNT(*),"
            " SUM(CASE WHEN k.end_date IS NULL THEN 1 ELSE 0 END)"
            " FROM customers c JOIN contracts k ON k.customer_id = c.customer_id"
            " GROUP BY c.account_tier"
        ),
        trap_sql=(
            "SELECT c.account_tier, COUNT(*),"
            " SUM(CASE WHEN k.end_date = NULL THEN 1 ELSE 0 END)"
            " FROM customers c JOIN contracts k ON k.customer_id = c.customer_id"
            " WHERE c.account_tier IS NOT NULL"
            " GROUP BY c.account_tier"
        ),
        note="Two NULL mistakes in one query: '= NULL' is never true so the"
             " second column comes back all zeros, and filtering the untiered"
             " customers out deletes a whole category from the report. GROUP BY"
             " keeps the NULLs together as one group -- the one place SQL treats"
             " NULLs as equal to each other.",
        claims=[
            ("the untiered group is present and is not empty",
             lambda rows, c: any(r[0] is None and r[1] > 0 for r in rows)),
            ("open-ended contracts exist",
             lambda rows, c: sum(r[2] for r in rows) > 0),
        ],
    ),
    dict(
        id=29, ledger="Q190", concept="C7", tier="NULLs",
        title="Certified, uncertified, unknown",
        prompt=(
            "For each depot: how many technicians it has, how many have a"
            " certification level recorded, and the average of those levels.\n\n"
            "Technicians with no level recorded still count toward the"
            " headcount, and must not drag the average down.\n\n"
            "Return: depot_id, name, technicians, certified, avg_cert_level"
        ),
        solution=(
            "SELECT d.depot_id, d.name, COUNT(*), COUNT(t.cert_level),"
            " AVG(t.cert_level)"
            " FROM depots d JOIN technicians t ON t.depot_id = d.depot_id"
            " GROUP BY d.depot_id, d.name"
        ),
        trap_sql=(
            "SELECT d.depot_id, d.name, COUNT(*), COUNT(t.cert_level),"
            " SUM(COALESCE(t.cert_level, 0)) * 1.0 / COUNT(*)"
            " FROM depots d JOIN technicians t ON t.depot_id = d.depot_id"
            " GROUP BY d.depot_id, d.name"
        ),
        note="COALESCE(level, 0) turns 'we do not know' into 'zero', which is a"
             " claim the data never made, and dividing by the full headcount"
             " compounds it. AVG already ignores NULLs in both the sum and the"
             " divisor, and COUNT(column) already counts only the rows that have"
             " a value -- the behaviour you want is the default.",
        claims=[
            ("some depots have technicians with no level recorded",
             lambda rows, c: any(r[3] < r[2] for r in rows)),
        ],
    ),
    # -------------------------------------------------------------------- general
    dict(
        id=30, ledger="Q191", concept="general", tier="General",
        title="Money still owed, by region",
        prompt=(
            "For each region, the value of invoices that are not yet settled --"
            " status PENDING or OVERDUE -- and how many such invoices there"
            " are.\n\n"
            "An invoice belongs to the region of the site its machine stands"
            " on. Regions with nothing outstanding do not appear.\n\n"
            "Return: region_name, unsettled_invoices, unsettled_value"
        ),
        solution=(
            "SELECT g.name, COUNT(*), SUM(i.amount)"
            " FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines m ON m.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = m.site_id"
            " JOIN regions g ON g.region_id = s.region_id"
            " WHERE i.status IN ('PENDING', 'OVERDUE')"
            " GROUP BY g.region_id, g.name"
        ),
        trap_sql=(
            "SELECT g.name, COUNT(*), SUM(i.amount)"
            " FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines m ON m.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = m.site_id"
            " JOIN regions g ON g.region_id = s.region_id"
            " WHERE i.status <> 'PAID'"
            " GROUP BY g.region_id, g.name"
        ),
        note="'not PAID' quietly sweeps in the VOID invoices, which were"
             " cancelled and are owed by nobody. When a column has more than two"
             " states, listing the ones you mean is safer than excluding the one"
             " you do not -- the set of 'everything else' grows the moment"
             " someone adds a status.",
        claims=[
            ("VOID invoices exist, so 'not PAID' really is wider than intended",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM invoices WHERE status = 'VOID'"
             ).fetchone()[0] > 0),
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
