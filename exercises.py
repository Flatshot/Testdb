"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q132-Q161) run on the repair-depot schema with a
fresh data set. Where the previous set was weighted 15/30 toward grain, this one
moves into ground the earlier sets never touched -- set operations, recursive
CTEs, correlated subqueries, conditional aggregation, date arithmetic and gap
analysis, and the window frames beyond a plain running total. Grain drops to two
questions, kept only so the habit does not rot.

One thread is deliberately carried over: three questions drill the bare column
under GROUP BY, where SQLite silently samples one arbitrary row instead of
raising an error. That is the mistake still actively costing answers.

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
    # ------------------------------------------------------- set operations
    dict(
        id=1, ledger="Q132", concept="S1", tier="Set operations",
        title="Parts only the urgent jobs need",
        prompt=(
            "Parts that have been fitted on at least one 'critical' work order"
            " and never on a 'low' one.\n\n"
            "This is a comparison between two SETS of parts, not a filter on"
            " individual rows: a part used on both must not appear.\n\n"
            "Return: part_id, name, category"
        ),
        solution=(
            "SELECT p.part_id, p.name, p.category FROM parts p WHERE p.part_id IN ("
            " SELECT pu.part_id FROM parts_used pu"
            " JOIN work_orders w ON w.work_order_id = pu.work_order_id"
            " WHERE w.priority = 'critical'"
            " EXCEPT"
            " SELECT pu.part_id FROM parts_used pu"
            " JOIN work_orders w ON w.work_order_id = pu.work_order_id"
            " WHERE w.priority = 'low')"
        ),
        trap_sql=(
            "SELECT DISTINCT p.part_id, p.name, p.category FROM parts p"
            " JOIN parts_used pu ON pu.part_id = p.part_id"
            " JOIN work_orders w ON w.work_order_id = pu.work_order_id"
            " WHERE w.priority = 'critical' AND w.priority <> 'low'"
        ),
        note="A row is only ever one priority, so 'critical AND not low' is"
             " just 'critical' -- the second test does nothing. Excluding parts"
             " used elsewhere is a set difference: EXCEPT, or NOT EXISTS.",
    ),
    dict(
        id=2, ledger="Q133", concept="S1", tier="Set operations",
        title="Two kinds of orphan",
        prompt=(
            "One list of problem parts, each labelled with its problem:\n\n"
            "  'stocked but never fitted' -- held in a depot, never used\n"
            "  'fitted but stocked nowhere' -- used on jobs, held nowhere\n\n"
            "Parts that are neither stocked nor fitted have neither problem and"
            " must not appear.\n\n"
            "Return: part_id, name, issue"
        ),
        solution=(
            "SELECT p.part_id, p.name, 'stocked but never fitted' FROM parts p"
            " WHERE EXISTS (SELECT 1 FROM part_stock s WHERE s.part_id = p.part_id)"
            " AND NOT EXISTS (SELECT 1 FROM parts_used u WHERE u.part_id = p.part_id)"
            " UNION ALL"
            " SELECT p.part_id, p.name, 'fitted but stocked nowhere' FROM parts p"
            " WHERE EXISTS (SELECT 1 FROM parts_used u WHERE u.part_id = p.part_id)"
            " AND NOT EXISTS (SELECT 1 FROM part_stock s WHERE s.part_id = p.part_id)"
        ),
        trap_sql=(
            "SELECT p.part_id, p.name, 'stocked but never fitted' FROM parts p"
            " WHERE NOT EXISTS (SELECT 1 FROM parts_used u WHERE u.part_id = p.part_id)"
            " UNION ALL"
            " SELECT p.part_id, p.name, 'fitted but stocked nowhere' FROM parts p"
            " WHERE NOT EXISTS (SELECT 1 FROM part_stock s WHERE s.part_id = p.part_id)"
        ),
        note="Each half needs BOTH halves of its condition -- what the part has"
             " as well as what it lacks. Drop the positive test and a part that"
             " is neither stocked nor fitted lands in both lists, labelled two"
             " contradictory ways.",
        claims=[
            ("both problems occur, and neither list is empty",
             lambda rows, c: len({r[2] for r in rows}) == 2
             and all(sum(1 for x in rows if x[2] == lbl) > 0
                     for lbl in {r[2] for r in rows})),
            ("2 parts are neither stocked nor fitted and are excluded",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM parts p WHERE NOT EXISTS"
                 " (SELECT 1 FROM part_stock s WHERE s.part_id = p.part_id)"
                 " AND NOT EXISTS (SELECT 1 FROM parts_used u"
                 " WHERE u.part_id = p.part_id)").fetchone()[0] == 2
             and len(rows) == 5),
        ],
    ),
    dict(
        id=3, ledger="Q134", concept="S1", tier="Set operations",
        title="Everything that happened, by month",
        prompt=(
            "Depot activity per calendar month, counting two kinds of event"
            " together: every labour visit and every inspection.\n\n"
            "Two events on the same date are two events. A month with a visit"
            " and an inspection on the same day counts 2, not 1.\n\n"
            "Return: month, events"
        ),
        solution=(
            "SELECT substr(d, 1, 7) AS m, COUNT(*) FROM ("
            " SELECT work_date AS d FROM labor_entries"
            " UNION ALL"
            " SELECT inspected_at FROM inspections) GROUP BY m"
        ),
        trap_sql=(
            "SELECT substr(d, 1, 7) AS m, COUNT(*) FROM ("
            " SELECT work_date AS d FROM labor_entries"
            " UNION"
            " SELECT inspected_at FROM inspections) GROUP BY m"
        ),
        note="UNION removes duplicate rows; UNION ALL keeps them. Stacking"
             " event dates with UNION silently collapses every pair that shares"
             " a date into one event. UNION ALL is also the cheaper of the two,"
             " since it never has to sort.",
    ),
    # ------------------------------------------------------ recursive CTEs
    dict(
        id=4, ledger="Q135", concept="R1", tier="Recursive CTEs",
        title="How deep in the chain",
        prompt=(
            "Every technician with their depth in the reporting chain. The one"
            " technician who reports to nobody is depth 1, anyone reporting to"
            " them is depth 2, and so on.\n\n"
            "The chain here runs three levels deep, so a single self-join"
            " cannot reach the bottom.\n\n"
            "Return: technician_id, name, depth"
        ),
        solution=(
            "WITH RECURSIVE h(technician_id, name, depth) AS ("
            " SELECT technician_id, name, 1 FROM technicians"
            " WHERE supervisor_id IS NULL"
            " UNION ALL"
            " SELECT t.technician_id, t.name, h.depth + 1 FROM technicians t"
            " JOIN h ON t.supervisor_id = h.technician_id)"
            " SELECT technician_id, name, depth FROM h"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name,"
            " CASE WHEN t.supervisor_id IS NULL THEN 1 ELSE 2 END"
            " FROM technicians t"
        ),
        note="A recursive CTE has two halves joined by UNION ALL: the anchor"
             " (where the chain starts) and the recursive step, which joins the"
             " table back to the CTE itself. It stops when the step returns no"
             " new rows -- you never say how many levels there are.",
        claims=[
            ("the chain is exactly 3 levels deep",
             lambda rows, c: max(r[2] for r in rows) == 3),
            ("every technician appears exactly once",
             lambda rows, c: len(rows) == c.execute(
                 "SELECT COUNT(*) FROM technicians").fetchone()[0]),
        ],
    ),
    dict(
        id=5, ledger="Q136", concept="R1", tier="Recursive CTEs",
        title="Who is at the top of your chain",
        prompt=(
            "For every technician, the name of the person at the very top of"
            " their reporting chain -- not their immediate supervisor, but the"
            " one who reports to nobody.\n\n"
            "That person is their own top, so they appear with their own name.\n\n"
            "Return: technician_id, name, top_manager"
        ),
        solution=(
            "WITH RECURSIVE h(technician_id, name, top_manager) AS ("
            " SELECT technician_id, name, name FROM technicians"
            " WHERE supervisor_id IS NULL"
            " UNION ALL"
            " SELECT t.technician_id, t.name, h.top_manager FROM technicians t"
            " JOIN h ON t.supervisor_id = h.technician_id)"
            " SELECT technician_id, name, top_manager FROM h"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, COALESCE(s.name, t.name)"
            " FROM technicians t"
            " LEFT JOIN technicians s ON s.technician_id = t.supervisor_id"
        ),
        note="The trick is that the anchor row carries the answer and the"
             " recursive step just passes it down unchanged -- h.top_manager,"
             " not t.name. A single self-join gets the immediate supervisor,"
             " which is only the right answer at depth 2.",
    ),
    # --------------------------------------------------- subqueries & EXISTS
    dict(
        id=6, ledger="Q137", concept="X1", tier="Subqueries & EXISTS",
        title="Nobody reports to them",
        prompt=(
            "Technicians who supervise nobody, with the depot they work from.\n\n"
            "Watch out: supervisor_id is NULL for the one technician at the top"
            " of the chain, and that NULL is inside the set you are testing"
            " against.\n\n"
            "Return: technician_id, name, depot_name"
        ),
        solution=(
            "SELECT t.technician_id, t.name, d.name FROM technicians t"
            " JOIN depots d ON d.depot_id = t.depot_id"
            " WHERE NOT EXISTS (SELECT 1 FROM technicians s"
            " WHERE s.supervisor_id = t.technician_id)"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, d.name FROM technicians t"
            " JOIN depots d ON d.depot_id = t.depot_id"
            " WHERE t.technician_id NOT IN (SELECT supervisor_id FROM technicians)"
        ),
        note="NOT IN against a set containing NULL returns NOTHING -- ever."
             " 'x NOT IN (1, NULL)' asks whether x differs from every member,"
             " and comparing to NULL is unknown, so the whole test is unknown."
             " NOT EXISTS has no such problem.",
        claims=[
            ("10 technicians supervise nobody",
             lambda rows, c: len(rows) == 10),
        ],
    ),
    dict(
        id=7, ledger="Q138", concept="X1", tier="Subqueries & EXISTS",
        title="Above your own priority's average",
        prompt=(
            "Closed work orders whose labour cost is above the average labour"
            " cost of closed jobs at the SAME priority.\n\n"
            "Each job is measured against its own priority band, not against"
            " all jobs. Labour cost is hours * rate summed over the visits.\n\n"
            "Return: work_order_id, priority, labor_cost"
        ),
        solution=(
            "WITH l AS (SELECT w.work_order_id, w.priority,"
            " SUM(le.hours * le.rate) AS lc FROM work_orders w"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' GROUP BY w.work_order_id)"
            " SELECT work_order_id, priority, lc FROM l"
            " WHERE lc > (SELECT AVG(l2.lc) FROM l l2 WHERE l2.priority = l.priority)"
        ),
        trap_sql=(
            "WITH l AS (SELECT w.work_order_id, w.priority,"
            " SUM(le.hours * le.rate) AS lc FROM work_orders w"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' GROUP BY w.work_order_id)"
            " SELECT work_order_id, priority, lc FROM l"
            " WHERE lc > (SELECT AVG(lc) FROM l)"
        ),
        note="A correlated subquery references the outer row -- here"
             " l2.priority = l.priority -- so it is re-evaluated per row and"
             " gives a different threshold per band. Drop the correlation and"
             " you get one global average, which is a different question.",
    ),
    dict(
        id=8, ledger="Q139", concept="X1", tier="Subqueries & EXISTS",
        title="Customers with something overdue",
        prompt=(
            "Customers who have at least one OVERDUE invoice, with their"
            " region.\n\n"
            "One row per customer, however many overdue invoices they have."
            " An invoice reaches a customer through its work order, machine"
            " and site.\n\n"
            "Return: customer_id, name, region_name"
        ),
        solution=(
            "SELECT c.customer_id, c.name, r.name FROM customers c"
            " JOIN regions r ON r.region_id = c.region_id"
            " WHERE EXISTS (SELECT 1 FROM sites s"
            " JOIN machines m ON m.site_id = s.site_id"
            " JOIN work_orders w ON w.machine_id = m.machine_id"
            " JOIN invoices i ON i.work_order_id = w.work_order_id"
            " WHERE s.customer_id = c.customer_id AND i.status = 'OVERDUE')"
        ),
        trap_sql=(
            "SELECT c.customer_id, c.name, r.name FROM customers c"
            " JOIN regions r ON r.region_id = c.region_id"
            " JOIN sites s ON s.customer_id = c.customer_id"
            " JOIN machines m ON m.site_id = s.site_id"
            " JOIN work_orders w ON w.machine_id = m.machine_id"
            " JOIN invoices i ON i.work_order_id = w.work_order_id"
            " WHERE i.status = 'OVERDUE'"
        ),
        note="EXISTS asks a yes/no question and stops at the first match, so it"
             " cannot duplicate the outer row. A join answers 'how many' and"
             " returns one row per match -- fine if you wanted that, wrong when"
             " the question is 'which customers'.",
    ),
    # ------------------------------------------------ conditional aggregation
    dict(
        id=9, ledger="Q140", concept="A1", tier="Conditional aggregation",
        title="Stock policy at a glance",
        prompt=(
            "For each depot, three counts of its stock lines in one row: how"
            " many are below their reorder level, how many are at or above it,"
            " and how many have no reorder policy set at all.\n\n"
            "The three counts must add up to the depot's total stock lines.\n\n"
            "Return: depot_id, name, below, at_or_above, no_policy"
        ),
        solution=(
            "SELECT d.depot_id, d.name,"
            " SUM(CASE WHEN ps.reorder_level IS NOT NULL"
            " AND ps.quantity_on_hand < ps.reorder_level THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN ps.reorder_level IS NOT NULL"
            " AND ps.quantity_on_hand >= ps.reorder_level THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN ps.reorder_level IS NULL THEN 1 ELSE 0 END)"
            " FROM depots d JOIN part_stock ps ON ps.depot_id = d.depot_id"
            " GROUP BY d.depot_id"
        ),
        trap_sql=(
            "SELECT d.depot_id, d.name,"
            " COUNT(CASE WHEN ps.reorder_level IS NOT NULL"
            " AND ps.quantity_on_hand < ps.reorder_level THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN ps.reorder_level IS NOT NULL"
            " AND ps.quantity_on_hand >= ps.reorder_level THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN ps.reorder_level IS NULL THEN 1 ELSE 0 END)"
            " FROM depots d JOIN part_stock ps ON ps.depot_id = d.depot_id"
            " GROUP BY d.depot_id"
        ),
        note="COUNT counts non-NULL values, and 0 is not NULL -- so"
             " COUNT(CASE ... ELSE 0 END) counts every row in the group, three"
             " times over. Either SUM(CASE ... THEN 1 ELSE 0 END) or"
             " COUNT(CASE ... THEN 1 END) with no ELSE.",
        claims=[
            ("the three counts add up to each depot's stock lines",
             lambda rows, c: all(
                 r[2] + r[3] + r[4] == c.execute(
                     "SELECT COUNT(*) FROM part_stock WHERE depot_id = ?",
                     (r[0],)).fetchone()[0] for r in rows)),
        ],
    ),
    dict(
        id=10, ledger="Q141", concept="A1", tier="Conditional aggregation",
        title="Job status by priority, side by side",
        prompt=(
            "For each priority, how many work orders are open, how many closed"
            " and how many cancelled -- as three columns on one row per"
            " priority, not three rows.\n\n"
            "Return: priority, open_jobs, closed_jobs, cancelled_jobs"
        ),
        solution=(
            "SELECT priority,"
            " SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END)"
            " FROM work_orders GROUP BY priority"
        ),
        trap_sql=(
            "SELECT priority, COUNT(status = 'open'),"
            " COUNT(status = 'closed'), COUNT(status = 'cancelled')"
            " FROM work_orders GROUP BY priority"
        ),
        note="status = 'open' evaluates to 1 or 0, never NULL, so COUNT of it"
             " is just the row count -- the same number in all three columns."
             " The condition has to select what gets summed, not what gets"
             " counted.",
    ),
    dict(
        id=11, ledger="Q142", concept="A1", tier="Conditional aggregation",
        title="Critical hours versus the rest",
        prompt=(
            "For each technician who has logged labour: hours logged on"
            " critical work orders, and hours logged on everything else.\n\n"
            "Every technician who has logged anything appears, including those"
            " who have never touched a critical job -- they show 0.\n\n"
            "Return: technician_id, name, critical_hours, other_hours"
        ),
        solution=(
            "SELECT t.technician_id, t.name,"
            " SUM(CASE WHEN w.priority = 'critical' THEN le.hours ELSE 0 END),"
            " SUM(CASE WHEN w.priority <> 'critical' THEN le.hours ELSE 0 END)"
            " FROM technicians t"
            " JOIN labor_entries le ON le.technician_id = t.technician_id"
            " JOIN work_orders w ON w.work_order_id = le.work_order_id"
            " GROUP BY t.technician_id"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, SUM(le.hours), 0"
            " FROM technicians t"
            " JOIN labor_entries le ON le.technician_id = t.technician_id"
            " JOIN work_orders w ON w.work_order_id = le.work_order_id"
            " WHERE w.priority = 'critical'"
            " GROUP BY t.technician_id"
        ),
        note="Filtering in WHERE throws the other rows away before grouping, so"
             " the 'everything else' column cannot be computed and technicians"
             " with no critical work vanish. Conditional aggregation keeps"
             " every row and decides per row which column it lands in.",
    ),
    # ---------------------------------------------------------- dates & gaps
    dict(
        id=12, ledger="Q143", concept="D1", tier="Dates & gaps",
        title="Work opened by month",
        prompt=(
            "How many work orders were opened in each calendar month, across"
            " the whole data set.\n\n"
            "The data spans 18 distinct months, so 18 rows -- January 2025 and"
            " January 2026 are different months.\n\n"
            "Return: month, work_orders"
        ),
        solution=(
            "SELECT substr(opened_at, 1, 7), COUNT(*) FROM work_orders"
            " GROUP BY substr(opened_at, 1, 7)"
        ),
        trap_sql=(
            "SELECT strftime('%m', opened_at), COUNT(*) FROM work_orders"
            " GROUP BY strftime('%m', opened_at)"
        ),
        note="'%m' is the month NUMBER, so every January in the data set lands"
             " in one bucket and 18 months collapse into 12. Keep the year:"
             " substr(date, 1, 7), or strftime('%Y-%m', date).",
        claims=[
            ("the data spans 18 distinct months",
             lambda rows, c: len(rows) == 18),
        ],
    ),
    dict(
        id=13, ledger="Q144", concept="D1", tier="Dates & gaps",
        title="Days between callouts",
        prompt=(
            "For machines with at least 3 work orders: every work order except"
            " each machine's first, with the number of days since the previous"
            " work order ON THAT MACHINE.\n\n"
            "Order within a machine by opened_at, then work_order_id.\n\n"
            "Return: machine_id, work_order_id, opened_at, days_since_previous"
        ),
        solution=(
            "WITH g AS (SELECT machine_id, work_order_id, opened_at,"
            " julianday(opened_at) - julianday(LAG(opened_at) OVER"
            " (PARTITION BY machine_id ORDER BY opened_at, work_order_id))"
            " AS gap FROM work_orders WHERE machine_id IN"
            " (SELECT machine_id FROM work_orders GROUP BY machine_id"
            " HAVING COUNT(*) >= 3))"
            " SELECT machine_id, work_order_id, opened_at, gap FROM g"
            " WHERE gap IS NOT NULL"
        ),
        trap_sql=(
            "WITH g AS (SELECT machine_id, work_order_id, opened_at,"
            " julianday(opened_at) - julianday(LAG(opened_at) OVER"
            " (ORDER BY opened_at, work_order_id))"
            " AS gap FROM work_orders WHERE machine_id IN"
            " (SELECT machine_id FROM work_orders GROUP BY machine_id"
            " HAVING COUNT(*) >= 3))"
            " SELECT machine_id, work_order_id, opened_at, gap FROM g"
            " WHERE gap IS NOT NULL"
        ),
        note="Without PARTITION BY, LAG walks the whole result as one sequence,"
             " so the 'previous' row is whatever machine happens to sort before"
             " it. The partition is what makes 'previous on that machine' mean"
             " anything.",
        claims=[
            ("no gap is negative",
             lambda rows, c: all(r[3] >= 0 for r in rows)),
        ],
    ),
    dict(
        id=14, ledger="Q145", concept="D1", tier="Dates & gaps",
        title="Slow payers",
        prompt=(
            "Invoices that were paid more than 30 days after they were issued,"
            " with how many whole days they took.\n\n"
            "Unpaid invoices have paid_on NULL and are not late -- they are"
            " unresolved. Leave them out.\n\n"
            "Return: invoice_id, issued_on, paid_on, days_to_pay"
        ),
        solution=(
            "SELECT invoice_id, issued_on, paid_on,"
            " CAST(julianday(paid_on) - julianday(issued_on) AS INTEGER)"
            " FROM invoices WHERE paid_on IS NOT NULL"
            " AND julianday(paid_on) - julianday(issued_on) > 30"
        ),
        trap_sql=(
            "SELECT invoice_id, issued_on, paid_on, paid_on - issued_on"
            " FROM invoices WHERE paid_on IS NOT NULL"
            " AND paid_on - issued_on > 30"
        ),
        note="Dates are TEXT in SQLite. Subtracting one from another does not"
             " error -- it coerces both to numbers, so '2026-03-01' becomes"
             " 2026 and the difference is 0. Use julianday() for arithmetic;"
             " plain <, > comparisons on ISO dates are fine as strings.",
        claims=[
            ("every result took more than 30 days",
             lambda rows, c: all(r[3] > 30 for r in rows)),
        ],
    ),
    dict(
        id=15, ledger="Q146", concept="D1", tier="Dates & gaps",
        title="Month on month",
        prompt=(
            "Work orders opened per calendar month, with the change from the"
            " previous month -- this month's count minus last month's.\n\n"
            "The earliest month has no previous month, so its change is NULL.\n\n"
            "Return: month, work_orders, change_from_previous"
        ),
        solution=(
            "WITH m AS (SELECT substr(opened_at, 1, 7) AS mth, COUNT(*) AS n"
            " FROM work_orders GROUP BY substr(opened_at, 1, 7))"
            " SELECT mth, n, n - LAG(n) OVER (ORDER BY mth) FROM m"
        ),
        trap_sql=(
            "WITH m AS (SELECT substr(opened_at, 1, 7) AS mth, COUNT(*) AS n"
            " FROM work_orders GROUP BY substr(opened_at, 1, 7))"
            " SELECT mth, n, LAG(n) OVER (ORDER BY mth) - n FROM m"
        ),
        note="Aggregate first, then window over the result -- LAG needs one row"
             " per month to look back at. Mind the direction: 'change from"
             " previous' is current minus previous, and reversing it turns"
             " every rise into a fall.",
    ),
    # --------------------------------------------------------- window frames
    dict(
        id=16, ledger="Q147", concept="W1", tier="Window frames",
        title="Quartiles of workload",
        prompt=(
            "Technicians who have logged labour, split into 4 equal-sized"
            " groups by total hours logged -- the busiest quarter in group 1,"
            " the quietest in group 4.\n\n"
            "Order by hours descending, then technician_id, so the split is"
            " deterministic.\n\n"
            "Return: technician_id, name, total_hours, quartile"
        ),
        solution=(
            "WITH h AS (SELECT t.technician_id, t.name, SUM(le.hours) AS hrs"
            " FROM technicians t"
            " JOIN labor_entries le ON le.technician_id = t.technician_id"
            " GROUP BY t.technician_id)"
            " SELECT technician_id, name, hrs,"
            " NTILE(4) OVER (ORDER BY hrs DESC, technician_id) FROM h"
        ),
        trap_sql=(
            "WITH h AS (SELECT t.technician_id, t.name, SUM(le.hours) AS hrs"
            " FROM technicians t"
            " JOIN labor_entries le ON le.technician_id = t.technician_id"
            " GROUP BY t.technician_id)"
            " SELECT technician_id, name, hrs,"
            " RANK() OVER (ORDER BY hrs DESC, technician_id) FROM h"
        ),
        note="NTILE(n) distributes rows into n buckets as evenly as it can,"
             " putting the remainder in the earlier buckets. RANK numbers rows"
             " individually -- useful, but it answers 'what position' not"
             " 'which quarter'.",
        claims=[
            ("exactly 4 quartiles appear",
             lambda rows, c: sorted({r[3] for r in rows}) == [1, 2, 3, 4]),
        ],
    ),
    dict(
        id=17, ledger="Q148", concept="W1", tier="Window frames",
        title="Three-month rolling average",
        prompt=(
            "Work orders opened per calendar month, with a rolling average"
            " over this month and the two before it.\n\n"
            "The first month's average is its own count; the second month's is"
            " the mean of two. From the third month on it is always three.\n\n"
            "Return: month, work_orders, rolling_avg_3"
        ),
        solution=(
            "WITH m AS (SELECT substr(opened_at, 1, 7) AS mth, COUNT(*) AS n"
            " FROM work_orders GROUP BY substr(opened_at, 1, 7))"
            " SELECT mth, n, AVG(n) OVER (ORDER BY mth"
            " ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) FROM m"
        ),
        trap_sql=(
            "WITH m AS (SELECT substr(opened_at, 1, 7) AS mth, COUNT(*) AS n"
            " FROM work_orders GROUP BY substr(opened_at, 1, 7))"
            " SELECT mth, n, AVG(n) OVER (ORDER BY mth) FROM m"
        ),
        note="An OVER clause with ORDER BY and no frame defaults to everything"
             " from the start up to the current row -- a running average over"
             " all history, which drifts further from the truth every month."
             " A fixed window needs ROWS BETWEEN n PRECEDING AND CURRENT ROW.",
    ),
    dict(
        id=18, ledger="Q149", concept="W1", tier="Window frames",
        title="The latest job on each machine",
        prompt=(
            "For every machine that has any work orders: the date and priority"
            " of its most recent one.\n\n"
            "Exactly one row per machine. Where two work orders share the"
            " latest date, take the higher work_order_id.\n\n"
            "Return: machine_id, opened_at, priority"
        ),
        solution=(
            "WITH r AS (SELECT machine_id, opened_at, priority,"
            " ROW_NUMBER() OVER (PARTITION BY machine_id"
            " ORDER BY opened_at DESC, work_order_id DESC) AS rn"
            " FROM work_orders)"
            " SELECT machine_id, opened_at, priority FROM r WHERE rn = 1"
        ),
        trap_sql=(
            "SELECT DISTINCT machine_id,"
            " LAST_VALUE(opened_at) OVER (PARTITION BY machine_id"
            " ORDER BY opened_at, work_order_id) AS last_open,"
            " LAST_VALUE(priority) OVER (PARTITION BY machine_id"
            " ORDER BY opened_at, work_order_id) AS last_pri"
            " FROM work_orders"
        ),
        note="LAST_VALUE with an ORDER BY and no frame sees only up to the"
             " current row, so it returns the current row's own value -- one"
             " row per work order, not per machine. It needs ROWS BETWEEN"
             " UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING to mean 'last'.",
    ),
    dict(
        id=19, ledger="Q150", concept="W1", tier="Window frames",
        title="Top two parts in each category",
        prompt=(
            "Within each part category, the 2 parts with the highest total"
            " spend across all work orders.\n\n"
            "Spend on a part is quantity * unit_price * (1 - discount), summed"
            " over every time it was fitted. Break ties on part_id ascending.\n\n"
            "Return: category, part_id, name, spend"
        ),
        solution=(
            "WITH s AS (SELECT p.category, p.part_id, p.name,"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount)) AS spend"
            " FROM parts p JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY p.part_id),"
            " r AS (SELECT category, part_id, name, spend, ROW_NUMBER() OVER"
            " (PARTITION BY category ORDER BY spend DESC, part_id) AS rn FROM s)"
            " SELECT category, part_id, name, spend FROM r WHERE rn <= 2"
        ),
        trap_sql=(
            "WITH s AS (SELECT p.category, p.part_id, p.name,"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount)) AS spend"
            " FROM parts p JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY p.part_id),"
            " r AS (SELECT category, part_id, name, spend, ROW_NUMBER() OVER"
            " (ORDER BY spend DESC, part_id) AS rn FROM s)"
            " SELECT category, part_id, name, spend FROM r WHERE rn <= 2"
        ),
        note="Top-N per group is ROW_NUMBER partitioned by the group, filtered"
             " outside the window -- you cannot put a window function in WHERE,"
             " which is why it needs the CTE. Without PARTITION BY you get the"
             " top 2 overall.",
    ),
    # -------------------------------------------------------- silent sampling
    dict(
        id=20, ledger="Q151", concept="B1", tier="Silent sampling",
        title="High scores per verdict",
        prompt=(
            "For each inspection result: how many inspections were recorded,"
            " and how many of them scored 80 or above.\n\n"
            "Inspections with no score recorded count toward the first number"
            " and not the second.\n\n"
            "Return: result, inspections, high_scores"
        ),
        solution=(
            "SELECT result, COUNT(*),"
            " SUM(CASE WHEN score >= 80 THEN 1 ELSE 0 END)"
            " FROM inspections GROUP BY result"
        ),
        trap_sql=(
            "SELECT result, COUNT(*),"
            " CASE WHEN score >= 80 THEN COUNT(*) ELSE 0 END"
            " FROM inspections GROUP BY result"
        ),
        note="The aggregate in the THEN branch does not protect the WHEN test."
             " COUNT runs over the group; 'score >= 80' runs against one"
             " arbitrary row SQLite picked. The condition belongs INSIDE the"
             " aggregate, not outside it.",
    ),
    dict(
        id=21, ledger="Q152", concept="B1", tier="Silent sampling",
        title="The newest site of each customer",
        prompt=(
            "For every customer: how many sites they have, and the city of"
            " their most recently added site -- the one with the highest"
            " site_id.\n\n"
            "Half the answers happen to match the customer's oldest site too,"
            " so checking a few rows will not tell you whether you are right.\n\n"
            "Return: customer_id, sites, newest_site_city"
        ),
        solution=(
            "WITH r AS (SELECT customer_id, city,"
            " ROW_NUMBER() OVER (PARTITION BY customer_id"
            " ORDER BY site_id DESC) AS rn,"
            " COUNT(*) OVER (PARTITION BY customer_id) AS n FROM sites)"
            " SELECT customer_id, n, city FROM r WHERE rn = 1"
        ),
        trap_sql=(
            "SELECT customer_id, COUNT(*), city FROM sites GROUP BY customer_id"
        ),
        note="A bare column beside an aggregate is not an error in SQLite -- it"
             " returns one arbitrary row's value. 'Arbitrary' in practice means"
             " the first row scanned, which here is the LOWEST site_id: right"
             " for every single-site customer and for half the rest, wrong the"
             " moment you actually needed it. Postgres and SQL Server reject"
             " the query outright.",
        claims=[
            ("most customers' newest and oldest site share a city, so a spot"
             " check will not catch the bug",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM (SELECT customer_id,"
                 " (SELECT city FROM sites x WHERE x.customer_id = s.customer_id"
                 "  ORDER BY site_id LIMIT 1) lo,"
                 " (SELECT city FROM sites x WHERE x.customer_id = s.customer_id"
                 "  ORDER BY site_id DESC LIMIT 1) hi"
                 " FROM sites s GROUP BY customer_id) WHERE lo = hi"
             ).fetchone()[0] >= len(rows) // 2),
        ],
    ),
    dict(
        id=22, ledger="Q153", concept="B1", tier="Silent sampling",
        title="Longest-serving technician per depot",
        prompt=(
            "For each depot: how many technicians are based there, and the name"
            " of the one hired earliest.\n\n"
            "Ties on hire date go to the lower technician_id.\n\n"
            "Return: depot_id, technicians, longest_serving"
        ),
        solution=(
            "WITH r AS (SELECT depot_id, name,"
            " ROW_NUMBER() OVER (PARTITION BY depot_id"
            " ORDER BY hired_on, technician_id) AS rn,"
            " COUNT(*) OVER (PARTITION BY depot_id) AS n FROM technicians)"
            " SELECT depot_id, n, name FROM r WHERE rn = 1"
        ),
        trap_sql=(
            "SELECT depot_id, COUNT(*), name FROM technicians"
            " GROUP BY depot_id"
        ),
        note="Pairing a value with the row that produced it needs ROW_NUMBER"
             " and a filter, or a join back on the winning key. SQLite has one"
             " narrow exception -- a query whose ONLY aggregate is MIN or MAX"
             " does take bare columns from the winning row -- but add a second"
             " aggregate, as here, and that guarantee is gone.",
    ),
    # -------------------------------------------------------------- self-joins
    dict(
        id=23, ledger="Q154", concept="J1", tier="Self-joins",
        title="Depot colleagues",
        prompt=(
            "Every pair of technicians who work out of the same depot, with the"
            " depot name.\n\n"
            "Each pair once, not twice, and nobody paired with themselves. List"
            " the lower technician_id first.\n\n"
            "Return: depot_name, technician_a, technician_b"
        ),
        solution=(
            "SELECT d.name, a.name, b.name FROM technicians a"
            " JOIN technicians b ON b.depot_id = a.depot_id"
            " AND b.technician_id > a.technician_id"
            " JOIN depots d ON d.depot_id = a.depot_id"
        ),
        trap_sql=(
            "SELECT d.name, a.name, b.name FROM technicians a"
            " JOIN technicians b ON b.depot_id = a.depot_id"
            " AND b.technician_id <> a.technician_id"
            " JOIN depots d ON d.depot_id = a.depot_id"
        ),
        note="'<>' keeps both (A, B) and (B, A) -- every pair twice. '>' picks"
             " one of the two orderings and drops the other, which also rules"
             " out self-pairs for free.",
        claims=[
            ("26 pairs share a depot",
             lambda rows, c: len(rows) == 26),
        ],
    ),
    dict(
        id=24, ledger="Q155", concept="J1", tier="Self-joins",
        title="Rival sites in one city",
        prompt=(
            "Pairs of sites in the same city that belong to DIFFERENT"
            " customers.\n\n"
            "Each pair once, lower site_id first. Two sites of the same"
            " customer in one city are not a pair.\n\n"
            "Return: city, site_a, site_b"
        ),
        solution=(
            "SELECT a.city, a.name, b.name FROM sites a"
            " JOIN sites b ON b.city = a.city AND b.site_id > a.site_id"
            " AND b.customer_id <> a.customer_id"
        ),
        trap_sql=(
            "SELECT a.city, a.name, b.name FROM sites a"
            " JOIN sites b ON b.city = a.city AND b.site_id > a.site_id"
        ),
        note="Every condition the question states has to reach the ON clause."
             " Dropping the customer test quietly includes a customer's own two"
             " sites in the same city, which is not a rivalry.",
    ),
    # ------------------------------------------------------------------ grain
    dict(
        id=25, ledger="Q156", concept="C2", tier="Grain",
        title="Parts and inspections on one job",
        prompt=(
            "Closed work orders that have both parts fitted and at least one"
            " inspection: the total parts cost and the number of"
            " inspections.\n\n"
            "Parts cost is quantity * unit_price * (1 - discount) summed over"
            " the job's parts.\n\n"
            "Return: work_order_id, parts_cost, inspections"
        ),
        solution=(
            "WITH p AS (SELECT work_order_id,"
            " SUM(quantity * unit_price * (1 - discount)) AS pc"
            " FROM parts_used GROUP BY work_order_id),"
            " i AS (SELECT work_order_id, COUNT(*) AS n FROM inspections"
            " GROUP BY work_order_id)"
            " SELECT w.work_order_id, p.pc, i.n FROM work_orders w"
            " JOIN p ON p.work_order_id = w.work_order_id"
            " JOIN i ON i.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed'"
        ),
        trap_sql=(
            "SELECT w.work_order_id,"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount)),"
            " COUNT(DISTINCT ins.inspection_id) FROM work_orders w"
            " JOIN parts_used pu ON pu.work_order_id = w.work_order_id"
            " JOIN inspections ins ON ins.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' GROUP BY w.work_order_id"
        ),
        note="Two children of the same parent multiply each other. DISTINCT"
             " rescues the count but there is no DISTINCT that can un-multiply"
             " a sum of money.",
    ),
    dict(
        id=26, ledger="Q157", concept="C2", tier="Grain",
        title="Regions, customers and depots",
        prompt=(
            "For each region: how many customers are based there and how many"
            " depots it has.\n\n"
            "One region has no depot at all and must show 0, not disappear.\n\n"
            "Return: region_id, name, customers, depots"
        ),
        solution=(
            "WITH c AS (SELECT region_id, COUNT(*) AS n FROM customers"
            " GROUP BY region_id),"
            " d AS (SELECT region_id, COUNT(*) AS n FROM depots"
            " GROUP BY region_id)"
            " SELECT r.region_id, r.name, c.n, COALESCE(d.n, 0) FROM regions r"
            " JOIN c ON c.region_id = r.region_id"
            " LEFT JOIN d ON d.region_id = r.region_id"
        ),
        trap_sql=(
            "SELECT r.region_id, r.name, COUNT(cu.customer_id),"
            " COUNT(dp.depot_id) FROM regions r"
            " JOIN customers cu ON cu.region_id = r.region_id"
            " LEFT JOIN depots dp ON dp.region_id = r.region_id"
            " GROUP BY r.region_id"
        ),
        note="Customers and depots both hang off the region, so joining both"
             " multiplies them together. Aggregate each side first, then join"
             " -- and COALESCE the outer side, because a region with no depot"
             " has no row to count.",
        claims=[
            ("one region has no depot",
             lambda rows, c: sum(1 for r in rows if r[3] == 0) == 1),
        ],
    ),
    # ------------------------------------------------------------------ NULLs
    dict(
        id=27, ledger="Q158", concept="C7", tier="NULLs",
        title="Expired, not merely unknown",
        prompt=(
            "Machines whose warranty ran out before 2026-01-01, with the model"
            " and the expiry date.\n\n"
            "A machine that was never registered for warranty has"
            " warranty_until NULL. An unknown expiry is not an expired one, so"
            " those must not appear.\n\n"
            "Return: machine_id, model, warranty_until"
        ),
        solution=(
            "SELECT machine_id, model, warranty_until FROM machines"
            " WHERE warranty_until < '2026-01-01'"
        ),
        trap_sql=(
            "SELECT machine_id, model, warranty_until FROM machines"
            " WHERE COALESCE(warranty_until, '1900-01-01') < '2026-01-01'"
        ),
        note="NULL < anything is unknown, not true, so unregistered machines"
             " drop out on their own -- the comparison already does the right"
             " thing. Coalescing to a very old date forces them in as though"
             " they were the most expired of all.",
        claims=[
            ("no result has a NULL expiry",
             lambda rows, c: all(r[2] is not None for r in rows)),
        ],
    ),
    dict(
        id=28, ledger="Q159", concept="C7", tier="NULLs",
        title="Response times by account tier",
        prompt=(
            "For each account tier: how many contracts those customers hold,"
            " how many of the contracts agreed a response time, and the average"
            " agreed response time.\n\n"
            "Some customers were never graded, so their tier is NULL. That is a"
            " tier in its own right here and gets its own row.\n\n"
            "Return: account_tier, contracts, with_sla, avg_response_hours"
        ),
        solution=(
            "SELECT c.account_tier, COUNT(*), COUNT(k.response_hours),"
            " AVG(k.response_hours) FROM customers c"
            " JOIN contracts k ON k.customer_id = c.customer_id"
            " GROUP BY c.account_tier"
        ),
        trap_sql=(
            "SELECT c.account_tier, COUNT(*), COUNT(k.response_hours),"
            " AVG(k.response_hours) FROM customers c"
            " JOIN contracts k ON k.customer_id = c.customer_id"
            " WHERE c.account_tier IS NOT NULL"
            " GROUP BY c.account_tier"
        ),
        note="GROUP BY puts all the NULLs together in one group rather than"
             " discarding them -- the one place SQL treats NULLs as equal to"
             " each other. Filtering them out first silently deletes a whole"
             " category from the report.",
        claims=[
            ("there is a NULL tier row",
             lambda rows, c: any(r[0] is None for r in rows)),
        ],
    ),
    # ---------------------------------------------------------------- general
    dict(
        id=29, ledger="Q160", concept="GEN", tier="General",
        title="Stock value by region",
        prompt=(
            "For each region that has a depot: how many depots it has, and the"
            " total value of stock held across them.\n\n"
            "A stock line's value is quantity_on_hand * the part's unit_cost.\n\n"
            "Return: region_name, depots, stock_value"
        ),
        solution=(
            "SELECT r.name, COUNT(DISTINCT d.depot_id),"
            " SUM(ps.quantity_on_hand * p.unit_cost) FROM regions r"
            " JOIN depots d ON d.region_id = r.region_id"
            " JOIN part_stock ps ON ps.depot_id = d.depot_id"
            " JOIN parts p ON p.part_id = ps.part_id"
            " GROUP BY r.region_id"
        ),
        trap_sql=(
            "SELECT r.name, COUNT(d.depot_id),"
            " SUM(ps.quantity_on_hand * p.unit_cost) FROM regions r"
            " JOIN depots d ON d.region_id = r.region_id"
            " JOIN part_stock ps ON ps.depot_id = d.depot_id"
            " JOIN parts p ON p.part_id = ps.part_id"
            " GROUP BY r.region_id"
        ),
        note="The stock join multiplies the depot rows, so a plain COUNT of"
             " depots reports the number of stock lines instead. The SUM is"
             " fine -- it is at the stock grain already -- so only the count"
             " needs DISTINCT.",
    ),
    dict(
        id=30, ledger="Q161", concept="GEN", tier="General",
        title="Oldest jobs still open",
        prompt=(
            "The 5 work orders that are still open and have been open longest,"
            " counting days up to 2026-07-20.\n\n"
            "Only status 'open' counts. Cancelled jobs also have closed_at"
            " NULL, but they are not open. Oldest first, then work_order_id"
            " ascending.\n\n"
            "Return: work_order_id, machine_id, opened_at, days_open"
        ),
        solution=(
            "SELECT work_order_id, machine_id, opened_at,"
            " CAST(julianday('2026-07-20') - julianday(opened_at) AS INTEGER)"
            " FROM work_orders WHERE status = 'open'"
            " ORDER BY opened_at ASC, work_order_id ASC LIMIT 5"
        ),
        trap_sql=(
            "SELECT work_order_id, machine_id, opened_at,"
            " CAST(julianday('2026-07-20') - julianday(opened_at) AS INTEGER)"
            " FROM work_orders WHERE closed_at IS NULL"
            " ORDER BY opened_at ASC, work_order_id ASC LIMIT 5"
        ),
        note="closed_at is NULL for cancelled jobs as well as open ones, so it"
             " cannot stand in for the status. Two different facts, two"
             " different columns -- the NULL tells you a job has no end date,"
             " not why.",
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
