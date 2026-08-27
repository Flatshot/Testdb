"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q102-Q131) are built on the repair-depot schema and
weighted hard toward GRAIN -- half of them punish the mistake of joining two
one-to-many children in a single query block. Each question carries:

  concept   the mistake it drills (C1..C9), or "GEN"
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

The one structural fact worth holding onto: a work order has THREE independent
children -- parts_used, labor_entries and inspections. A job with 4 parts and
3 visits produces 12 rows if you join both, so the parts total comes out 3x too
big and the labour total 4x too big. Aggregate each branch to one row per work
order FIRST, then join the results together.
"""

EXERCISES = [
    # ---------------------------------------------------------------- grain
    dict(
        id=1, ledger="Q102", concept="C2", tier="Grain",
        title="What a job actually cost",
        prompt=(
            "Every closed work order that has both parts and labour logged"
            " against it, with what each side cost and the total.\n\n"
            "Parts cost is quantity * unit_price * (1 - discount), summed over"
            " the job's parts. Labour cost is hours * rate, summed over the"
            " job's visits.\n\n"
            "Return: work_order_id, parts_cost, labor_cost, total_cost"
        ),
        solution=(
            "WITH p AS (SELECT work_order_id,"
            " SUM(quantity * unit_price * (1 - discount)) AS pc"
            " FROM parts_used GROUP BY work_order_id),"
            " l AS (SELECT work_order_id, SUM(hours * rate) AS lc"
            " FROM labor_entries GROUP BY work_order_id)"
            " SELECT w.work_order_id, p.pc, l.lc, p.pc + l.lc"
            " FROM work_orders w JOIN p USING(work_order_id)"
            " JOIN l USING(work_order_id) WHERE w.status = 'closed'"
        ),
        trap_sql=(
            "SELECT w.work_order_id,"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount)),"
            " SUM(le.hours * le.rate),"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount))"
            " + SUM(le.hours * le.rate)"
            " FROM work_orders w"
            " JOIN parts_used pu ON pu.work_order_id = w.work_order_id"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' GROUP BY w.work_order_id"
        ),
        note="Parts and labour are separate children of the work order. Joined"
             " together, 4 parts x 3 visits gives 12 rows: the parts total"
             " comes out 3x too big and the labour total 4x. Collapse each"
             " branch to one row per job before they meet.",
        claims=[
            ("no job's parts and labour are both counted more than once",
             lambda rows, c: all(abs(r[1] + r[2] - r[3]) < 0.01 for r in rows)),
        ],
    ),
    dict(
        id=2, ledger="Q103", concept="C2", tier="Grain",
        title="Labour's share of the bill",
        prompt=(
            "For closed work orders that have both parts and labour: labour"
            " cost as a percentage of the whole job cost.\n\n"
            "Whole job cost is parts plus labour. Work each side out"
            " separately -- one row per work order each -- then divide.\n\n"
            "The answer is between 0 and 100 for every job.\n\n"
            "Return: work_order_id, labor_pct_of_total"
        ),
        solution=(
            "WITH p AS (SELECT work_order_id,"
            " SUM(quantity * unit_price * (1 - discount)) AS pc"
            " FROM parts_used GROUP BY work_order_id),"
            " l AS (SELECT work_order_id, SUM(hours * rate) AS lc"
            " FROM labor_entries GROUP BY work_order_id)"
            " SELECT w.work_order_id, 100.0 * l.lc / (p.pc + l.lc)"
            " FROM work_orders w JOIN p USING(work_order_id)"
            " JOIN l USING(work_order_id) WHERE w.status = 'closed'"
        ),
        trap_sql=(
            "WITH p AS (SELECT work_order_id,"
            " SUM(quantity * unit_price * (1 - discount)) AS pc"
            " FROM parts_used GROUP BY work_order_id),"
            " l AS (SELECT work_order_id, SUM(hours * rate) AS lc"
            " FROM labor_entries GROUP BY work_order_id)"
            " SELECT w.work_order_id, 100.0 * l.lc / p.pc"
            " FROM work_orders w JOIN p USING(work_order_id)"
            " JOIN l USING(work_order_id) WHERE w.status = 'closed'"
        ),
        note="'A as a share of the total' puts the TOTAL on the bottom, not the"
             " other half. Dividing labour by parts answers a different"
             " question and can exceed 100, which is the tell.",
        claims=[
            ("every share lies between 0 and 100",
             lambda rows, c: all(0 <= r[1] <= 100 for r in rows)),
        ],
    ),
    dict(
        id=3, ledger="Q104", concept="C2", tier="Grain",
        title="Parts count and hours together",
        prompt=(
            "For every work order that has both parts and labour: how many"
            " distinct parts were fitted, and how many hours were worked in"
            " total.\n\n"
            "A part fitted in quantity 6 still counts as one part.\n\n"
            "Return: work_order_id, part_lines, total_hours"
        ),
        solution=(
            "WITH p AS (SELECT work_order_id, COUNT(*) AS n"
            " FROM parts_used GROUP BY work_order_id),"
            " l AS (SELECT work_order_id, SUM(hours) AS h"
            " FROM labor_entries GROUP BY work_order_id)"
            " SELECT work_order_id, p.n, l.h FROM p JOIN l USING(work_order_id)"
        ),
        trap_sql=(
            "SELECT w.work_order_id, COUNT(*), SUM(le.hours)"
            " FROM work_orders w"
            " JOIN parts_used pu ON pu.work_order_id = w.work_order_id"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " GROUP BY w.work_order_id"
        ),
        note="COUNT(*) after a fan-out counts the multiplied rows, not the"
             " parts. Both columns are wrong for the same reason, in different"
             " ways -- one is inflated by the visits, the other by the parts.",
    ),
    dict(
        id=4, ledger="Q105", concept="C2", tier="Grain",
        title="Hours, and who signed the job off",
        prompt=(
            "For each work order that has labour logged and an assigned"
            " technician: the total hours worked on it, and the name of the"
            " technician the job is assigned to.\n\n"
            "The assignment lives on the work order. Several technicians may"
            " have logged visits against the same job, so the assigned one is"
            " not simply whoever appears in labor_entries.\n\n"
            "Return: work_order_id, technician_name, total_hours"
        ),
        solution=(
            "WITH h AS (SELECT work_order_id, SUM(hours) AS total"
            " FROM labor_entries GROUP BY work_order_id)"
            " SELECT w.work_order_id, t.name, h.total"
            " FROM work_orders w JOIN h USING(work_order_id)"
            " JOIN technicians t ON t.technician_id = w.technician_id"
        ),
        trap_sql=(
            "SELECT w.work_order_id, t.name, SUM(le.hours)"
            " FROM work_orders w"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " JOIN technicians t ON t.technician_id = le.technician_id"
            " WHERE w.technician_id IS NOT NULL"
            " GROUP BY w.work_order_id"
        ),
        note="Joining technicians through labor_entries picks whoever logged a"
             " visit, then GROUP BY silently keeps one arbitrary name. The"
             " assignment is a column on work_orders -- join to it directly.",
    ),
    dict(
        id=5, ledger="Q106", concept="C2", tier="Grain",
        title="The missing SUM",
        prompt=(
            "Total parts cost for every work order that used any parts, and the"
            " number of separate part lines on it.\n\n"
            "Parts cost is quantity * unit_price * (1 - discount).\n\n"
            "Jobs using a single part are the ones to check your answer"
            " against: if a multi-part job reports the same figure as a"
            " one-part job of similar size, something is not being added up.\n\n"
            "Return: work_order_id, part_lines, parts_cost"
        ),
        solution=(
            "SELECT work_order_id, COUNT(*),"
            " SUM(quantity * unit_price * (1 - discount))"
            " FROM parts_used GROUP BY work_order_id"
        ),
        trap_sql=(
            "SELECT work_order_id, COUNT(*),"
            " quantity * unit_price * (1 - discount)"
            " FROM parts_used GROUP BY work_order_id"
        ),
        note="A bare expression under GROUP BY is not an error in SQLite -- it"
             " silently returns one arbitrary row's value. Most engines reject"
             " it. Every non-grouped column in the SELECT needs an aggregate.",
    ),
    dict(
        id=6, ledger="Q107", concept="C2", tier="Grain",
        title="Do not go back to the well",
        prompt=(
            "Closed work orders whose labour cost is more than 400, showing"
            " when the job was opened and how many visits it took.\n\n"
            "Labour cost is hours * rate summed over the visits.\n\n"
            "Return: work_order_id, opened_at, visits, labor_cost"
        ),
        solution=(
            "WITH l AS (SELECT work_order_id, COUNT(*) AS visits,"
            " SUM(hours * rate) AS lc FROM labor_entries GROUP BY work_order_id)"
            " SELECT w.work_order_id, w.opened_at, l.visits, l.lc"
            " FROM work_orders w JOIN l USING(work_order_id)"
            " WHERE w.status = 'closed' AND l.lc > 400"
        ),
        trap_sql=(
            "WITH l AS (SELECT work_order_id, COUNT(*) AS visits,"
            " SUM(hours * rate) AS lc FROM labor_entries GROUP BY work_order_id)"
            " SELECT w.work_order_id, w.opened_at, l.visits, l.lc"
            " FROM work_orders w JOIN l USING(work_order_id)"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' AND l.lc > 400"
        ),
        note="Once a CTE has collapsed a table to one row per job, joining that"
             " same table again re-expands it. The CTE already holds everything"
             " you need from it.",
    ),
    dict(
        id=7, ledger="Q108", concept="C2", tier="Grain",
        title="Three children, one job",
        prompt=(
            "Closed work orders that have parts, labour AND at least one"
            " inspection: the parts cost, the total hours, and how many"
            " inspections the job received.\n\n"
            "Return: work_order_id, parts_cost, total_hours, inspections"
        ),
        solution=(
            "WITH p AS (SELECT work_order_id,"
            " SUM(quantity * unit_price * (1 - discount)) AS pc"
            " FROM parts_used GROUP BY work_order_id),"
            " l AS (SELECT work_order_id, SUM(hours) AS h"
            " FROM labor_entries GROUP BY work_order_id),"
            " i AS (SELECT work_order_id, COUNT(*) AS n"
            " FROM inspections GROUP BY work_order_id)"
            " SELECT w.work_order_id, p.pc, l.h, i.n FROM work_orders w"
            " JOIN p USING(work_order_id) JOIN l USING(work_order_id)"
            " JOIN i USING(work_order_id) WHERE w.status = 'closed'"
        ),
        trap_sql=(
            "SELECT w.work_order_id,"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount)),"
            " SUM(le.hours), COUNT(DISTINCT i.inspection_id)"
            " FROM work_orders w"
            " JOIN parts_used pu ON pu.work_order_id = w.work_order_id"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " JOIN inspections i ON i.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' GROUP BY w.work_order_id"
        ),
        note="Three children multiply three ways. COUNT(DISTINCT ...) rescues"
             " the count column but does nothing for the two SUMs -- there is"
             " no DISTINCT that can un-multiply a sum of money or hours.",
    ),
    dict(
        id=8, ledger="Q109", concept="C2", tier="Grain",
        title="Contracts and callouts",
        prompt=(
            "For each customer that has at least one contract and at least one"
            " work order: their total monthly contract fee, and how many work"
            " orders have been raised across all their sites.\n\n"
            "Contracts hang off the customer. Work orders hang off the"
            " customer's sites and machines. They are separate branches.\n\n"
            "Return: customer_id, name, monthly_fee_total, work_orders"
        ),
        solution=(
            "WITH k AS (SELECT customer_id, SUM(monthly_fee) AS fee"
            " FROM contracts GROUP BY customer_id),"
            " w AS (SELECT s.customer_id, COUNT(*) AS n FROM sites s"
            " JOIN machines m ON m.site_id = s.site_id"
            " JOIN work_orders o ON o.machine_id = m.machine_id"
            " GROUP BY s.customer_id)"
            " SELECT c.customer_id, c.name, k.fee, w.n FROM customers c"
            " JOIN k ON k.customer_id = c.customer_id"
            " JOIN w ON w.customer_id = c.customer_id"
        ),
        trap_sql=(
            "SELECT c.customer_id, c.name, SUM(k.monthly_fee), COUNT(*)"
            " FROM customers c"
            " JOIN contracts k ON k.customer_id = c.customer_id"
            " JOIN sites s ON s.customer_id = c.customer_id"
            " JOIN machines m ON m.site_id = s.site_id"
            " JOIN work_orders o ON o.machine_id = m.machine_id"
            " GROUP BY c.customer_id"
        ),
        note="The fan-out is not only about parts and labour. Any two"
             " independent branches off the same parent do it -- here contracts"
             " and the whole sites-machines-work_orders chain.",
    ),
    dict(
        id=9, ledger="Q110", concept="C2", tier="Grain",
        title="Counting down a chain",
        prompt=(
            "For each customer: how many sites they have, how many machines"
            " across those sites, and how many work orders across those"
            " machines.\n\n"
            "Every customer has at least one site, so all of them appear. Two"
            " customers have never had a work order raised and must show 0.\n\n"
            "Return: customer_id, sites, machines, work_orders"
        ),
        solution=(
            "SELECT c.customer_id, COUNT(DISTINCT s.site_id),"
            " COUNT(DISTINCT m.machine_id), COUNT(DISTINCT o.work_order_id)"
            " FROM customers c JOIN sites s ON s.customer_id = c.customer_id"
            " LEFT JOIN machines m ON m.site_id = s.site_id"
            " LEFT JOIN work_orders o ON o.machine_id = m.machine_id"
            " GROUP BY c.customer_id"
        ),
        trap_sql=(
            "SELECT c.customer_id, COUNT(s.site_id), COUNT(m.machine_id),"
            " COUNT(o.work_order_id)"
            " FROM customers c JOIN sites s ON s.customer_id = c.customer_id"
            " LEFT JOIN machines m ON m.site_id = s.site_id"
            " LEFT JOIN work_orders o ON o.machine_id = m.machine_id"
            " GROUP BY c.customer_id"
        ),
        note="Going down a one-to-many chain, each level multiplies the ones"
             " above it. Only COUNT(DISTINCT ...) survives that. Plain COUNT"
             " reports the row count of the widest level every time.",
        claims=[
            ("exactly 2 customers show 0 work orders",
             lambda rows, c: sum(1 for r in rows if r[3] == 0) == 2),
            ("every customer has at least one site",
             lambda rows, c: all(r[1] >= 1 for r in rows)),
        ],
    ),
    dict(
        id=10, ledger="Q111", concept="C2", tier="Grain",
        title="Stock on hand per part",
        prompt=(
            "For every part that is stocked somewhere: the total quantity on"
            " hand across all depots, and how many depots carry it.\n\n"
            "Three parts are stocked in no depot at all and are correctly"
            " absent from the answer.\n\n"
            "Return: part_id, depots_carrying, total_on_hand"
        ),
        solution=(
            "SELECT part_id, COUNT(*), SUM(quantity_on_hand)"
            " FROM part_stock GROUP BY part_id"
        ),
        trap_sql=(
            "SELECT ps.part_id, COUNT(*), SUM(ps.quantity_on_hand)"
            " FROM part_stock ps"
            " JOIN parts_used pu ON pu.part_id = ps.part_id"
            " GROUP BY ps.part_id"
        ),
        note="Nothing in the question needs parts_used, and joining it"
             " multiplies every stock row by the number of times the part was"
             " ever fitted. Join only what the answer actually requires.",
        claims=[
            ("37 parts are stocked somewhere",
             lambda rows, c: len(rows) == 37),
        ],
    ),
    dict(
        id=11, ledger="Q112", concept="C2", tier="Grain",
        title="Invoice against actual cost",
        prompt=(
            "For every invoiced work order that has both parts and labour: the"
            " invoice amount and the true cost of the job, and the difference"
            " between them.\n\n"
            "True cost is parts plus labour. Difference is invoice minus"
            " true cost.\n\n"
            "Return: work_order_id, invoice_amount, true_cost, difference"
        ),
        solution=(
            "WITH p AS (SELECT work_order_id,"
            " SUM(quantity * unit_price * (1 - discount)) AS pc"
            " FROM parts_used GROUP BY work_order_id),"
            " l AS (SELECT work_order_id, SUM(hours * rate) AS lc"
            " FROM labor_entries GROUP BY work_order_id)"
            " SELECT i.work_order_id, i.amount, p.pc + l.lc,"
            " i.amount - (p.pc + l.lc) FROM invoices i"
            " JOIN p USING(work_order_id) JOIN l USING(work_order_id)"
        ),
        trap_sql=(
            "SELECT i.work_order_id, i.amount,"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount))"
            " + SUM(le.hours * le.rate),"
            " i.amount - (SUM(pu.quantity * pu.unit_price * (1 - pu.discount))"
            " + SUM(le.hours * le.rate)) FROM invoices i"
            " JOIN parts_used pu ON pu.work_order_id = i.work_order_id"
            " JOIN labor_entries le ON le.work_order_id = i.work_order_id"
            " GROUP BY i.work_order_id"
        ),
        note="A reconciliation that shows every job massively over-billed is"
             " usually a fan-out, not fraud. The invoice side is one row per"
             " job already; only the cost side needs collapsing.",
        claims=[
            ("the invoice matches the true cost on every job",
             lambda rows, c: all(abs(r[3]) < 0.01 for r in rows)),
        ],
    ),
    dict(
        id=12, ledger="Q113", concept="C2", tier="Grain",
        title="Technician workload",
        prompt=(
            "For each technician who has logged any labour: the total hours"
            " they logged, and how many distinct work orders they logged them"
            " against.\n\n"
            "A technician can log several visits to the same job.\n\n"
            "Return: technician_id, name, total_hours, jobs_touched"
        ),
        solution=(
            "SELECT t.technician_id, t.name, SUM(le.hours),"
            " COUNT(DISTINCT le.work_order_id) FROM technicians t"
            " JOIN labor_entries le ON le.technician_id = t.technician_id"
            " GROUP BY t.technician_id"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, SUM(le.hours),"
            " COUNT(le.work_order_id) FROM technicians t"
            " JOIN labor_entries le ON le.technician_id = t.technician_id"
            " GROUP BY t.technician_id"
        ),
        note="COUNT(col) counts rows where col is not null, which here is"
             " visits, not jobs. Whenever the question says 'distinct' or"
             " 'how many different', the word belongs inside the COUNT.",
    ),
    dict(
        id=13, ledger="Q114", concept="C2", tier="Grain",
        title="Depot stock and staff",
        prompt=(
            "For each depot: how many technicians are based there, and the"
            " total quantity of stock it holds across all part lines.\n\n"
            "Technicians and stock lines are separate children of the depot.\n\n"
            "Return: depot_id, name, technicians, total_stock"
        ),
        solution=(
            "WITH t AS (SELECT depot_id, COUNT(*) AS n FROM technicians"
            " GROUP BY depot_id),"
            " s AS (SELECT depot_id, SUM(quantity_on_hand) AS q"
            " FROM part_stock GROUP BY depot_id)"
            " SELECT d.depot_id, d.name, t.n, s.q FROM depots d"
            " JOIN t ON t.depot_id = d.depot_id"
            " JOIN s ON s.depot_id = d.depot_id"
        ),
        trap_sql=(
            "SELECT d.depot_id, d.name, COUNT(DISTINCT t.technician_id),"
            " SUM(ps.quantity_on_hand) FROM depots d"
            " JOIN technicians t ON t.depot_id = d.depot_id"
            " JOIN part_stock ps ON ps.depot_id = d.depot_id"
            " GROUP BY d.depot_id"
        ),
        note="COUNT(DISTINCT ...) fixed the headcount but the stock total is"
             " still multiplied by the number of technicians. DISTINCT protects"
             " counts, never sums.",
    ),
    dict(
        id=14, ledger="Q115", concept="C2", tier="Grain",
        title="Cost per hour on the job",
        prompt=(
            "For closed work orders with both parts and labour: the parts cost"
            " per labour hour.\n\n"
            "That is total parts cost divided by total hours -- each worked out"
            " over the whole job, not line by line.\n\n"
            "Return: work_order_id, parts_cost_per_hour"
        ),
        solution=(
            "WITH p AS (SELECT work_order_id,"
            " SUM(quantity * unit_price * (1 - discount)) AS pc"
            " FROM parts_used GROUP BY work_order_id),"
            " l AS (SELECT work_order_id, SUM(hours) AS h"
            " FROM labor_entries GROUP BY work_order_id)"
            " SELECT w.work_order_id, p.pc / l.h FROM work_orders w"
            " JOIN p USING(work_order_id) JOIN l USING(work_order_id)"
            " WHERE w.status = 'closed'"
        ),
        trap_sql=(
            "SELECT w.work_order_id,"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount))"
            " / SUM(le.hours) FROM work_orders w"
            " JOIN parts_used pu ON pu.work_order_id = w.work_order_id"
            " JOIN labor_entries le ON le.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' GROUP BY w.work_order_id"
        ),
        note="Both halves of the ratio are inflated, but by different factors,"
             " so the result is wrong rather than merely scaled. A ratio built"
             " from two fanned-out sums cannot be rescued by dividing.",
    ),
    dict(
        id=15, ledger="Q116", concept="C2", tier="Grain",
        title="Busiest machines",
        prompt=(
            "The 5 machines with the most work orders raised against them,"
            " showing the model and the owning customer.\n\n"
            "Order by the work order count highest first, then by machine_id"
            " ascending so ties are settled.\n\n"
            "Return: machine_id, model, customer_name, work_orders"
        ),
        solution=(
            "WITH w AS (SELECT machine_id, COUNT(*) AS n FROM work_orders"
            " GROUP BY machine_id)"
            " SELECT m.machine_id, m.model, c.name, w.n FROM w"
            " JOIN machines m ON m.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = m.site_id"
            " JOIN customers c ON c.customer_id = s.customer_id"
            " ORDER BY w.n DESC, m.machine_id ASC LIMIT 5"
        ),
        trap_sql=(
            "SELECT m.machine_id, m.model, c.name, COUNT(*)"
            " FROM machines m JOIN sites s ON s.site_id = m.site_id"
            " JOIN customers c ON c.customer_id = s.customer_id"
            " JOIN work_orders o ON o.machine_id = m.machine_id"
            " JOIN labor_entries le ON le.work_order_id = o.work_order_id"
            " GROUP BY m.machine_id ORDER BY COUNT(*) DESC, m.machine_id ASC"
            " LIMIT 5"
        ),
        note="Dragging in labor_entries to 'get more detail' changes what is"
             " being counted from jobs to visits, and reorders the top 5. Only"
             " join a table when the answer needs a column from it.",
    ),
    # ------------------------------------------------------------- windows
    dict(
        id=16, ledger="Q117", concept="C3", tier="Window vs GROUP BY",
        title="Each visit against the job total",
        prompt=(
            "Every labour entry on work order 2, showing the hours on that"
            " visit and the total hours across the whole job on every row.\n\n"
            "The total is the same value on all of the job's rows -- the"
            " individual visits are not collapsed.\n\n"
            "Return: entry_id, work_date, hours, job_total_hours"
        ),
        solution=(
            "SELECT entry_id, work_date, hours,"
            " SUM(hours) OVER (PARTITION BY work_order_id)"
            " FROM labor_entries WHERE work_order_id = 2"
        ),
        trap_sql=(
            "SELECT entry_id, work_date, hours,"
            " SUM(hours) OVER (PARTITION BY work_order_id ORDER BY work_date)"
            " FROM labor_entries WHERE work_order_id = 2"
        ),
        note="Adding ORDER BY inside OVER() changes the frame from the whole"
             " partition to everything up to the current row, turning a"
             " partition total into a running total. Leave it out when you"
             " want the total.",
    ),
    dict(
        id=17, ledger="Q118", concept="C3", tier="Window vs GROUP BY",
        title="First visit to each job",
        prompt=(
            "For every work order that has labour logged: the details of its"
            " earliest visit.\n\n"
            "Jobs can have two visits on the same date. Where that happens,"
            " take the one with the lower entry_id, so exactly one row comes"
            " back per work order.\n\n"
            "Return: work_order_id, entry_id, work_date, hours"
        ),
        solution=(
            "WITH r AS (SELECT work_order_id, entry_id, work_date, hours,"
            " ROW_NUMBER() OVER (PARTITION BY work_order_id"
            " ORDER BY work_date ASC, entry_id ASC) AS rn"
            " FROM labor_entries)"
            " SELECT work_order_id, entry_id, work_date, hours FROM r"
            " WHERE rn = 1"
        ),
        trap_sql=(
            "WITH r AS (SELECT work_order_id, entry_id, work_date, hours,"
            " RANK() OVER (PARTITION BY work_order_id"
            " ORDER BY work_date ASC) AS rn"
            " FROM labor_entries)"
            " SELECT work_order_id, entry_id, work_date, hours FROM r"
            " WHERE rn = 1"
        ),
        note="RANK() gives tied rows the same number, so 'rank = 1' returns two"
             " rows when two visits share a date. ROW_NUMBER() always breaks"
             " the tie -- which is why its ORDER BY needs a tiebreak column.",
        claims=[
            ("one row per work order that has labour",
             lambda rows, c: len(rows) == c.execute(
                 "SELECT COUNT(DISTINCT work_order_id) FROM labor_entries"
             ).fetchone()[0]),
        ],
    ),
    dict(
        id=18, ledger="Q119", concept="C3", tier="Window vs GROUP BY",
        title="Running spend per depot",
        prompt=(
            "Every stock line in depot 2, ordered by part_id, with a running"
            " total of quantity on hand accumulating down that order.\n\n"
            "The first row's running total equals its own quantity; the last"
            " row's equals the depot's whole stock.\n\n"
            "Return: part_id, quantity_on_hand, running_total"
        ),
        solution=(
            "SELECT part_id, quantity_on_hand,"
            " SUM(quantity_on_hand) OVER (ORDER BY part_id"
            " ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"
            " FROM part_stock WHERE depot_id = 2"
        ),
        trap_sql=(
            "SELECT part_id, quantity_on_hand,"
            " SUM(quantity_on_hand) OVER ()"
            " FROM part_stock WHERE depot_id = 2"
        ),
        note="OVER() with no ORDER BY frames the whole partition, giving the"
             " same grand total on every row. The running total needs the"
             " ORDER BY -- the opposite of the previous question, which is"
             " exactly why the two get confused.",
    ),
    # ------------------------------------------------------ aggregates/WHERE
    dict(
        id=19, ledger="Q120", concept="C1", tier="Aggregates in WHERE",
        title="Jobs that ran long",
        prompt=(
            "Work orders that took more than 3 visits to close, with the visit"
            " count and total hours.\n\n"
            "Only closed jobs count.\n\n"
            "Return: work_order_id, visits, total_hours"
        ),
        solution=(
            "SELECT le.work_order_id, COUNT(*), SUM(le.hours)"
            " FROM labor_entries le"
            " JOIN work_orders w ON w.work_order_id = le.work_order_id"
            " WHERE w.status = 'closed'"
            " GROUP BY le.work_order_id HAVING COUNT(*) > 3"
        ),
        trap_sql=(
            "SELECT le.work_order_id, COUNT(*), SUM(le.hours)"
            " FROM labor_entries le"
            " JOIN work_orders w ON w.work_order_id = le.work_order_id"
            " WHERE w.status = 'closed'"
            " GROUP BY le.work_order_id HAVING COUNT(*) >= 3"
        ),
        note="A condition on an aggregate belongs in HAVING, which runs after"
             " grouping. WHERE runs before, on individual rows, where the"
             " count does not exist yet.",
    ),
    dict(
        id=20, ledger="Q121", concept="C1", tier="Aggregates in WHERE",
        title="Customers worth chasing",
        prompt=(
            "Customers whose unpaid invoices -- anything not PAID -- come to"
            " more than 3000 in total, with the amount outstanding and how many"
            " invoices make it up.\n\n"
            "An invoice belongs to a customer through its work order, machine"
            " and site.\n\n"
            "Return: customer_id, name, unpaid_invoices, amount_outstanding"
        ),
        solution=(
            "SELECT c.customer_id, c.name, COUNT(*), SUM(i.amount)"
            " FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines m ON m.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = m.site_id"
            " JOIN customers c ON c.customer_id = s.customer_id"
            " WHERE i.status <> 'PAID'"
            " GROUP BY c.customer_id HAVING SUM(i.amount) > 3000"
        ),
        trap_sql=(
            "SELECT c.customer_id, c.name, COUNT(*), SUM(i.amount)"
            " FROM invoices i"
            " JOIN work_orders w ON w.work_order_id = i.work_order_id"
            " JOIN machines m ON m.machine_id = w.machine_id"
            " JOIN sites s ON s.site_id = m.site_id"
            " JOIN customers c ON c.customer_id = s.customer_id"
            " WHERE i.status <> 'PAID' AND i.amount > 3000"
            " GROUP BY c.customer_id"
        ),
        note="'Total more than 3000' is a condition on the group. Filtering"
             " individual invoices over 3000 in WHERE answers a different"
             " question and quietly drops customers with many small debts.",
    ),
    # ------------------------------------------------------------ CTE scope
    dict(
        id=21, ledger="Q122", concept="C4", tier="CTE scope",
        title="Carry it through the wall",
        prompt=(
            "Closed work orders whose parts cost is above 1200, showing the"
            " machine's model and the priority the job was raised at.\n\n"
            "Build the parts cost in a CTE first.\n\n"
            "Return: work_order_id, model, priority, parts_cost"
        ),
        solution=(
            "WITH p AS (SELECT pu.work_order_id, w.priority, w.machine_id,"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount)) AS pc"
            " FROM parts_used pu"
            " JOIN work_orders w ON w.work_order_id = pu.work_order_id"
            " WHERE w.status = 'closed' GROUP BY pu.work_order_id)"
            " SELECT p.work_order_id, m.model, p.priority, p.pc FROM p"
            " JOIN machines m ON m.machine_id = p.machine_id WHERE p.pc > 1200"
        ),
        trap_sql=(
            "WITH p AS (SELECT pu.work_order_id,"
            " SUM(pu.quantity * pu.unit_price * (1 - pu.discount)) AS pc"
            " FROM parts_used pu"
            " JOIN work_orders w ON w.work_order_id = pu.work_order_id"
            " WHERE w.status = 'closed' GROUP BY pu.work_order_id)"
            " SELECT p.work_order_id, m.model, w.priority, p.pc FROM p"
            " JOIN machines m ON m.machine_id = p.machine_id WHERE p.pc > 1200"
        ),
        note="The CTE is a wall: the outer query sees only the columns the CTE"
             " selected, never the tables behind it. List what the outer query"
             " needs before you write the CTE.",
    ),
    # --------------------------------------------------------------- COUNT
    dict(
        id=22, ledger="Q123", concept="C5", tier="COUNT",
        title="Inspected, or not",
        prompt=(
            "Every closed work order, with how many inspections it received."
            " Jobs never inspected must show 0, not vanish.\n\n"
            "Return: work_order_id, inspections"
        ),
        solution=(
            "SELECT w.work_order_id, COUNT(i.inspection_id)"
            " FROM work_orders w"
            " LEFT JOIN inspections i ON i.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' GROUP BY w.work_order_id"
        ),
        trap_sql=(
            "SELECT w.work_order_id, COUNT(*)"
            " FROM work_orders w"
            " LEFT JOIN inspections i ON i.work_order_id = w.work_order_id"
            " WHERE w.status = 'closed' GROUP BY w.work_order_id"
        ),
        note="A LEFT JOIN that finds nothing still produces one row, with NULLs"
             " in the right-hand columns. COUNT(*) counts that phantom row as"
             " 1; COUNT(i.inspection_id) skips the NULL and gives 0.",
        claims=[
            ("23 closed jobs were never inspected and show 0",
             lambda rows, c: sum(1 for r in rows if r[1] == 0) == 23),
        ],
    ),
    dict(
        id=23, ledger="Q124", concept="C5", tier="COUNT",
        title="Scored and unscored",
        prompt=(
            "For each inspection result -- pass, fail, conditional -- how many"
            " inspections were recorded, how many carried a numeric score, and"
            " the average of those scores.\n\n"
            "Some inspectors record a verdict without a score.\n\n"
            "Return: result, inspections, with_score, avg_score"
        ),
        solution=(
            "SELECT result, COUNT(*), COUNT(score), AVG(score)"
            " FROM inspections GROUP BY result"
        ),
        trap_sql=(
            "SELECT result, COUNT(*), COUNT(*), AVG(COALESCE(score, 0))"
            " FROM inspections GROUP BY result"
        ),
        note="COUNT(*) counts rows, COUNT(score) counts non-NULL scores, and"
             " AVG(score) divides by the latter. Coalescing NULL to 0 first"
             " drags the average down by inventing scores nobody gave.",
        claims=[
            ("some inspections have no score",
             lambda rows, c: any(r[1] > r[2] for r in rows)),
        ],
    ),
    # ---------------------------------------------------------------- NULLs
    dict(
        id=24, ledger="Q125", concept="C7", tier="NULLs",
        title="Slow to answer",
        prompt=(
            "Contracts with an agreed response time of more than 24 hours,"
            " showing the customer.\n\n"
            "Four contracts never agreed a response time at all. An unknown"
            " response time is not a slow one, so those must not appear.\n\n"
            "Return: contract_id, customer_name, response_hours"
        ),
        solution=(
            "SELECT k.contract_id, c.name, k.response_hours FROM contracts k"
            " JOIN customers c ON c.customer_id = k.customer_id"
            " WHERE k.response_hours > 24"
        ),
        trap_sql=(
            "SELECT k.contract_id, c.name, k.response_hours FROM contracts k"
            " JOIN customers c ON c.customer_id = k.customer_id"
            " WHERE COALESCE(k.response_hours, 999) > 24"
        ),
        note="NULL > 24 is not true, so those rows drop out on their own -- the"
             " comparison already does the right thing. Coalescing to a big"
             " number forces unknowns into the answer as though they were the"
             " worst offenders.",
    ),
    dict(
        id=25, ledger="Q126", concept="C7", tier="NULLs",
        title="Never certified",
        prompt=(
            "Technicians who have not been certified, with their depot and how"
            " many labour hours they have logged.\n\n"
            "A technician with no certification has cert_level NULL. Every one"
            " of them has logged some labour.\n\n"
            "Return: technician_id, name, depot_name, total_hours"
        ),
        solution=(
            "SELECT t.technician_id, t.name, d.name, SUM(le.hours)"
            " FROM technicians t JOIN depots d ON d.depot_id = t.depot_id"
            " JOIN labor_entries le ON le.technician_id = t.technician_id"
            " WHERE t.cert_level IS NULL GROUP BY t.technician_id"
        ),
        trap_sql=(
            "SELECT t.technician_id, t.name, d.name, SUM(le.hours)"
            " FROM technicians t JOIN depots d ON d.depot_id = t.depot_id"
            " JOIN labor_entries le ON le.technician_id = t.technician_id"
            " WHERE t.cert_level = NULL GROUP BY t.technician_id"
        ),
        note="Nothing equals NULL, not even NULL -- 'cert_level = NULL' is"
             " never true and returns no rows at all. Use IS NULL.",
        claims=[
            ("4 technicians are uncertified",
             lambda rows, c: len(rows) == 4),
        ],
    ),
    dict(
        id=26, ledger="Q127", concept="C7", tier="NULLs",
        title="Parts nobody has fitted",
        prompt=(
            "Parts that have never been used on any work order, with their"
            " category and unit cost.\n\n"
            "Return: part_id, name, category, unit_cost"
        ),
        solution=(
            "SELECT p.part_id, p.name, p.category, p.unit_cost FROM parts p"
            " WHERE NOT EXISTS (SELECT 1 FROM parts_used pu"
            " WHERE pu.part_id = p.part_id)"
        ),
        trap_sql=(
            "SELECT p.part_id, p.name, p.category, p.unit_cost FROM parts p"
            " LEFT JOIN parts_used pu ON pu.part_id = p.part_id"
            " WHERE pu.quantity = 0"
        ),
        note="An anti-join needs NOT EXISTS, or a LEFT JOIN with 'IS NULL' on"
             " the right-hand key. Testing a right-hand column for a value"
             " never matches, because unmatched rows hold NULL, not 0.",
        claims=[
            ("2 parts have never been fitted",
             lambda rows, c: len(rows) == 2),
        ],
    ),
    # ----------------------------------------------------- integer division
    dict(
        id=27, ledger="Q128", concept="C9", tier="Integer division",
        title="Average parts per job",
        prompt=(
            "For each work order priority, the average number of part lines per"
            " work order that used parts.\n\n"
            "Both the part count and the job count are integers. The answer is"
            " not a whole number -- 'critical' comes to 2.64.\n\n"
            "Return: priority, jobs, part_lines, avg_lines_per_job"
        ),
        solution=(
            "WITH p AS (SELECT work_order_id, COUNT(*) AS n FROM parts_used"
            " GROUP BY work_order_id)"
            " SELECT w.priority, COUNT(*), SUM(p.n), SUM(p.n) * 1.0 / COUNT(*)"
            " FROM work_orders w JOIN p USING(work_order_id)"
            " GROUP BY w.priority"
        ),
        trap_sql=(
            "WITH p AS (SELECT work_order_id, COUNT(*) AS n FROM parts_used"
            " GROUP BY work_order_id)"
            " SELECT w.priority, COUNT(*), SUM(p.n), SUM(p.n) / COUNT(*)"
            " FROM work_orders w JOIN p USING(work_order_id)"
            " GROUP BY w.priority"
        ),
        note="Integer divided by integer truncates in SQLite: 8/3 is 2, not"
             " 2.67. Multiply one side by 1.0 -- or use CAST -- before"
             " dividing. The result looks plausible, which is the danger.",
        claims=[
            ("at least one average is not a whole number",
             lambda rows, c: any(abs(r[3] - round(r[3])) > 0.01 for r in rows)),
            ("'critical' averages 2.64 part lines per job",
             lambda rows, c: any(r[0] == "critical" and abs(r[3] - 2.64) < 0.005
                                 for r in rows)),
        ],
    ),
    dict(
        id=28, ledger="Q129", concept="C9", tier="Integer division",
        title="Stock cover against reorder level",
        prompt=(
            "Stock lines that have a reorder level set, showing quantity on"
            " hand as a multiple of that level.\n\n"
            "Lines with no agreed reorder policy are excluded. Report the"
            " multiple to full precision, not rounded down.\n\n"
            "Return: depot_id, part_id, quantity_on_hand, reorder_level, cover"
        ),
        solution=(
            "SELECT depot_id, part_id, quantity_on_hand, reorder_level,"
            " quantity_on_hand * 1.0 / reorder_level FROM part_stock"
            " WHERE reorder_level IS NOT NULL"
        ),
        trap_sql=(
            "SELECT depot_id, part_id, quantity_on_hand, reorder_level,"
            " quantity_on_hand / reorder_level FROM part_stock"
            " WHERE reorder_level IS NOT NULL"
        ),
        note="Both columns are INTEGER, so the division truncates and every"
             " partial cover reads as a whole multiple. A stock line at 1.9x"
             " its reorder level reports 1.",
    ),
    # -------------------------------------------------------------- general
    dict(
        id=29, ledger="Q130", concept="GEN", tier="General",
        title="Who reports to whom",
        prompt=(
            "Every technician who has a supervisor, with the supervisor's name"
            " and how much longer the supervisor has been employed, in whole"
            " days.\n\n"
            "One technician is the depot manager and reports to nobody, so does"
            " not appear.\n\n"
            "Return: technician_name, supervisor_name, supervisor_extra_days"
        ),
        solution=(
            "SELECT t.name, s.name,"
            " CAST(julianday(t.hired_on) - julianday(s.hired_on) AS INTEGER)"
            " FROM technicians t"
            " JOIN technicians s ON s.technician_id = t.supervisor_id"
        ),
        trap_sql=(
            "SELECT t.name, s.name,"
            " CAST(julianday(t.hired_on) - julianday(s.hired_on) AS INTEGER)"
            " FROM technicians t"
            " LEFT JOIN technicians s ON s.technician_id = t.supervisor_id"
        ),
        note="A self-join needs two aliases of the same table. Using LEFT JOIN"
             " keeps the one technician who reports to nobody, with NULLs"
             " where the supervisor should be.",
        claims=[
            ("13 of the 14 technicians have a supervisor",
             lambda rows, c: len(rows) == 13),
        ],
    ),
    dict(
        id=30, ledger="Q131", concept="GEN", tier="General",
        title="How long jobs stay open",
        prompt=(
            "For each priority, how many jobs were closed and the average whole"
            " days from opening to closing.\n\n"
            "Only jobs that actually closed count -- open and cancelled ones"
            " both have closed_at NULL and must be excluded.\n\n"
            "Return: priority, closed_jobs, avg_days_open"
        ),
        solution=(
            "SELECT priority, COUNT(*),"
            " AVG(julianday(closed_at) - julianday(opened_at))"
            " FROM work_orders WHERE closed_at IS NOT NULL GROUP BY priority"
        ),
        trap_sql=(
            "SELECT priority, COUNT(*),"
            " AVG(julianday(closed_at) - julianday(opened_at))"
            " FROM work_orders GROUP BY priority"
        ),
        note="AVG skips NULL rows but COUNT(*) does not, so leaving the open"
             " jobs in inflates the job count while the average stays right."
             " Filter them out explicitly.",
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
