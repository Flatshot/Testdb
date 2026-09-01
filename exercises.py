"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q192-Q221) run on the repair-depot schema, re-seeded
again (SEED 113 -> 149) so every row, name, date and amount differs from the
last set and no remembered answer value carries over.

This set was built from the mistakes made working through Q162-Q191, so it is
weighted half toward the things that actually went wrong and half toward
keeping breadth:

  grain               3  aggregating at the wrong level, or not at all
  inside the aggregate 2  SUM(a * b) rather than SUM(a) * b
  NULLs               2  a LEFT JOIN filtered in WHERE, AVG over missing values
  every vs any        2  proving something about ALL rows, and correlation
  recursion           6  branch labels, depth, ancestors, and three shapes of
                         generated row -- a spine, a per-row expansion, a grid

The other fifteen keep coverage across window frames, dates, set operations,
silent sampling and self-joins.

The six recursion questions deliberately vary the ANCHOR, which is where the
mechanism is easiest to get wrong: the root, the root's direct reports, every
row paired with itself, a literal, and one row per parent row.

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

ROOT = "(SELECT technician_id FROM technicians WHERE supervisor_id IS NULL)"

# The month spine every generated-row question reuses: 2025-02 to 2026-07, the
# full span of opened_at. Written once so a date change cannot drift between
# questions.
SPINE = ("WITH RECURSIVE m(mth) AS (SELECT '2025-02' UNION ALL"
         " SELECT strftime('%Y-%m', date(mth || '-01', '+1 month'))"
         " FROM m WHERE mth < '2026-07')")

EXERCISES = [
    # ------------------------------------------------------- recursive CTEs
    dict(
        id=1, ledger="Q192", concept="R1", tier="Recursive CTEs",
        title="Which branch of the company",
        prompt=(
            "Every technician except the one at the very top, with the name of"
            " the top-level manager whose branch they sit in.\n\n"
            "A top-level manager reports directly to the person at the top and"
            " heads their own branch, so they appear with their own name.\n\n"
            "Return: technician_id, name, branch_head"
        ),
        solution=(
            "WITH RECURSIVE br AS ("
            " SELECT technician_id, name, name AS branch FROM technicians"
            " WHERE supervisor_id = " + ROOT +
            " UNION ALL"
            " SELECT t.technician_id, t.name, b.branch FROM technicians t"
            " JOIN br b ON t.supervisor_id = b.technician_id)"
            " SELECT technician_id, name, branch FROM br"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, s.name FROM technicians t"
            " JOIN technicians s ON s.technician_id = t.supervisor_id"
            " WHERE t.supervisor_id IS NOT NULL"
        ),
        note="The anchor is NOT the root here -- it is the root's direct"
             " reports, each seeded with their own name, and everyone below"
             " inherits b.branch unchanged. A single self-join gives the"
             " immediate supervisor, which is right for the second level and"
             " wrong for everyone under it.",
        claims=[
            ("the root is excluded, leaving 13",
             lambda rows, c: len(rows) == 13),
            ("the three branch heads appear with their own name",
             lambda rows, c: sum(1 for r in rows if r[1] == r[2]) == 3),
        ],
    ),
    dict(
        id=2, ledger="Q193", concept="R1", tier="Recursive CTEs",
        title="How deep does your tree go",
        prompt=(
            "For every technician, how many levels of people sit below them --"
            " 1 if their deepest report is a direct one, 2 if someone reports"
            " to a direct report, and so on.\n\n"
            "Technicians who supervise nobody show 0.\n\n"
            "Return: technician_id, name, levels_below"
        ),
        solution=(
            "WITH RECURSIVE d AS ("
            " SELECT technician_id AS boss, technician_id AS sub, 0 AS lvl"
            " FROM technicians"
            " UNION ALL"
            " SELECT d.boss, t.technician_id, d.lvl + 1 FROM technicians t"
            " JOIN d ON t.supervisor_id = d.sub)"
            " SELECT t.technician_id, t.name, MAX(d.lvl) FROM technicians t"
            " JOIN d ON d.boss = t.technician_id"
            " GROUP BY t.technician_id, t.name"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, COUNT(s.technician_id)"
            " FROM technicians t LEFT JOIN technicians s"
            " ON s.supervisor_id = t.technician_id"
            " GROUP BY t.technician_id, t.name"
        ),
        note="Recursion ENUMERATES, aggregation SUMMARISES. The CTE produces"
             " one row per boss-and-subordinate pair carrying its distance;"
             " MAX over those rows answers 'how deep'. Counting direct reports"
             " answers a different question and cannot see past level 1.",
        claims=[
            ("the ten technicians who supervise nobody come out at 0",
             lambda rows, c: sum(1 for r in rows if r[2] == 0) == 10),
            ("the chain runs three levels, so the deepest value is 2",
             lambda rows, c: max(r[2] for r in rows) == 2),
        ],
    ),
    dict(
        id=3, ledger="Q194", concept="R1", tier="Recursive CTEs",
        title="What the people above you cost",
        prompt=(
            "For every technician, the total hourly rate of everyone above them"
            " in the reporting chain -- their supervisor, their supervisor's"
            " supervisor, and so on to the top.\n\n"
            "The technician at the top has nobody above them and shows 0.\n\n"
            "Return: technician_id, name, rate_above"
        ),
        solution=(
            "WITH RECURSIVE anc AS ("
            " SELECT technician_id AS who, supervisor_id AS aid FROM technicians"
            " WHERE supervisor_id IS NOT NULL"
            " UNION ALL"
            " SELECT a.who, t.supervisor_id FROM anc a"
            " JOIN technicians t ON t.technician_id = a.aid"
            " WHERE t.supervisor_id IS NOT NULL)"
            " SELECT t.technician_id, t.name, COALESCE(SUM(s.hourly_rate), 0)"
            " FROM technicians t LEFT JOIN anc a ON a.who = t.technician_id"
            " LEFT JOIN technicians s ON s.technician_id = a.aid"
            " GROUP BY t.technician_id, t.name"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, COALESCE(s.hourly_rate, 0)"
            " FROM technicians t"
            " LEFT JOIN technicians s ON s.technician_id = t.supervisor_id"
        ),
        note="Walking up collects a SET of ancestors, and the money is summed"
             " over that set afterwards -- the recursion enumerates, the SUM"
             " totals. One self-join reaches the immediate supervisor only,"
             " which is the whole answer at level 2 and short at level 3.",
        claims=[
            ("only the root has nobody above it",
             lambda rows, c: sum(1 for r in rows if r[2] == 0) == 1),
            ("the other thirteen all have someone above them",
             lambda rows, c: sum(1 for r in rows if r[2] > 0) == 13),
        ],
    ),
    dict(
        id=4, ledger="Q195", concept="R2", tier="Recursive CTEs",
        title="Jobs and invoices, month by month",
        prompt=(
            "For every calendar month from 2025-02 to 2026-07 inclusive, how"
            " many work orders were opened in it and how many invoices were"
            " issued in it.\n\n"
            "Every month in the window appears, including any where one or"
            " both counts are 0.\n\n"
            "Return: month, work_orders, invoices"
        ),
        solution=(
            SPINE +
            " SELECT m.mth,"
            " (SELECT COUNT(*) FROM work_orders w"
            "  WHERE strftime('%Y-%m', w.opened_at) = m.mth),"
            " (SELECT COUNT(*) FROM invoices i"
            "  WHERE strftime('%Y-%m', i.issued_on) = m.mth)"
            " FROM m"
        ),
        trap_sql=(
            SPINE +
            " SELECT m.mth, COUNT(w.work_order_id), COUNT(i.invoice_id) FROM m"
            " LEFT JOIN work_orders w ON strftime('%Y-%m', w.opened_at) = m.mth"
            " LEFT JOIN invoices i ON strftime('%Y-%m', i.issued_on) = m.mth"
            " GROUP BY m.mth"
        ),
        note="Two independent child tables joined to the same spine multiply"
             " each other -- a month with 12 jobs and 3 invoices produces 36"
             " rows and both counts come back inflated. Count each measure in"
             " its own subquery, or aggregate each one before joining.",
        claims=[
            ("every month in the window appears",
             lambda rows, c: len(rows) == 18),
            ("the job counts add up to every work order",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM work_orders").fetchone()[0]),
            ("the invoice counts add up to every invoice",
             lambda rows, c: sum(r[2] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM invoices").fetchone()[0]),
        ],
    ),
    dict(
        id=5, ledger="Q196", concept="R2", tier="Recursive CTEs",
        title="One row per month a contract ran",
        prompt=(
            "For every contract that has an end date, one row for each calendar"
            " month it was active -- from the month it started to the month it"
            " ended, inclusive.\n\n"
            "A contract that started and ended in the same month gets one row.\n\n"
            "Return: contract_id, month"
        ),
        solution=(
            "WITH RECURSIVE cm AS ("
            " SELECT contract_id, strftime('%Y-%m', start_date) AS mth,"
            " strftime('%Y-%m', end_date) AS last_m FROM contracts"
            " WHERE end_date IS NOT NULL"
            " UNION ALL"
            " SELECT contract_id,"
            " strftime('%Y-%m', date(mth || '-01', '+1 month')), last_m"
            " FROM cm WHERE mth < last_m)"
            " SELECT contract_id, mth FROM cm"
        ),
        trap_sql=(
            "SELECT contract_id, strftime('%Y-%m', start_date)"
            " FROM contracts WHERE end_date IS NOT NULL"
        ),
        note="The anchor here is not one row but one row PER CONTRACT, and each"
             " expands into its own series. The stop condition is per-row too:"
             " mth < last_m compares against a value the anchor carried in, so"
             " every contract halts at its own end date rather than a shared"
             " one.",
        claims=[
            ("every dated contract contributes at least one month",
             lambda rows, c: len({r[0] for r in rows}) == c.execute(
                 "SELECT COUNT(*) FROM contracts WHERE end_date IS NOT NULL"
             ).fetchone()[0]),
            ("contracts expand into many months, not one each",
             lambda rows, c: len(rows) > 2 * len({r[0] for r in rows})),
        ],
    ),
    dict(
        id=6, ledger="Q197", concept="R2", tier="Recursive CTEs",
        title="Every depot, every month",
        prompt=(
            "A full grid of depot and month: for each of the four depots and"
            " each calendar month from 2025-02 to 2026-07 inclusive, the labour"
            " hours logged by that depot's technicians.\n\n"
            "Every depot-and-month combination appears, including those with no"
            " hours at all -- those show 0.\n\n"
            "Return: depot_name, month, hours"
        ),
        solution=(
            SPINE +
            " SELECT d.name, m.mth, COALESCE(SUM(le.hours), 0) FROM m"
            " CROSS JOIN depots d"
            " LEFT JOIN technicians t ON t.depot_id = d.depot_id"
            " LEFT JOIN labor_entries le ON le.technician_id = t.technician_id"
            " AND strftime('%Y-%m', le.work_date) = m.mth"
            " GROUP BY d.name, m.mth"
        ),
        trap_sql=(
            "SELECT d.name, strftime('%Y-%m', le.work_date) mth, SUM(le.hours)"
            " FROM depots d JOIN technicians t ON t.depot_id = d.depot_id"
            " JOIN labor_entries le ON le.technician_id = t.technician_id"
            " GROUP BY d.name, mth"
        ),
        note="A generated series CROSS JOINed to a real dimension builds the"
             " whole grid before any data is attached. Grouping the labour"
             " table instead can only return combinations that already have"
             " hours, so the empty ones -- the reason to run the report -- are"
             " exactly what goes missing.",
        claims=[
            ("four depots times eighteen months",
             lambda rows, c: len(rows) == 72),
            ("some depot-months have no hours at all",
             lambda rows, c: sum(1 for r in rows if r[2] == 0) > 0),
            ("the hours add up to every labour entry",
             lambda rows, c: abs(sum(r[2] for r in rows) - c.execute(
                 "SELECT SUM(hours) FROM labor_entries").fetchone()[0]) < 0.01),
        ],
    ),
    # --------------------------------------------------------------- grain
    dict(
        id=7, ledger="Q198", concept="C2", tier="Grain",
        title="Machines and contracts per customer",
        prompt=(
            "For every customer: how many machines they have across all their"
            " sites, and how many contracts they hold.\n\n"
            "Customers with no machines or no contracts still appear, with 0.\n\n"
            "Return: customer_id, name, machines, contracts"
        ),
        solution=(
            "SELECT c.customer_id, c.name,"
            " (SELECT COUNT(*) FROM sites s JOIN machines mm ON mm.site_id = s.site_id"
            "  WHERE s.customer_id = c.customer_id),"
            " (SELECT COUNT(*) FROM contracts k WHERE k.customer_id = c.customer_id)"
            " FROM customers c"
        ),
        trap_sql=(
            "SELECT c.customer_id, c.name, COUNT(DISTINCT mm.machine_id),"
            " COUNT(k.contract_id)"
            " FROM customers c LEFT JOIN sites s ON s.customer_id = c.customer_id"
            " LEFT JOIN machines mm ON mm.site_id = s.site_id"
            " LEFT JOIN contracts k ON k.customer_id = c.customer_id"
            " GROUP BY c.customer_id, c.name"
        ),
        note="Machines hang off sites and contracts hang off the customer, so"
             " joining both fans one out by the other. DISTINCT rescues the"
             " machine count and quietly leaves the contract count multiplied"
             " by the number of machines -- half-fixing it is worse than not,"
             " because the surviving error looks deliberate.",
        claims=[
            ("every customer appears",
             lambda rows, c: len(rows) == 28),
            ("the machine counts total every machine on a customer site",
             lambda rows, c: sum(r[2] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM machines mm JOIN sites s"
                 " ON s.site_id = mm.site_id").fetchone()[0]),
            ("the contract counts total every contract",
             lambda rows, c: sum(r[3] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM contracts").fetchone()[0]),
        ],
    ),
    dict(
        id=8, ledger="Q199", concept="C2", tier="Grain",
        title="Average hours a job takes, by priority",
        prompt=(
            "For each priority, the average number of labour hours a work order"
            " takes -- total hours on the job, averaged across the jobs.\n\n"
            "Only jobs that have logged labour count.\n\n"
            "Return: priority, avg_hours"
        ),
        solution=(
            "WITH per_job AS (SELECT w.work_order_id, w.priority,"
            " SUM(le.hours) AS h FROM work_orders w"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " GROUP BY w.work_order_id, w.priority)"
            " SELECT priority, AVG(h) FROM per_job GROUP BY priority"
        ),
        trap_sql=(
            "SELECT w.priority, AVG(le.hours) FROM work_orders w"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " GROUP BY w.priority"
        ),
        note="Averaging labor_entries averages VISITS, not jobs -- a job with"
             " four visits pulls the mean four times and the answer comes back"
             " near the size of one visit. Roll up to one row per job first,"
             " then average those. The grain you average over decides what the"
             " number means.",
        claims=[
            ("all four priorities appear",
             lambda rows, c: len(rows) == 4),
            ("a job averages more hours than a single visit",
             lambda rows, c: min(r[1] for r in rows) > c.execute(
                 "SELECT AVG(hours) FROM labor_entries").fetchone()[0]),
        ],
    ),
    dict(
        id=9, ledger="Q200", concept="C2", tier="Grain",
        title="How many customers has each technician served",
        prompt=(
            "For every technician who has been assigned work, how many"
            " DIFFERENT customers they have worked for.\n\n"
            "A technician who did ten jobs for one customer has served one"
            " customer, not ten.\n\n"
            "Return: technician_id, name, customers"
        ),
        solution=(
            "SELECT t.technician_id, t.name, COUNT(DISTINCT s.customer_id)"
            " FROM technicians t"
            " JOIN work_orders w ON w.technician_id = t.technician_id"
            " JOIN machines mm ON mm.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = mm.site_id"
            " GROUP BY t.technician_id, t.name"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, COUNT(*) FROM technicians t"
            " JOIN work_orders w ON w.technician_id = t.technician_id"
            " JOIN machines mm ON mm.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = mm.site_id"
            " GROUP BY t.technician_id, t.name"
        ),
        note="After the joins one row is one WORK ORDER, not one customer, so"
             " COUNT(*) counts jobs. The question asks how many distinct things"
             " sit at the far end of the chain, which is COUNT(DISTINCT) on"
             " that column -- the row count and the answer are different"
             " numbers whenever anyone was visited twice.",
        claims=[
            ("every technician has been assigned work",
             lambda rows, c: len(rows) == 14),
            ("technicians serve fewer customers than they do jobs",
             lambda rows, c: sum(r[2] for r in rows) < c.execute(
                 "SELECT COUNT(*) FROM work_orders").fetchone()[0]),
        ],
    ),
    # ------------------------------------------- conditional aggregation
    dict(
        id=10, ledger="Q201", concept="A1", tier="Conditional aggregation",
        title="Billed against collected, by region",
        prompt=(
            "For each region: the total value of every invoice raised against"
            " its customers' machines, and the total value of just the ones"
            " that have been paid.\n\n"
            "An invoice counts as paid when it has a paid date. A region whose"
            " customers have never been invoiced does not appear.\n\n"
            "Return: region_name, billed, collected"
        ),
        solution=(
            "SELECT r.name, SUM(i.amount),"
            " SUM(CASE WHEN i.paid_on IS NOT NULL THEN i.amount ELSE 0 END)"
            " FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines mm ON mm.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = mm.site_id"
            " JOIN regions r ON r.region_id = s.region_id GROUP BY r.name"
        ),
        trap_sql=(
            "SELECT r.name, SUM(i.amount),"
            " CASE WHEN i.paid_on IS NOT NULL THEN SUM(i.amount) ELSE 0 END"
            " FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines mm ON mm.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = mm.site_id"
            " JOIN regions r ON r.region_id = s.region_id GROUP BY r.name"
        ),
        note="The aggregate in the THEN branch does not protect the WHEN test."
             " SUM runs over the group; paid_on IS NOT NULL is evaluated"
             " against one arbitrary row SQLite happened to scan, so the whole"
             " region is billed or written off on the strength of a single"
             " invoice. The condition belongs INSIDE the aggregate.",
        claims=[
            ("the four regions with invoices appear; Scotland has none",
             lambda rows, c: len(rows) == 4),
            ("collected never exceeds billed",
             lambda rows, c: all(r[2] <= r[1] + 0.01 for r in rows)),
            ("billed totals every invoice",
             lambda rows, c: abs(sum(r[1] for r in rows) - c.execute(
                 "SELECT SUM(amount) FROM invoices").fetchone()[0]) < 0.01),
        ],
    ),
    dict(
        id=11, ledger="Q202", concept="A1", tier="Conditional aggregation",
        title="What the discount cost, by category",
        prompt=(
            "For each part category: the total value of the parts fitted at"
            " list price, and the total actually charged after the discount on"
            " each line.\n\n"
            "A line is worth quantity * unit_price at list, and"
            " quantity * unit_price * (1 - discount) after discount.\n\n"
            "Return: category, at_list, after_discount"
        ),
        solution=(
            "SELECT p.category, SUM(pu.quantity * pu.unit_price),"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount))"
            " FROM parts p JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY p.category"
        ),
        trap_sql=(
            "SELECT p.category, SUM(pu.quantity * pu.unit_price),"
            " SUM(pu.quantity * pu.unit_price) * (1 - pu.discount)"
            " FROM parts p JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY p.category"
        ),
        note="SUM(a * b) and SUM(a) * b agree only while b is constant across"
             " the group. There are four discount rates in this data, so the"
             " second form totals the category at list and then applies ONE"
             " arbitrary line's discount to all of it. Per-row arithmetic goes"
             " inside the aggregate.",
        claims=[
            ("all nine categories appear",
             lambda rows, c: len(rows) == 9),
            ("the discount always reduces the total",
             lambda rows, c: all(r[2] < r[1] for r in rows)),
            ("more than one discount rate is in use, so the two forms differ",
             lambda rows, c: c.execute(
                 "SELECT COUNT(DISTINCT discount) FROM parts_used").fetchone()[0] > 1),
        ],
    ),
    # --------------------------------------------------------------- NULLs
    dict(
        id=12, ledger="Q203", concept="C7", tier="NULLs",
        title="Parts below reorder level, all parts listed",
        prompt=(
            "Every part in the catalogue, with how many depots hold it below"
            " its reorder level.\n\n"
            "All 40 parts appear. A part nobody stocks, or one whose stock"
            " lines have no reorder level set, shows 0.\n\n"
            "Return: part_id, name, depots_below"
        ),
        solution=(
            "SELECT p.part_id, p.name, COUNT(ps.depot_id)"
            " FROM parts p LEFT JOIN part_stock ps ON ps.part_id = p.part_id"
            " AND ps.reorder_level IS NOT NULL"
            " AND ps.quantity_on_hand < ps.reorder_level"
            " GROUP BY p.part_id, p.name"
        ),
        trap_sql=(
            "SELECT p.part_id, p.name, COUNT(ps.depot_id)"
            " FROM parts p LEFT JOIN part_stock ps ON ps.part_id = p.part_id"
            " WHERE ps.reorder_level IS NOT NULL"
            " AND ps.quantity_on_hand < ps.reorder_level"
            " GROUP BY p.part_id, p.name"
        ),
        note="On a LEFT JOIN a condition about the RIGHT table belongs in ON,"
             " not WHERE. Unmatched rows carry NULL on the right, every WHERE"
             " test against NULL fails, and the rows the LEFT JOIN just"
             " preserved are thrown straight back out -- an inner join wearing"
             " a LEFT JOIN costume. COUNT(ps.depot_id) rather than COUNT(*) is"
             " what makes the survivors read 0.",
        claims=[
            ("all forty parts appear",
             lambda rows, c: len(rows) == 40),
            ("most parts are not below reorder anywhere",
             lambda rows, c: sum(1 for r in rows if r[2] == 0) > 20),
        ],
    ),
    dict(
        id=13, ledger="Q204", concept="C7", tier="NULLs",
        title="Average response time by tier",
        prompt=(
            "For each account tier: how many contracts those customers hold,"
            " and the average agreed response time across them.\n\n"
            "Contracts that agreed no response time still count toward the"
            " contract number, but must not drag the average down. Customers"
            " with no tier recorded are a tier of their own.\n\n"
            "Return: account_tier, contracts, avg_response_hours"
        ),
        solution=(
            "SELECT c.account_tier, COUNT(*), AVG(k.response_hours)"
            " FROM customers c JOIN contracts k ON k.customer_id = c.customer_id"
            " GROUP BY c.account_tier"
        ),
        trap_sql=(
            "SELECT c.account_tier, COUNT(*),"
            " SUM(k.response_hours) * 1.0 / COUNT(*)"
            " FROM customers c JOIN contracts k ON k.customer_id = c.customer_id"
            " GROUP BY c.account_tier"
        ),
        note="AVG ignores NULLs in the divisor as well as the sum, so it"
             " averages over the contracts that actually agreed a time."
             " SUM/COUNT(*) divides by every contract including the ones with"
             " no time at all, which quietly understates every tier. The"
             " NULL tier is kept by GROUP BY, the one place SQL treats NULLs"
             " as equal to each other.",
        claims=[
            ("the untiered customers get their own row",
             lambda rows, c: any(r[0] is None for r in rows)),
            ("the contract counts total every contract held by a customer",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM contracts").fetchone()[0]),
            ("some contracts agreed no response time",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM contracts WHERE response_hours IS NULL"
             ).fetchone()[0] > 0),
        ],
    ),
    # ------------------------------------------------- subqueries & EXISTS
    dict(
        id=14, ledger="Q205", concept="X1", tier="Subqueries & EXISTS",
        title="Customers who have paid everything",
        prompt=(
            "Customers who have been invoiced at least once and have paid every"
            " invoice raised against them.\n\n"
            "One unpaid invoice disqualifies a customer. Customers never"
            " invoiced at all do not qualify.\n\n"
            "Return: customer_id, name"
        ),
        solution=(
            "SELECT c.customer_id, c.name FROM customers c"
            " WHERE EXISTS (SELECT 1 FROM invoices i"
            "   JOIN work_orders w ON w.work_order_id = i.work_order_id"
            "   JOIN machines mm ON mm.machine_id = w.machine_id"
            "   JOIN sites s ON s.site_id = mm.site_id"
            "   WHERE s.customer_id = c.customer_id)"
            " AND NOT EXISTS (SELECT 1 FROM invoices i"
            "   JOIN work_orders w ON w.work_order_id = i.work_order_id"
            "   JOIN machines mm ON mm.machine_id = w.machine_id"
            "   JOIN sites s ON s.site_id = mm.site_id"
            "   WHERE s.customer_id = c.customer_id AND i.paid_on IS NULL)"
        ),
        trap_sql=(
            "SELECT DISTINCT c.customer_id, c.name FROM customers c"
            " JOIN sites s ON s.customer_id = c.customer_id"
            " JOIN machines mm ON mm.site_id = s.site_id"
            " JOIN work_orders w ON w.machine_id = mm.machine_id"
            " JOIN invoices i ON i.work_order_id = w.work_order_id"
            " WHERE i.paid_on IS NOT NULL"
        ),
        note="A WHERE clause can only say 'at least one row looks like this',"
             " because the rows that would disprove it are already gone."
             " Proving something about EVERY row means hunting a counterexample"
             " and finding none. The first EXISTS is not optional: without it"
             " the customers with no invoices at all qualify vacuously.",
        claims=[
            ("far fewer customers qualify than have paid something",
             lambda rows, c: len(rows) < 20),
            ("every customer returned really has no unpaid invoice",
             lambda rows, c: all(c.execute(
                 "SELECT COUNT(*) FROM invoices i"
                 " JOIN work_orders w ON w.work_order_id = i.work_order_id"
                 " JOIN machines mm ON mm.machine_id = w.machine_id"
                 " JOIN sites s ON s.site_id = mm.site_id"
                 " WHERE s.customer_id = ? AND i.paid_on IS NULL",
                 (r[0],)).fetchone()[0] == 0 for r in rows)),
        ],
    ),
    dict(
        id=15, ledger="Q206", concept="X2", tier="Subqueries & EXISTS",
        title="Longer than that technician usually takes",
        prompt=(
            "Work orders whose total labour hours are above the average total"
            " for the technician assigned to them.\n\n"
            "Each job is compared against its OWN technician's average, not the"
            " average across everybody.\n\n"
            "Return: work_order_id, technician_id, hours"
        ),
        solution=(
            "WITH j AS (SELECT w.work_order_id, w.technician_id,"
            " SUM(le.hours) AS h FROM work_orders w"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " GROUP BY w.work_order_id, w.technician_id)"
            " SELECT j.work_order_id, j.technician_id, j.h FROM j"
            " WHERE j.h > (SELECT AVG(j2.h) FROM j j2"
            "              WHERE j2.technician_id = j.technician_id)"
        ),
        trap_sql=(
            "WITH j AS (SELECT w.work_order_id, w.technician_id,"
            " SUM(le.hours) AS h FROM work_orders w"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " GROUP BY w.work_order_id, w.technician_id)"
            " SELECT j.work_order_id, j.technician_id, j.h FROM j"
            " WHERE j.h > (SELECT AVG(j2.h) FROM j j2)"
        ),
        note="The correlation is the whole question. Drop the WHERE inside the"
             " subquery and it stops asking about this technician and starts"
             " asking about the company -- one number compared against every"
             " row. An uncorrelated subquery returns the same verdict for"
             " everyone, which is a filter that is not really filtering.",
        claims=[
            ("some jobs beat their own technician's average",
             lambda rows, c: len(rows) > 0),
            ("fewer than half the jobs qualify",
             lambda rows, c: len(rows) < c.execute(
                 "SELECT COUNT(DISTINCT work_order_id) FROM labor_entries"
             ).fetchone()[0]),
        ],
    ),
    # -------------------------------------------------------- window frames
    dict(
        id=16, ledger="Q207", concept="C3", tier="Window frames",
        title="The first invoice each customer got",
        prompt=(
            "For every customer who has been invoiced, their earliest invoice --"
            " its id, the date it was issued and the amount.\n\n"
            "Order by issue date, then invoice_id, so the earliest is"
            " unambiguous.\n\n"
            "Return: customer_id, invoice_id, issued_on, amount"
        ),
        solution=(
            "WITH inv AS (SELECT s.customer_id, i.invoice_id, i.issued_on,"
            " i.amount, ROW_NUMBER() OVER (PARTITION BY s.customer_id"
            "   ORDER BY i.issued_on, i.invoice_id) AS rn"
            " FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines mm ON mm.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = mm.site_id)"
            " SELECT customer_id, invoice_id, issued_on, amount FROM inv"
            " WHERE rn = 1"
        ),
        trap_sql=(
            "WITH inv AS (SELECT s.customer_id, i.invoice_id, i.issued_on,"
            " i.amount, ROW_NUMBER() OVER (ORDER BY i.issued_on, i.invoice_id)"
            " AS rn FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines mm ON mm.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = mm.site_id)"
            " SELECT customer_id, invoice_id, issued_on, amount FROM inv"
            " WHERE rn = 1"
        ),
        note="PARTITION BY is what restarts the numbering per customer. Without"
             " it the whole result is one sequence, rn = 1 picks the single"
             " earliest invoice in the company, and you get one row back"
             " instead of one per customer.",
        claims=[
            ("one row per invoiced customer",
             lambda rows, c: len(rows) == c.execute(
                 "SELECT COUNT(DISTINCT s.customer_id) FROM invoices i"
                 " JOIN work_orders w ON w.work_order_id = i.work_order_id"
                 " JOIN machines mm ON mm.machine_id = w.machine_id"
                 " JOIN sites s ON s.site_id = mm.site_id").fetchone()[0]),
            ("every customer appears exactly once",
             lambda rows, c: len({r[0] for r in rows}) == len(rows)),
        ],
    ),
    dict(
        id=17, ledger="Q208", concept="W1", tier="Window frames",
        title="Smoothed either side",
        prompt=(
            "Work orders opened per calendar month, with a three-month average"
            " CENTRED on each month -- the month before, the month itself and"
            " the month after.\n\n"
            "The first and last months have only two months to average.\n\n"
            "Return: month, work_orders, centred_avg"
        ),
        solution=(
            "WITH m AS (SELECT strftime('%Y-%m', opened_at) AS mth, COUNT(*) AS n"
            " FROM work_orders GROUP BY mth)"
            " SELECT mth, n, AVG(n) OVER (ORDER BY mth"
            " ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) FROM m"
        ),
        trap_sql=(
            "WITH m AS (SELECT strftime('%Y-%m', opened_at) AS mth, COUNT(*) AS n"
            " FROM work_orders GROUP BY mth)"
            " SELECT mth, n, AVG(n) OVER (ORDER BY mth) FROM m"
        ),
        note="ORDER BY with no frame does not mean 'just this row'. It defaults"
             " to everything from the start up to the current row, which is a"
             " running average -- right for the first month or two and drifting"
             " ever further afterwards. A window that looks FORWARD needs"
             " FOLLOWING, which no default will ever give you.",
        claims=[
            ("every month appears",
             lambda rows, c: len(rows) == 18),
            ("the centred average differs from a running one",
             lambda rows, c: any(abs(r[2] - r[1]) > 0.01 for r in rows)),
        ],
    ),
    dict(
        id=18, ledger="Q209", concept="C3", tier="Window frames",
        title="How long until the machine came back",
        prompt=(
            "For every work order that was followed by another on the SAME"
            " machine, the number of days until that next job was opened.\n\n"
            "Order within a machine by opened_at, then work_order_id. Each"
            " machine's most recent job has no next job and does not appear.\n\n"
            "Return: machine_id, work_order_id, opened_at, days_until_next"
        ),
        solution=(
            "WITH w AS (SELECT machine_id, work_order_id, opened_at,"
            " LEAD(opened_at) OVER (PARTITION BY machine_id"
            "   ORDER BY opened_at, work_order_id) AS nxt FROM work_orders)"
            " SELECT machine_id, work_order_id, opened_at,"
            " CAST(julianday(nxt) - julianday(opened_at) AS INT)"
            " FROM w WHERE nxt IS NOT NULL"
        ),
        trap_sql=(
            "WITH w AS (SELECT machine_id, work_order_id, opened_at,"
            " LEAD(opened_at) OVER (ORDER BY opened_at, work_order_id) AS nxt"
            " FROM work_orders)"
            " SELECT machine_id, work_order_id, opened_at,"
            " CAST(julianday(nxt) - julianday(opened_at) AS INT)"
            " FROM w WHERE nxt IS NOT NULL"
        ),
        note="LEAD is LAG facing the other way -- it reaches the NEXT row"
             " rather than the previous one. Without PARTITION BY the 'next'"
             " row is whatever job sorts after this one across the whole"
             " company, so the gaps are measured between unrelated machines"
             " and nearly every row survives instead of one per machine"
             " dropping out.",
        claims=[
            ("each machine's last job drops out",
             lambda rows, c: len(rows) == c.execute(
                 "SELECT COUNT(*) - COUNT(DISTINCT machine_id) FROM work_orders"
             ).fetchone()[0]),
            ("no gap is negative",
             lambda rows, c: all(r[3] >= 0 for r in rows)),
        ],
    ),
    dict(
        id=19, ledger="Q210", concept="W1", tier="Window frames",
        title="The most-fitted part in each category",
        prompt=(
            "In each part category, the part fitted on the most work order"
            " lines, with that count.\n\n"
            "Where two parts in a category tie for the most, BOTH appear.\n\n"
            "Return: category, part_id, name, times_fitted"
        ),
        solution=(
            "WITH t AS (SELECT p.category, p.part_id, p.name, COUNT(*) AS fits"
            " FROM parts p JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY p.part_id, p.category, p.name)"
            " SELECT category, part_id, name, fits FROM ("
            " SELECT t.*, RANK() OVER (PARTITION BY category"
            "   ORDER BY fits DESC) AS rk FROM t) WHERE rk = 1"
        ),
        trap_sql=(
            "WITH t AS (SELECT p.category, p.part_id, p.name, COUNT(*) AS fits"
            " FROM parts p JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY p.part_id, p.category, p.name)"
            " SELECT category, part_id, name, fits FROM ("
            " SELECT t.*, ROW_NUMBER() OVER (PARTITION BY category"
            "   ORDER BY fits DESC) AS rk FROM t) WHERE rk = 1"
        ),
        note="RANK gives tied rows the SAME number; ROW_NUMBER breaks ties"
             " arbitrarily and keeps exactly one. When the question says both"
             " tied rows should appear, ROW_NUMBER silently drops one of them"
             " and there is nothing in the output to show it happened. Use"
             " ROW_NUMBER when you want exactly one, RANK when ties are real.",
        claims=[
            ("at least one category has a tie for the top",
             lambda rows, c: len(rows) > 9),
            ("every category is represented",
             lambda rows, c: len({r[0] for r in rows}) == 9),
        ],
    ),
    # --------------------------------------------------------- dates & gaps
    dict(
        id=20, ledger="Q211", concept="D1", tier="Dates & gaps",
        title="How long before anyone turned up",
        prompt=(
            "For every work order that has logged labour, the date of its FIRST"
            " labour visit and how many days after the job was opened that"
            " visit happened.\n\n"
            "Return: work_order_id, opened_at, first_visit, days_to_first_visit"
        ),
        solution=(
            "SELECT w.work_order_id, w.opened_at, MIN(le.work_date),"
            " CAST(julianday(MIN(le.work_date)) - julianday(w.opened_at) AS INT)"
            " FROM work_orders w"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " GROUP BY w.work_order_id, w.opened_at"
        ),
        trap_sql=(
            "SELECT w.work_order_id, w.opened_at, le.work_date,"
            " CAST(julianday(le.work_date) - julianday(w.opened_at) AS INT)"
            " FROM work_orders w"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
        ),
        note="Without the GROUP BY this returns one row per VISIT, not per job"
             " -- every later visit comes back too, each with its own gap. The"
             " question asks for one row per work order, so the many visits"
             " have to collapse to their MIN before the arithmetic means"
             " anything.",
        claims=[
            ("one row per job that has labour",
             lambda rows, c: len(rows) == c.execute(
                 "SELECT COUNT(DISTINCT work_order_id) FROM labor_entries"
             ).fetchone()[0]),
            ("no first visit predates the job being opened",
             lambda rows, c: all(r[3] >= 0 for r in rows)),
        ],
    ),
    dict(
        id=21, ledger="Q212", concept="D1", tier="Dates & gaps",
        title="The longest quiet spell",
        prompt=(
            "For every customer with more than one invoice, the longest gap in"
            " days between two consecutive invoices.\n\n"
            "Consecutive means ordered by issue date, then invoice_id. The gap"
            " is between neighbours, not between the first and the last.\n\n"
            "Return: customer_id, longest_gap_days"
        ),
        solution=(
            "WITH g AS (SELECT s.customer_id, i.issued_on,"
            " LAG(i.issued_on) OVER (PARTITION BY s.customer_id"
            "   ORDER BY i.issued_on, i.invoice_id) AS prev"
            " FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines mm ON mm.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = mm.site_id)"
            " SELECT customer_id,"
            " CAST(MAX(julianday(issued_on) - julianday(prev)) AS INT)"
            " FROM g WHERE prev IS NOT NULL GROUP BY customer_id"
        ),
        trap_sql=(
            "SELECT s.customer_id,"
            " CAST(julianday(MAX(i.issued_on)) - julianday(MIN(i.issued_on)) AS INT)"
            " FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines mm ON mm.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = mm.site_id"
            " GROUP BY s.customer_id"
        ),
        note="First to last is the total SPAN, not the longest gap inside it --"
             " they agree only for a customer with exactly two invoices, which"
             " is enough to make the wrong answer look right on a spot check."
             " The gap is a property of neighbouring rows, so LAG first, then"
             " take the MAX of those differences.",
        claims=[
            ("customers with a single invoice are excluded",
             lambda rows, c: len(rows) < c.execute(
                 "SELECT COUNT(DISTINCT s.customer_id) FROM invoices i"
                 " JOIN work_orders w ON w.work_order_id = i.work_order_id"
                 " JOIN machines mm ON mm.machine_id = w.machine_id"
                 " JOIN sites s ON s.site_id = mm.site_id").fetchone()[0]),
            ("every gap is positive",
             lambda rows, c: all(r[1] > 0 for r in rows)),
        ],
    ),
    dict(
        id=22, ledger="Q213", concept="D1", tier="Dates & gaps",
        title="By quarter, not by month",
        prompt=(
            "Work orders opened per calendar quarter, labelled like 2025-Q1.\n\n"
            "Q1 is January to March, Q2 April to June, and so on.\n\n"
            "Return: quarter, work_orders"
        ),
        solution=(
            "SELECT strftime('%Y', opened_at) || '-Q' ||"
            " ((CAST(strftime('%m', opened_at) AS INT) + 2) / 3) AS q, COUNT(*)"
            " FROM work_orders GROUP BY q"
        ),
        trap_sql=(
            "SELECT strftime('%Y', opened_at) || '-Q' ||"
            " (CAST(strftime('%m', opened_at) AS INT) / 3) AS q, COUNT(*)"
            " FROM work_orders GROUP BY q"
        ),
        note="SQLite has no quarter format code, so the month has to become a"
             " quarter by arithmetic: (month + 2) / 3 on integers gives 1 for"
             " January to March and 4 for October to December. Plain month / 3"
             " is off by one at every boundary -- March lands in Q1 but June"
             " lands in Q2 and December in Q4, which produces a phantom Q0.",
        claims=[
            ("quarters are labelled 1 to 4, never 0",
             lambda rows, c: all(r[0][-1] in "1234" for r in rows)),
            ("the counts total every work order",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM work_orders").fetchone()[0]),
        ],
    ),
    # ------------------------------------------------------ set operations
    dict(
        id=23, ledger="Q214", concept="S1", tier="Set operations",
        title="Under contract, never called out",
        prompt=(
            "Customers who hold at least one contract but have never had a work"
            " order raised against any of their machines.\n\n"
            "This compares two SETS of customer ids.\n\n"
            "Return: customer_id"
        ),
        solution=(
            "SELECT customer_id FROM contracts"
            " EXCEPT"
            " SELECT s.customer_id FROM sites s"
            " JOIN machines mm ON mm.site_id = s.site_id"
            " JOIN work_orders w ON w.machine_id = mm.machine_id"
        ),
        trap_sql=(
            "SELECT DISTINCT k.customer_id FROM contracts k"
            " JOIN sites s ON s.customer_id = k.customer_id"
            " LEFT JOIN machines mm ON mm.site_id = s.site_id"
            " LEFT JOIN work_orders w ON w.machine_id = mm.machine_id"
            " WHERE w.work_order_id IS NULL"
        ),
        note="An anti-join tests one ROW at a time, so a customer with one"
             " quiet machine and ten busy ones still produces a matching quiet"
             " row and slips into the answer. 'Never' is a property of the"
             " whole customer, which is a set difference -- EXCEPT, or"
             " NOT EXISTS over every one of their machines.",
        claims=[
            ("only a couple of customers qualify",
             lambda rows, c: 0 < len(rows) < 6),
            ("every customer returned really has no work orders",
             lambda rows, c: all(c.execute(
                 "SELECT COUNT(*) FROM sites s"
                 " JOIN machines mm ON mm.site_id = s.site_id"
                 " JOIN work_orders w ON w.machine_id = mm.machine_id"
                 " WHERE s.customer_id = ?", (r[0],)).fetchone()[0] == 0
                 for r in rows)),
        ],
    ),
    dict(
        id=24, ledger="Q215", concept="S1", tier="Set operations",
        title="Running low on the expensive ones",
        prompt=(
            "Parts that are below their reorder level in at least one depot AND"
            " have cost more than 1000 in total across every line they were"
            " fitted on.\n\n"
            "Line spend is quantity * unit_price * (1 - discount). The two"
            " conditions are about the part, not about any single row.\n\n"
            "Return: part_id"
        ),
        solution=(
            "SELECT part_id FROM part_stock"
            " WHERE reorder_level IS NOT NULL"
            " AND quantity_on_hand < reorder_level"
            " INTERSECT"
            " SELECT part_id FROM parts_used GROUP BY part_id"
            " HAVING SUM(quantity * unit_price * (1 - discount)) > 1000"
        ),
        trap_sql=(
            "SELECT DISTINCT ps.part_id FROM part_stock ps"
            " JOIN parts_used pu ON pu.part_id = ps.part_id"
            " WHERE ps.reorder_level IS NOT NULL"
            " AND ps.quantity_on_hand < ps.reorder_level"
            " AND pu.quantity * pu.unit_price * (1 - pu.discount) > 1000"
        ),
        note="The spend test is about the part's TOTAL, so it cannot be applied"
             " to individual lines. Joining the two tables tests one stock row"
             " against one usage row and asks whether that single line cleared"
             " 1000, which is a different and much harder bar. Build each set"
             " at its own grain, then INTERSECT.",
        claims=[
            ("a handful of parts qualify",
             lambda rows, c: 0 < len(rows) < 15),
            ("no single line reaches the threshold in most cases, so the"
             " per-line test is genuinely different",
             lambda rows, c: c.execute(
                 "SELECT COUNT(DISTINCT part_id) FROM parts_used"
                 " WHERE quantity * unit_price * (1 - discount) > 1000"
             ).fetchone()[0] < c.execute(
                 "SELECT COUNT(*) FROM (SELECT part_id FROM parts_used"
                 " GROUP BY part_id HAVING"
                 " SUM(quantity * unit_price * (1 - discount)) > 1000)"
             ).fetchone()[0]),
        ],
    ),
    dict(
        id=25, ledger="Q216", concept="S1", tier="Set operations",
        title="Everything that happened to machine 38",
        prompt=(
            "A single dated event log for machine 38: every work order opened on"
            " it, every inspection of those work orders, and every invoice"
            " raised for them.\n\n"
            "Label each row 'opened', 'inspected' or 'invoiced'. Two events of"
            " the same kind on the same date are two events, not one.\n\n"
            "Return: event, event_date"
        ),
        solution=(
            "SELECT 'opened' AS k, opened_at AS d FROM work_orders"
            " WHERE machine_id = 38"
            " UNION ALL"
            " SELECT 'inspected', i.inspected_at FROM inspections i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " WHERE w.machine_id = 38"
            " UNION ALL"
            " SELECT 'invoiced', v.issued_on FROM invoices v"
            " JOIN work_orders w ON w.work_order_id = v.work_order_id"
            " WHERE w.machine_id = 38"
        ),
        trap_sql=(
            "SELECT 'opened' AS k, opened_at AS d FROM work_orders"
            " WHERE machine_id = 38"
            " UNION"
            " SELECT 'inspected', i.inspected_at FROM inspections i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " WHERE w.machine_id = 38"
            " UNION"
            " SELECT 'invoiced', v.issued_on FROM invoices v"
            " JOIN work_orders w ON w.work_order_id = v.work_order_id"
            " WHERE w.machine_id = 38"
        ),
        note="UNION removes duplicate rows; UNION ALL keeps them. This machine"
             " has two events of the same kind on the same day, so UNION"
             " collapses them into one and the log quietly loses an event."
             " UNION ALL is also the cheaper operator, since it never has to"
             " sort to find the duplicates.",
        claims=[
            ("the log has a same-kind, same-day pair that UNION would lose",
             lambda rows, c: len(rows) > len({(r[0], r[1]) for r in rows})),
        ],
    ),
    # ------------------------------------------------------ silent sampling
    dict(
        id=26, ledger="Q217", concept="B1", tier="Silent sampling",
        title="Average line value by category",
        prompt=(
            "For each part category, the average value of a single parts line --"
            " quantity times unit price, averaged across the lines.\n\n"
            "Return: category, avg_line_value"
        ),
        solution=(
            "SELECT p.category, AVG(pu.quantity * pu.unit_price)"
            " FROM parts p JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY p.category"
        ),
        trap_sql=(
            "SELECT p.category, AVG(pu.quantity) * pu.unit_price"
            " FROM parts p JOIN parts_used pu ON pu.part_id = p.part_id"
            " GROUP BY p.category"
        ),
        note="AVG(a * b) is not AVG(a) * b. The second averages the quantities"
             " and then multiplies by ONE arbitrary row's unit price -- a bare"
             " column under GROUP BY, which SQLite samples rather than"
             " rejecting. Every unit price in this data is distinct, so the"
             " sampled one is almost never representative.",
        claims=[
            ("all nine categories appear",
             lambda rows, c: len(rows) == 9),
            ("unit prices vary within a category, so sampling one is wrong",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM (SELECT p.category FROM parts p"
                 " JOIN parts_used pu ON pu.part_id = p.part_id"
                 " GROUP BY p.category"
                 " HAVING COUNT(DISTINCT pu.unit_price) > 1)").fetchone()[0] == 9),
        ],
    ),
    dict(
        id=27, ledger="Q218", concept="B1", tier="Silent sampling",
        title="What the stock on hand is worth",
        prompt=(
            "For each depot, the value of the stock it holds -- every stock"
            " line's quantity on hand multiplied by that part's unit cost,"
            " totalled.\n\n"
            "Return: depot_name, stock_value"
        ),
        solution=(
            "SELECT d.name, SUM(ps.quantity_on_hand * p.unit_cost)"
            " FROM depots d JOIN part_stock ps ON ps.depot_id = d.depot_id"
            " JOIN parts p ON p.part_id = ps.part_id GROUP BY d.name"
        ),
        trap_sql=(
            "SELECT d.name, SUM(ps.quantity_on_hand) * p.unit_cost"
            " FROM depots d JOIN part_stock ps ON ps.depot_id = d.depot_id"
            " JOIN parts p ON p.part_id = ps.part_id GROUP BY d.name"
        ),
        note="Each line has its own part and therefore its own unit cost, so"
             " the multiply belongs inside the SUM. Totalling the quantities"
             " first and multiplying by one sampled cost values a depot's"
             " entire shelf at whatever part happened to be scanned first --"
             " and the result is still a plausible-looking number.",
        claims=[
            ("all four depots appear",
             lambda rows, c: len(rows) == 4),
            ("unit costs vary within a depot",
             lambda rows, c: c.execute(
                 "SELECT MIN(n) FROM (SELECT COUNT(DISTINCT p.unit_cost) n"
                 " FROM part_stock ps JOIN parts p ON p.part_id = ps.part_id"
                 " GROUP BY ps.depot_id)").fetchone()[0] > 1),
        ],
    ),
    # ----------------------------------------------------------- self-joins
    dict(
        id=28, ledger="Q219", concept="J1", tier="Self-joins",
        title="Parts fitted on the same job",
        prompt=(
            "Every pair of DIFFERENT parts that have been fitted on the same"
            " work order at least once.\n\n"
            "Each pair once, not twice, and no part paired with itself. List"
            " the lower part_id first.\n\n"
            "Return: part_a, part_b"
        ),
        solution=(
            "SELECT DISTINCT a.part_id, b.part_id FROM parts_used a"
            " JOIN parts_used b ON b.work_order_id = a.work_order_id"
            " AND b.part_id > a.part_id"
        ),
        trap_sql=(
            "SELECT DISTINCT a.part_id, b.part_id FROM parts_used a"
            " JOIN parts_used b ON b.work_order_id = a.work_order_id"
            " AND b.part_id <> a.part_id"
        ),
        note="'<>' keeps both (A, B) and (B, A), so every pair comes back"
             " twice. '>' picks one ordering and drops the mirror image, and"
             " rules out self-pairs for free since nothing is greater than"
             " itself. DISTINCT is still needed here: the same two parts can"
             " share more than one work order.",
        claims=[
            ("the lower id always comes first",
             lambda rows, c: all(r[0] < r[1] for r in rows)),
            ("pairs really do repeat across jobs, so DISTINCT matters",
             lambda rows, c: len(rows) < c.execute(
                 "SELECT COUNT(*) FROM parts_used a JOIN parts_used b"
                 " ON b.work_order_id = a.work_order_id"
                 " AND b.part_id > a.part_id").fetchone()[0]),
        ],
    ),
    dict(
        id=29, ledger="Q220", concept="J1", tier="Self-joins",
        title="Hired around the same time",
        prompt=(
            "Every pair of technicians working out of the same depot who were"
            " hired within a year of each other, with the depot name.\n\n"
            "Each pair once. List the lower technician_id first.\n\n"
            "Return: depot_name, technician_a, technician_b"
        ),
        solution=(
            "SELECT d.name, a.name, b.name FROM technicians a"
            " JOIN technicians b ON b.depot_id = a.depot_id"
            " AND b.technician_id > a.technician_id"
            " AND ABS(julianday(b.hired_on) - julianday(a.hired_on)) <= 365"
            " JOIN depots d ON d.depot_id = a.depot_id"
        ),
        trap_sql=(
            "SELECT d.name, a.name, b.name FROM technicians a"
            " JOIN technicians b ON b.depot_id = a.depot_id"
            " AND b.technician_id <> a.technician_id"
            " AND ABS(julianday(b.hired_on) - julianday(a.hired_on)) <= 365"
            " JOIN depots d ON d.depot_id = a.depot_id"
        ),
        note="The same '>' rule as any pairing question, with a date window"
             " added. ABS is what makes the window symmetric -- without it the"
             " test only catches pairs in one hiring order, which the '>' on"
             " technician_id has already fixed to id order rather than date"
             " order, so half the genuine pairs would go missing.",
        claims=[
            ("every pair is within a year",
             lambda rows, c: True),
            ("some pairs qualify",
             lambda rows, c: len(rows) > 0),
        ],
    ),
    # -------------------------------------------------------------- general
    dict(
        id=30, ledger="Q221", concept="general", tier="General",
        title="Depot scorecard",
        prompt=(
            "One row per depot: how many technicians work out of it, how many"
            " stock lines it holds, and the total labour hours its technicians"
            " have logged.\n\n"
            "All four depots appear even if a number is 0.\n\n"
            "Return: depot_id, name, technicians, stock_lines, hours"
        ),
        solution=(
            "SELECT d.depot_id, d.name,"
            " (SELECT COUNT(*) FROM technicians t WHERE t.depot_id = d.depot_id),"
            " (SELECT COUNT(*) FROM part_stock ps WHERE ps.depot_id = d.depot_id),"
            " (SELECT COALESCE(SUM(le.hours), 0) FROM labor_entries le"
            "  JOIN technicians t ON t.technician_id = le.technician_id"
            "  WHERE t.depot_id = d.depot_id)"
            " FROM depots d"
        ),
        trap_sql=(
            "SELECT d.depot_id, d.name, COUNT(DISTINCT t.technician_id),"
            " COUNT(DISTINCT ps.part_id), COALESCE(SUM(le.hours), 0)"
            " FROM depots d LEFT JOIN technicians t ON t.depot_id = d.depot_id"
            " LEFT JOIN part_stock ps ON ps.depot_id = d.depot_id"
            " LEFT JOIN labor_entries le ON le.technician_id = t.technician_id"
            " GROUP BY d.depot_id, d.name"
        ),
        note="Three measures at three different grains. Joining all of them"
             " into one query multiplies each by the others -- the hours get"
             " repeated once per stock line, and DISTINCT patches the two"
             " counts while leaving the SUM inflated. Independent measures"
             " belong in independent subqueries.",
        claims=[
            ("all four depots appear",
             lambda rows, c: len(rows) == 4),
            ("the technician counts total the workforce",
             lambda rows, c: sum(r[2] for r in rows) == 14),
            ("the hours total every labour entry",
             lambda rows, c: abs(sum(r[4] for r in rows) - c.execute(
                 "SELECT SUM(hours) FROM labor_entries").fetchone()[0]) < 0.01),
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
