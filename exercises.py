"""Practice exercises: fifteen questions on the parcel-courier schema.

The eighth set on the courier scheme (SEED 1241), nine questions that
read and six that change the data, the last three of them procedures. The
tiers are named by task, the tools are ones the first seven courier sets
left out, and the prompts name the tool but do not write the statement.
Text, matched and built -- a first name of exactly four letters by LIKE's
one-character wildcard, a postcode ending in two digits by GLOB's
character class, a reference padded with zeros by printf. More from
windows -- record months by a MAX whose frame stops short of the current
row, the same month a year earlier by LAG with an offset, customers with
a namesake by COUNT(*) OVER a partition. Positions, years and thresholds
-- fourth to sixth place by LIMIT with OFFSET, completed years of service
by anniversary arithmetic, customers at or above several levels by a
join on >=.

Changing rows, three single statements:

  * an INSERT of two rows whose foreign key is looked up, not typed
  * an UPDATE whose SET holds a correlated subquery
  * a DELETE whose WHERE says 'neither of these' the right way

Procedures, three scripts of several steps. SQLite has no CREATE
PROCEDURE; what it has is a transaction, whose steps stand or fall
together, and a trigger body, which is stored and runs when called:

  * a table rebuilt to add a CHECK: create, copy, drop, rename
  * a depot opened and staffed, its new id read by last_insert_rowid()
  * a BEFORE DELETE trigger that records a parcel's trail and clears it

Each writable question runs in a private in-memory copy of the database,
so nothing you write can reach the real file. The copy persists across
Runs of one question -- run an UPDATE, then a SELECT to see what it did --
and is discarded by Reset or by moving to another question, so no question
can depend on what another one wrote. Check answer always grades a FRESH
copy. The question's `probe_sql` then reads the result, and that is what
is compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script.
"""

import sqlite3

EXERCISES = [
    # ============================================== 1 Text, matched and built
    dict(
        id=1, ledger="Q1327", concept="LIKE1", tier="1 - Text, matched and built",
        title="First names of exactly four letters",
        prompt=(
            "A personal customer's name is a first name, one space, and"
            " a surname. For each first name of exactly FOUR letters:"
            " how many personal customers have it. In a LIKE pattern %"
            " is any run of characters; there is a second wildcard that"
            " stands for exactly one.\n\n"
            "Return: first_name, customers"
        ),
        solution=("SELECT SUBSTR(name, 1, 4) AS first_name, COUNT(*) FROM customers"
                  " WHERE kind = 'personal' AND name LIKE '____ %' GROUP BY first_name"),
        trap_sql=("SELECT SUBSTR(name, 1, 4) AS first_name, COUNT(*) FROM customers"
                  " WHERE kind = 'personal' AND name LIKE '____%' GROUP BY first_name"),
        note="An underscore in a LIKE pattern matches exactly one"
             " character, any character. Four of them and then a space"
             " pin the space to the fifth position, which is what"
             " 'four letters' means; the % takes the surname. Without"
             " the space, the trap, the pattern is 'at least four"
             " characters' -- nearly everybody -- and the first four"
             " letters of Dmitri and Imogen are counted as names."
             " LENGTH and INSTR could do it too; the pattern says it"
             " in one go.",
        claims=[("three names: Rosa, Umar and Zara",
                 lambda rows, c: sorted(r[0] for r in rows) == ["Rosa", "Umar", "Zara"]),
                ("17 customers called Zara",
                 lambda rows, c: ("Zara", 17) in rows)],
    ),
    dict(
        id=2, ledger="Q1328", concept="GLOB", tier="1 - Text, matched and built",
        title="Postcode areas that end in two digits",
        prompt=(
            "For each depot, by name: how many of its customers have a"
            " postcode_area that ENDS IN TWO DIGITS, like DE22. LIKE"
            " has no way to say 'a digit'. GLOB has: a character class"
            " in square brackets. Its wildcard for 'anything' is * and"
            " not %.\n\n"
            "Return: depot, customers"
        ),
        solution=("SELECT d.name, COUNT(*) FROM customers c JOIN depots d ON d.depot_id = c.depot_id"
                  " WHERE c.postcode_area GLOB '*[0-9][0-9]' GROUP BY d.name"),
        trap_sql=("SELECT d.name, COUNT(*) FROM customers c JOIN depots d ON d.depot_id = c.depot_id"
                  " WHERE c.postcode_area GLOB '*[0-9]' GROUP BY d.name"),
        note="GLOB uses the shell's wildcards: * for any run, ? for one"
             " character, and [0-9] for one character out of a set."
             " Two classes at the end demand two digits; one, the"
             " trap, is satisfied by every area there is, since they"
             " all end in a digit. Unlike LIKE, GLOB is case-sensitive,"
             " so [A-Z] means capitals only. The customers with no"
             " postcode_area drop out by themselves: NULL matches no"
             " pattern.",
        claims=[("ten depots, 42 customers in all",
                 lambda rows, c: len(rows) == 10 and sum(r[1] for r in rows) == 42),
                ("Hillcrest has the most, seven",
                 lambda rows, c: max(rows, key=lambda r: r[1]) == ("Hillcrest", 7))],
    ),
    dict(
        id=3, ledger="Q1329", concept="PAD", tier="1 - Text, matched and built",
        title="A reference number for the reminder letters",
        prompt=(
            "Every UNPAID invoice for period 2026-05 needs a reference:"
            " 'INV-', the period, a hyphen, and the customer_id padded"
            " with zeros to FIVE digits -- INV-2026-05-00004 for"
            " customer 4. printf pads a number; || joins the pieces.\n\n"
            "Return: reference, amount_cents"
        ),
        solution=("SELECT 'INV-' || period || '-' || printf('%05d', customer_id), amount_cents"
                  " FROM invoices WHERE period = '2026-05' AND paid_on IS NULL"),
        trap_sql=("SELECT 'INV-' || period || '-' || customer_id, amount_cents"
                  " FROM invoices WHERE period = '2026-05' AND paid_on IS NULL"),
        note="In a printf format %d is a whole number, 5 is the"
             " minimum width, and the 0 in front says fill the width"
             " with zeros and not spaces. Fixed-width references sort"
             " correctly as text and are hard to misread; the trap's"
             " INV-2026-05-4 sorts after INV-2026-05-12. || turns a"
             " number into text as it joins, which is why the unpadded"
             " version runs at all. SUBSTR('00000' || id, -5) is the"
             " same trick without printf.",
        claims=[("76 references, every one seventeen characters long",
                 lambda rows, c: len(rows) == 76 and all(len(r[0]) == 17 for r in rows)),
                ("customer 4 owes 2,000 cents under INV-2026-05-00004",
                 lambda rows, c: ("INV-2026-05-00004", 2000) in rows)],
    ),
    # ==================================================== 2 More from windows
    dict(
        id=4, ledger="Q1330", concept="RECORD", tier="2 - More from windows",
        title="The months that set a record",
        prompt=(
            "A record month is one in which more parcels were collected"
            " than in ANY earlier month. List the record months, each"
            " with the best figure it had to beat. The first month of"
            " the data has nothing to beat and is not listed. A window"
            " MAX whose frame stops one row BEFORE the current one.\n\n"
            "Return: month, parcels, previous_best"
        ),
        solution=("SELECT m, n, best FROM (SELECT m, n, MAX(n) OVER (ORDER BY m"
                  " ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS best"
                  " FROM (SELECT strftime('%Y-%m', collected_at) AS m, COUNT(*) AS n FROM parcels GROUP BY m))"
                  " WHERE n > best"),
        trap_sql=("SELECT m, n, best FROM (SELECT m, n, LAG(n) OVER (ORDER BY m) AS best"
                  " FROM (SELECT strftime('%Y-%m', collected_at) AS m, COUNT(*) AS n FROM parcels GROUP BY m))"
                  " WHERE n > best"),
        note="A frame says which rows around the current one a window"
             " function may see. UNBOUNDED PRECEDING AND 1 PRECEDING is"
             " everything before this row and not this row, so MAX is"
             " the best so far and the comparison is honest; with the"
             " default frame the current month is included and nothing"
             " ever beats itself. LAG, the trap, looks back one month"
             " only and reports every month that improved on the last,"
             " record or not. The first month's frame is empty, its"
             " MAX is NULL, and n > NULL filters it out.",
        claims=[("seven record months, the last 2026-03 beating 1,543",
                 lambda rows, c: len(rows) == 7 and max(rows) == ("2026-03", 1565, 1543)),
                ("2025-03 was the first, beating January's 1,099",
                 lambda rows, c: min(rows) == ("2025-03", 1120, 1099))],
    ),
    dict(
        id=5, ledger="Q1331", concept="YOY", tier="2 - More from windows",
        title="This month against the same month last year",
        prompt=(
            "For each month that has one: the parcels collected, and"
            " the parcels collected in the SAME month a year earlier."
            " Months with no such earlier month are not listed. No"
            " month is missing from the data. LAG takes a second"
            " argument.\n\n"
            "Return: month, parcels, a_year_earlier"
        ),
        solution=("SELECT m, n, last_year FROM (SELECT m, n, LAG(n, 12) OVER (ORDER BY m) AS last_year"
                  " FROM (SELECT strftime('%Y-%m', collected_at) AS m, COUNT(*) AS n FROM parcels GROUP BY m))"
                  " WHERE last_year IS NOT NULL"),
        trap_sql=("SELECT m, n, last_year FROM (SELECT m, n, LAG(n) OVER (ORDER BY m) AS last_year"
                  " FROM (SELECT strftime('%Y-%m', collected_at) AS m, COUNT(*) AS n FROM parcels GROUP BY m))"
                  " WHERE last_year IS NOT NULL"),
        note="LAG(x, 12) reads the row twelve places back, which is the"
             " same month last year as long as every month has a row"
             " -- the promise the question makes, and the thing to"
             " check on real data. Plain LAG, the trap, is last month:"
             " seventeen rows of month-on-month where six of"
             " year-on-year were asked for. A third argument would"
             " supply a default where there is nothing to look back"
             " to; here those rows are simply filtered out.",
        claims=[("six months, January to June 2026",
                 lambda rows, c: [r[0] for r in sorted(rows)] == ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]),
                ("June 2026 had 1,523 against 1,202 a year before",
                 lambda rows, c: ("2026-06", 1523, 1202) in rows)],
    ),
    dict(
        id=6, ledger="Q1332", concept="NAMESAKE", tier="2 - More from windows",
        title="Customers who share their name with another",
        prompt=(
            "Some customers have exactly the same name as another"
            " customer, anywhere in the company. For each depot, by"
            " name: how many of its customers have such a namesake. A"
            " window COUNT partitioned by name puts the size of each"
            " name's group on every row, without collapsing the"
            " rows.\n\n"
            "Return: depot, customers"
        ),
        solution=("SELECT d.name, COUNT(*) FROM (SELECT depot_id, COUNT(*) OVER (PARTITION BY name) AS same_name"
                  " FROM customers) x JOIN depots d ON d.depot_id = x.depot_id WHERE x.same_name > 1 GROUP BY d.name"),
        trap_sql=("SELECT d.name, COUNT(*) FROM (SELECT depot_id, COUNT(*) OVER (PARTITION BY name, depot_id) AS same_name"
                  " FROM customers) x JOIN depots d ON d.depot_id = x.depot_id WHERE x.same_name > 1 GROUP BY d.name"),
        note="GROUP BY name HAVING COUNT(*) > 1 finds the shared names"
             " and loses the customers; COUNT(*) OVER (PARTITION BY"
             " name) keeps every customer's row and writes the count"
             " beside it, so the row can still be filtered and then"
             " grouped by something else. The trap adds depot_id to the"
             " partition and so counts only namesakes at the SAME"
             " depot, twenty customers where there are 235. The window"
             " runs before the outer WHERE, which is why it sits in a"
             " subquery.",
        claims=[("ten depots, 235 customers with a namesake",
                 lambda rows, c: len(rows) == 10 and sum(r[1] for r in rows) == 235),
                ("Harbour Point has the most, 32",
                 lambda rows, c: max(rows, key=lambda r: r[1]) == ("Harbour Point", 32))],
    ),
    # ====================================== 3 Positions, years and thresholds
    dict(
        id=7, ledger="Q1333", concept="OFFSET", tier="3 - Positions, years and thresholds",
        title="Fourth, fifth and sixth place",
        prompt=(
            "Rank the couriers by parcels delivered, most first. Return"
            " the three in 4th, 5th and 6th place. No two of the top"
            " ten are tied. LIMIT has a partner that skips rows"
            " first.\n\n"
            "Return: courier, deliveries"
        ),
        solution=("SELECT c.name, COUNT(*) AS n FROM parcels p JOIN couriers c ON c.courier_id = p.courier_id"
                  " GROUP BY c.courier_id ORDER BY n DESC, c.courier_id LIMIT 3 OFFSET 3"),
        trap_sql=("SELECT c.name, COUNT(*) AS n FROM parcels p JOIN couriers c ON c.courier_id = p.courier_id"
                  " GROUP BY c.courier_id ORDER BY n DESC, c.courier_id LIMIT 3 OFFSET 4"),
        note="OFFSET is how many rows to skip, not where to start: to"
             " begin at 4th place you skip 3. The trap skips four and"
             " returns 5th to 7th, the off-by-one every paging query"
             " is one keystroke from. LIMIT 3 OFFSET 3 can also be"
             " written LIMIT 3, 3 -- offset first, which is the wrong"
             " way round often enough to avoid. Without an ORDER BY"
             " that leaves no ties, which rows are 'the fourth to"
             " sixth' is not defined at all.",
        claims=[("Samir Chowdhury, Tamsin Achebe and Samir Lindqvist",
                 lambda rows, c: sorted(rows, key=lambda r: -r[1]) == [("Samir Chowdhury", 643), ("Tamsin Achebe", 620), ("Samir Lindqvist", 578)])],
    ),
    dict(
        id=8, ledger="Q1334", concept="YEARS", tier="3 - Positions, years and thresholds",
        title="Completed years of service",
        prompt=(
            "For couriers still employed: their COMPLETED years of"
            " service on 2026-06-30, counted the way a birthday is --"
            " a year counts only once its anniversary has come -- and"
            " how many couriers have each number. Subtracting the"
            " years is one too many for anyone whose anniversary falls"
            " later in the year; comparing the 'MM-DD' parts as text"
            " says who.\n\n"
            "Return: years, couriers"
        ),
        solution=("SELECT 2026 - CAST(strftime('%Y', hired_on) AS INTEGER) - ('06-30' < strftime('%m-%d', hired_on)) AS years,"
                  " COUNT(*) FROM couriers WHERE left_on IS NULL GROUP BY years"),
        trap_sql=("SELECT 2026 - CAST(strftime('%Y', hired_on) AS INTEGER) AS years,"
                  " COUNT(*) FROM couriers WHERE left_on IS NULL GROUP BY years"),
        note="A comparison is 1 or 0 in SQLite, so subtracting ('06-30'"
             " < the hiring MM-DD) takes one year off exactly those"
             " whose anniversary is still to come. The trap is the"
             " plain difference of the years: someone hired in"
             " November 2025 has 'one year' of service after seven"
             " months, and nobody has zero. Dividing a difference in"
             " days by 365 is nearly right and goes wrong around leap"
             " years; this is the same calculation as an age from a"
             " date of birth.",
        claims=[("nine different lengths of service, four couriers under a year",
                 lambda rows, c: len(rows) == 9 and (0, 4) in rows),
                ("nine couriers have three years",
                 lambda rows, c: (3, 9) in rows and sum(r[1] for r in rows) == 45)],
    ),
    dict(
        id=9, ledger="Q1335", concept="ATLEAST", tier="3 - Positions, years and thresholds",
        title="How many customers reach each level",
        prompt=(
            "How many customers have sent AT LEAST 10 parcels? At"
            " least 15, 20, 25, 30, 100? One row per level; a customer"
            " with 40 parcels is counted at five of them. Walk-ins are"
            " left out. A join does not have to be on equality: put"
            " the six levels in an inline table and join on >=.\n\n"
            "Return: at_least, customers"
        ),
        solution=("WITH levels(at_least) AS (VALUES (10), (15), (20), (25), (30), (100)),"
                  " sent AS (SELECT customer_id, COUNT(*) AS n FROM parcels WHERE customer_id IS NOT NULL GROUP BY customer_id)"
                  " SELECT l.at_least, COUNT(*) FROM levels l JOIN sent s ON s.n >= l.at_least GROUP BY l.at_least"),
        trap_sql=("SELECT CASE WHEN n >= 100 THEN 100 WHEN n >= 30 THEN 30 WHEN n >= 25 THEN 25"
                  " WHEN n >= 20 THEN 20 WHEN n >= 15 THEN 15 ELSE 10 END AS at_least, COUNT(*)"
                  " FROM (SELECT customer_id, COUNT(*) AS n FROM parcels WHERE customer_id IS NOT NULL GROUP BY customer_id)"
                  " WHERE n >= 10 GROUP BY at_least"),
        note="An ON clause is any condition, and with >= one customer"
             " row matches EVERY level it reaches -- which is what 'at"
             " least' means, and what a join on equality could never"
             " do. A CASE, the trap, puts each customer in a single"
             " band, the highest one, so its counts are 'between this"
             " level and the next': 70 at level 10 where 613 customers"
             " have sent ten or more. The counts can only fall as the"
             " level rises; that is a quick check on any such table.",
        claims=[("six levels, 613 customers at ten or more",
                 lambda rows, c: len(rows) == 6 and (10, 613) in rows),
                ("25 customers at a hundred or more, and the counts never rise",
                 lambda rows, c: (100, 25) in rows and [r[1] for r in sorted(rows)] == sorted((r[1] for r in rows), reverse=True))],
    ),
    # ======================================================== 4 Changing rows
    dict(
        id=10, ledger="Q1336", concept="LOOKUP", tier="4 - Changing rows",
        kind="script",
        title="Two new starters at Hillcrest",
        prompt=(
            "Two couriers start at the Hillcrest depot on 2026-07-01:"
            " Ada Whitlock on a bike and Tom Reyes in a van. Add them"
            " in ONE INSERT with two rows. The depot is known by its"
            " name, so its id is looked up, not typed: a subquery in"
            " brackets can stand wherever a value can.\n\n"
            "Checked: name, depot name, vehicle, hiring and leaving"
            " dates of every courier hired from July 2026 on"
        ),
        solution=("INSERT INTO couriers (name, depot_id, vehicle, hired_on) VALUES\n"
                  "  ('Ada Whitlock', (SELECT depot_id FROM depots WHERE name = 'Hillcrest'), 'bike', '2026-07-01'),\n"
                  "  ('Tom Reyes',    (SELECT depot_id FROM depots WHERE name = 'Hillcrest'), 'van',  '2026-07-01');"),
        trap_sql=("INSERT INTO couriers (name, depot_id, vehicle, hired_on)\n"
                  "SELECT 'Ada Whitlock', depot_id, 'bike', '2026-07-01' FROM depots\n"
                  "UNION ALL\n"
                  "SELECT 'Tom Reyes', depot_id, 'van', '2026-07-01' FROM depots;"),
        probe_sql=("SELECT c.name, d.name, c.vehicle, c.hired_on, c.left_on FROM couriers c"
                   " JOIN depots d ON d.depot_id = c.depot_id WHERE c.hired_on >= '2026-07-01'"),
        note="VALUES takes several rows separated by commas, and any"
             " value in a row can be a scalar subquery -- one that"
             " returns one column of one row -- in its own brackets."
             " Looking the id up by name keeps the statement true if"
             " the ids are ever different, on a test copy for example."
             " The trap reads depots with no WHERE and hires the pair"
             " at all ten depots. If the name matched nothing the"
             " subquery would give NULL, and the NOT NULL on depot_id"
             " would refuse the row: a loud failure, the good kind.",
        claims=[("two new couriers, both at Hillcrest, neither with a leaving date",
                 lambda rows, c: sorted(rows) == [("Ada Whitlock", "Hillcrest", "bike", "2026-07-01", None),
                                                  ("Tom Reyes", "Hillcrest", "van", "2026-07-01", None)])],
    ),
    dict(
        id=11, ledger="Q1337", concept="SETSUB", tier="4 - Changing rows",
        kind="script",
        title="Bays to match the people",
        prompt=(
            "The bays are re-planned: every depot still open is to have"
            " FOUR bays for each courier currently working there, no"
            " more and no fewer. The closed depot keeps what it has."
            " One UPDATE; the SET holds a subquery that counts the"
            " couriers of the depot being updated.\n\n"
            "Checked: every depot's name and bays"
        ),
        solution=("UPDATE depots\n"
                  "SET bays = 4 * (SELECT COUNT(*) FROM couriers c\n"
                  "                WHERE c.depot_id = depots.depot_id AND c.left_on IS NULL)\n"
                  "WHERE closed_on IS NULL;"),
        trap_sql=("UPDATE depots\n"
                  "SET bays = 4 * (SELECT COUNT(*) FROM couriers c WHERE c.left_on IS NULL)\n"
                  "WHERE closed_on IS NULL;"),
        probe_sql="SELECT name, bays FROM depots",
        note="A subquery in SET runs once for each row being updated,"
             " and it is correlated when it mentions that row:"
             " depots.depot_id inside the subquery is the depot"
             " currently being changed. Leave that condition out, the"
             " trap, and the subquery is the same number for every"
             " row -- all 45 current couriers -- and every open depot"
             " gets 180 bays. The table being updated cannot be given"
             " an alias in SQLite's UPDATE, so its own name is used to"
             " point at it.",
        claims=[("Central Hub down to eight bays, Moorside and Millbank on 24",
                 lambda rows, c: ("Central Hub", 8) in rows and ("Moorside", 24) in rows and ("Millbank", 24) in rows),
                ("Old Foundry, closed, still has twelve",
                 lambda rows, c: ("Old Foundry", 12) in rows and len(rows) == 10)],
    ),
    dict(
        id=12, ledger="Q1338", concept="NEITHER", tier="4 - Changing rows",
        kind="script",
        title="Old trails, thinned to their two ends",
        prompt=(
            "Trails of old parcels are thinned to save space. For every"
            " parcel DELIVERED before 2025-04-01, delete the scans that"
            " are neither its 'collected' scan nor its 'delivered'"
            " scan. Every other parcel keeps its whole trail. Take care"
            " how 'neither ... nor' is written: NOT IN says it"
            " safely.\n\n"
            "Checked: scans left, for each status"
        ),
        solution=("DELETE FROM scans\n"
                  "WHERE status NOT IN ('collected', 'delivered')\n"
                  "  AND parcel_id IN (SELECT parcel_id FROM parcels WHERE delivered_at < '2025-04-01');"),
        trap_sql=("DELETE FROM scans\n"
                  "WHERE (status <> 'collected' OR status <> 'delivered')\n"
                  "  AND parcel_id IN (SELECT parcel_id FROM parcels WHERE delivered_at < '2025-04-01');"),
        probe_sql="SELECT status, COUNT(*) FROM scans GROUP BY status",
        note="'Neither A nor B' is NOT A AND NOT B, which is what NOT"
             " IN (A, B) means. Written with OR, the trap, it is true"
             " of every row there is: a 'collected' scan is not"
             " 'delivered', so it passes, and the trails lose their"
             " ends as well, 14,417 scans gone instead of 8,251. In a"
             " SELECT that mistake shows; in a DELETE it does not, so"
             " run the WHERE as a SELECT COUNT(*) first. The 3,083"
             " parcels keep exactly two scans each.",
        claims=[("8,251 scans deleted: every 'collected' and 'delivered' still there",
                 lambda rows, c: ("collected", 24000) in rows and ("delivered", 23729) in rows
                 and sum(r[1] for r in rows) == 112378 - 8251)],
    ),
    # =========================================================== 5 Procedures
    dict(
        id=13, ledger="Q1339", concept="REBUILD", tier="5 - Procedures",
        kind="script",
        title="A new rule for a table that already exists",
        prompt=(
            "New rule: an invoice cannot be paid before it was issued."
            " SQLite's ALTER TABLE cannot add a CHECK to an existing"
            " table, so the table is rebuilt, in one transaction, by"
            " the standard procedure: create invoices_new with"
            " everything invoices has PLUS the new CHECK; copy every"
            " row across; drop invoices; rename invoices_new to"
            " invoices. The present definition is in schema.sql -- start"
            " from it, so that no existing rule is lost. The question"
            " then tries three inserts: one paid before it was issued,"
            " one that is fine, and one repeating a customer and period"
            " already there.\n\n"
            "Checked: invoices in the table, how many are for 2026-06,"
            " and the cents added up"
        ),
        solution=("BEGIN;\n"
                  "CREATE TABLE invoices_new (\n"
                  "  invoice_id   INTEGER PRIMARY KEY,\n"
                  "  customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),\n"
                  "  period       TEXT    NOT NULL,\n"
                  "  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),\n"
                  "  issued_on    TEXT    NOT NULL,\n"
                  "  paid_on      TEXT,\n"
                  "  method       TEXT    CHECK (method IN ('card', 'transfer')),\n"
                  "  UNIQUE (customer_id, period),\n"
                  "  CHECK ((paid_on IS NULL) = (method IS NULL)),\n"
                  "  CHECK (paid_on >= issued_on)\n"
                  ");\n"
                  "INSERT INTO invoices_new SELECT * FROM invoices;\n"
                  "DROP TABLE invoices;\n"
                  "ALTER TABLE invoices_new RENAME TO invoices;\n"
                  "CREATE INDEX idx_invoices_customer ON invoices(customer_id);\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "CREATE TABLE invoices_new (\n"
                  "  invoice_id   INTEGER PRIMARY KEY,\n"
                  "  customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),\n"
                  "  period       TEXT    NOT NULL,\n"
                  "  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),\n"
                  "  issued_on    TEXT    NOT NULL,\n"
                  "  paid_on      TEXT,\n"
                  "  method       TEXT    CHECK (method IN ('card', 'transfer')),\n"
                  "  CHECK ((paid_on IS NULL) = (method IS NULL)),\n"
                  "  CHECK (paid_on >= issued_on)\n"
                  ");\n"
                  "INSERT INTO invoices_new SELECT * FROM invoices;\n"
                  "DROP TABLE invoices;\n"
                  "ALTER TABLE invoices_new RENAME TO invoices;\n"
                  "COMMIT;"),
        driver_sql=("INSERT INTO invoices (customer_id, period, amount_cents, issued_on, paid_on, method)"
                    " VALUES (8, '2026-06', 1500, '2026-07-01', '2026-06-28', 'card');\n"
                    "INSERT INTO invoices (customer_id, period, amount_cents, issued_on, paid_on, method)"
                    " VALUES (12, '2026-06', 2400, '2026-07-01', '2026-07-03', 'transfer');\n"
                    "INSERT INTO invoices (customer_id, period, amount_cents, issued_on, paid_on, method)"
                    " VALUES (4, '2026-05', 100, '2026-06-01', NULL, NULL);"),
        probe_sql="SELECT COUNT(*), SUM(period = '2026-06'), SUM(amount_cents) FROM invoices",
        note="Create, copy, drop, rename is how SQLite changes anything"
             " ALTER TABLE cannot, and the transaction means nobody"
             " ever sees the moment with no invoices table. The risk"
             " is in the retyping: the trap adds the new CHECK and"
             " drops the UNIQUE (customer_id, period) on the way, and"
             " the third insert bills customer 4 twice for May. An"
             " unpaid invoice passes the new CHECK without an IS NULL"
             " test, because a CHECK only fails when its condition is"
             " false, and NULL >= anything is not false. Indexes go"
             " with the old table and have to be created again.",
        claims=[("one of the three inserts got in: 2,299 invoices, one for June",
                 lambda rows, c: rows == [(2299, 1, 7462080 + 2400)])],
    ),
    dict(
        id=14, ledger="Q1340", concept="LASTID", tier="5 - Procedures",
        kind="script",
        title="Riverside opens, with staff and customers",
        prompt=(
            "A new depot, Riverside, opens in the east region on"
            " 2026-07-01 with 12 bays. In ONE transaction: add the"
            " depot; move the lorry drivers of Docklands (depot 5) to"
            " it; move to it every Docklands customer whose"
            " postcode_area begins LE. The new depot's id is whatever"
            " the table gives it -- do not assume a number:"
            " last_insert_rowid() reports the id of the row an INSERT"
            " has just made. The question then issues a ROLLBACK:"
            " committed work survives it.\n\n"
            "Checked: for Docklands and Riverside: region, bays,"
            " couriers listed, customers listed"
        ),
        solution=("BEGIN;\n"
                  "INSERT INTO depots (name, region, bays, opened_on) VALUES ('Riverside', 'east', 12, '2026-07-01');\n"
                  "UPDATE couriers SET depot_id = last_insert_rowid() WHERE depot_id = 5 AND vehicle = 'lorry';\n"
                  "UPDATE customers SET depot_id = last_insert_rowid() WHERE depot_id = 5 AND postcode_area LIKE 'LE%';\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "INSERT INTO depots (name, region, bays, opened_on) VALUES ('Riverside', 'east', 12, '2026-07-01');\n"
                  "UPDATE couriers SET depot_id = last_insert_rowid() WHERE depot_id = 5 AND vehicle = 'lorry';\n"
                  "UPDATE customers SET depot_id = last_insert_rowid() WHERE postcode_area LIKE 'LE%';\n"
                  "COMMIT;"),
        driver_sql="ROLLBACK;",
        probe_sql=("SELECT d.name, d.region, d.bays,"
                   " (SELECT COUNT(*) FROM couriers c WHERE c.depot_id = d.depot_id),"
                   " (SELECT COUNT(*) FROM customers c WHERE c.depot_id = d.depot_id)"
                   " FROM depots d WHERE d.name IN ('Docklands', 'Riverside')"),
        note="last_insert_rowid() is the key the most recent INSERT on"
             " this connection produced, and it is the link between"
             " the steps of a procedure that creates a parent and then"
             " points children at it. Only an INSERT changes it, so"
             " both UPDATEs can use it. The steps have to come in this"
             " order: until the depot exists the foreign key will not"
             " accept its id. The trap drops 'depot_id = 5' from the"
             " last step and moves every LE customer in the company,"
             " 126 of them, to a depot with two lorries.",
        claims=[("Riverside: east, 12 bays, two couriers, sixteen customers",
                 lambda rows, c: ("Riverside", "east", 12, 2, 16) in rows),
                ("Docklands keeps three couriers and 53 customers",
                 lambda rows, c: ("Docklands", "east", 30, 3, 53) in rows)],
    ),
    dict(
        id=15, ledger="Q1341", concept="CASCADE", tier="5 - Procedures",
        kind="script",
        title="A parcel that takes its trail with it",
        prompt=(
            "Deleting a parcel is refused while it has scans: the"
            " foreign key protects the trail. Store the procedure that"
            " makes it possible. Create a table removed with parcel_id"
            " as its primary key and a required whole number"
            " scans_removed, and a BEFORE DELETE trigger on parcels"
            " whose body does two things for the parcel about to go:"
            " records in removed how many scans it has, and deletes"
            " those scans. The question then deletes parcels 40 and"
            " 122.\n\n"
            "Checked: each row of removed, with the parcels and scans"
            " left in the database"
        ),
        solution=("CREATE TABLE removed (\n"
                  "  parcel_id     INTEGER PRIMARY KEY,\n"
                  "  scans_removed INTEGER NOT NULL\n"
                  ");\n"
                  "CREATE TRIGGER clear_trail BEFORE DELETE ON parcels\n"
                  "BEGIN\n"
                  "  INSERT INTO removed (parcel_id, scans_removed)\n"
                  "  SELECT OLD.parcel_id, COUNT(*) FROM scans WHERE parcel_id = OLD.parcel_id;\n"
                  "  DELETE FROM scans WHERE parcel_id = OLD.parcel_id;\n"
                  "END;"),
        trap_sql=("CREATE TABLE removed (\n"
                  "  parcel_id     INTEGER PRIMARY KEY,\n"
                  "  scans_removed INTEGER NOT NULL\n"
                  ");\n"
                  "CREATE TRIGGER clear_trail BEFORE DELETE ON parcels\n"
                  "BEGIN\n"
                  "  DELETE FROM scans WHERE parcel_id = OLD.parcel_id;\n"
                  "  INSERT INTO removed (parcel_id, scans_removed)\n"
                  "  SELECT OLD.parcel_id, COUNT(*) FROM scans WHERE parcel_id = OLD.parcel_id;\n"
                  "END;"),
        driver_sql="DELETE FROM parcels WHERE parcel_id IN (40, 122);",
        probe_sql=("SELECT r.parcel_id, r.scans_removed, (SELECT COUNT(*) FROM parcels),"
                   " (SELECT COUNT(*) FROM scans) FROM removed r"),
        note="A trigger body is a small procedure: its statements run"
             " in the order written, once for each row the DELETE"
             " removes, with OLD holding that row. Count first, then"
             " delete -- the trap has them the other way round and"
             " carefully records that each parcel had 0 scans. With"
             " the scans gone the foreign key has nothing to object"
             " to, and the DELETE that fired the trigger goes ahead."
             " This is ON DELETE CASCADE written by hand, which is how"
             " you get it on a table whose foreign key was declared"
             " without one.",
        claims=[("parcel 40 had five scans and 122 three; eight scans gone with them",
                 lambda rows, c: sorted(rows) == [(40, 5, 23998, 112370), (122, 3, 23998, 112370)])],
    ),
]

BY_ID = {ex["id"]: ex for ex in EXERCISES}
TIERS = list(dict.fromkeys(ex["tier"] for ex in EXERCISES))

def query_plan(conn, sql):
    """The rows of EXPLAIN QUERY PLAN, joined into one searchable string.

    SQLite's plan output is a small tree; the `detail` column carries the text
    everyone actually reads -- "SCAN enrolments", "SEARCH ... USING INDEX ...",
    "USE TEMP B-TREE FOR ORDER BY". Joining them gives one string that a
    question can make assertions about.
    """
    return " | ".join(
        r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall())


def plan_ok(exercise, plan):
    """(passed, message) for an exercise's plan assertions.

    Efficiency questions cannot be graded on their result, because the slow
    way and the fast way return exactly the same rows -- that is what makes
    them worth asking. So they carry `plan_requires` and/or `plan_forbids`,
    checked against EXPLAIN QUERY PLAN, and a right answer has to be BOTH
    correct and taken by the intended route.

    Matching is case-insensitive substring, which is coarse on purpose: it
    should accept any query that reaches the plan the question is about, not
    just the reference wording.
    """
    up = plan.upper()
    for needle in exercise.get("plan_requires", ()):
        if needle.upper() not in up:
            return False, (f"Right rows, but the query plan does not contain"
                           f" {needle!r}.\n  Plan: {plan}")
    for needle in exercise.get("plan_forbids", ()):
        if needle.upper() in up:
            return False, (f"Right rows, but the query plan contains"
                           f" {needle!r}, which this question asks you to"
                           f" avoid.\n  Plan: {plan}")
    return True, ""


def is_script(exercise):
    """True for a writable question: graded on the database AFTER the script.

    A query question is graded on what its SELECT returns. A script question
    runs the editor's contents -- any number of statements, DML or DDL -- in
    a throwaway copy of the database, then runs the question's `probe_sql`
    against the result and grades THAT. So the answer is a state, not a
    result set, and the reference solution is whatever script produces the
    same state.
    """
    return exercise.get("kind") == "script"


def script_result(exercise, script, db_path=None):
    """(rows, error, info) from running `script` and then the probe.

    The pipeline every grader path shares, so the GUI and check_questions.py
    cannot drift:

      1. a fresh sandbox copy of the database
      2. the script, statement by statement, time-limited
      3. `driver_sql`, if the question has one: statements the question itself
         runs afterwards to EXERCISE what the script built -- an INSERT that
         should fire a trigger, or one that a CHECK or trigger should reject.
         Each runs separately and a rejection is recorded, not fatal, because
         "this row must be refused" is a legitimate thing to test.
      4. `probe_sql`, whose rows are the answer

    info carries statement/change counts and any driver rejections, for the
    status bar. error is a string if the script itself failed.
    """
    import db
    conn = db.sandbox(db_path)
    info = {"statements": 0, "changes": 0, "rejected": []}
    try:
        try:
            n, changed, _, _ = db.run_script(conn, script)
            info["statements"], info["changes"] = n, changed
        except (db.QueryTimeout, db.TooManyRows) as exc:
            return None, str(exc), info
        except sqlite3.Error as exc:
            return None, f"SQL error: {exc}", info
        for stmt in db.split_statements(exercise.get("driver_sql", "")):
            try:
                with db.time_limit(conn):
                    conn.execute(stmt)
            except sqlite3.Error as exc:
                info["rejected"].append((stmt, str(exc)))
        try:
            with db.time_limit(conn):
                cur = conn.execute(exercise["probe_sql"])
                info["headers"] = [d[0] for d in cur.description]
                rows = db.fetch_capped(cur)
        except (db.QueryTimeout, db.TooManyRows, sqlite3.Error) as exc:
            return None, f"probe failed: {exc}", info
        return [tuple(r) for r in rows], None, info
    finally:
        conn.close()


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


CELL_CHARS = 70          # per value in a sample row
SAMPLE_CHARS = 300       # per sample row, after the per-value trim


def brief(row):
    """One sample row, short enough to sit in a one-line status bar.

    A wrong GROUP_CONCAT can hold every value in the table -- 300,000
    characters in a single cell -- so the feedback has to be trimmed at the
    point it is built, not left to whatever displays it.
    """
    parts = []
    for v in row:
        s = repr(v)
        if len(s) > CELL_CHARS:
            s = s[:CELL_CHARS - 4] + "..." + s[-1]
        parts.append(s)
    out = "(" + ", ".join(parts) + ")"
    if len(out) > SAMPLE_CHARS:
        out = out[:SAMPLE_CHARS - 3] + "..."
    return out


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
        detail += f"\n  Expected but missing:  {brief(missing[0])}"
    if unexpected:
        detail += f"\n  Returned but wrong:    {brief(unexpected[0])}"
    return False, (f"Right row count ({len(got)}), but the values differ "
                   f"in {len(missing)} row(s).{detail}")
