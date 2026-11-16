"""Practice exercises: fifteen questions on the parcel-courier schema.

The sixth set on the courier scheme (SEED 1241), and the first with SIX
writable questions instead of three: nine that read, six that change the
data, the last three of them procedures. The tiers are named by task, the
tools are ones the first five courier sets left out, and the prompts name
the tool but do not write the statement. Text and patterns -- names that
END in a word by LIKE, a surname cut out by INSTR and SUBSTR, a postcode's
letters by RTRIM with a character list. Windows and shares -- days after a
depot's first hire by FIRST_VALUE, each region's share of all postage by a
window over the grouped rows, the top sender at each depot WITH ties by
RANK. Rows as values -- a price list written inline with VALUES, a route
matched as a row value, depots touched at either end by UNION.

Changing rows, three single statements:

  * an UPDATE that sets two columns at once, for rows named by a subquery
  * an INSERT OR IGNORE that leaves existing rows alone
  * a DELETE that keeps one row per group

Procedures, three scripts of several steps. SQLite has no CREATE
PROCEDURE; what it has is a transaction, whose steps stand or fall
together, and a trigger body, which is stored and runs when called:

  * three UPDATEs that close a depot, in one transaction
  * archive, then delete children, then delete parents, in that order
  * an INSTEAD OF trigger on a view: a procedure you call with INSERT

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
    # ==================================================== 1 Text and patterns
    dict(
        id=1, ledger="Q1297", concept="LIKE", tier="1 - Text and patterns",
        title="Businesses whose name ends in Supplies",
        prompt=(
            "Some businesses trade in 'Garden Supplies' and are called"
            " '... Garden Supplies Ltd'; others are simply '..."
            " Supplies'. For each depot, by name: how many of its"
            " customers have a name that ENDS with the word Supplies."
            " LIKE, with a wildcard on one side only.\n\n"
            "Return: depot, customers"
        ),
        solution=("SELECT d.name, COUNT(*) FROM customers c JOIN depots d ON d.depot_id = c.depot_id"
                  " WHERE c.name LIKE '%Supplies' GROUP BY d.name"),
        trap_sql=("SELECT d.name, COUNT(*) FROM customers c JOIN depots d ON d.depot_id = c.depot_id"
                  " WHERE c.name LIKE '%Supplies%' GROUP BY d.name"),
        note="In a LIKE pattern % stands for any run of characters,"
             " including none. '%Supplies' must finish with the word;"
             " '%Supplies%', the trap, only has to contain it, and"
             " counts 23 more, the businesses like 'Garden Supplies"
             " Ltd' where the word sits in the middle. 'Supplies%' would be 'starts with'. LIKE"
             " ignores case for ASCII letters, so '%supplies' finds the"
             " same 41.",
        claims=[("ten depots, 41 customers in all",
                 lambda rows, c: len(rows) == 10 and sum(r[1] for r in rows) == 41),
                ("Westway has the most, eight",
                 lambda rows, c: max(rows, key=lambda r: r[1]) == ("Westway", 8))],
    ),
    dict(
        id=2, ledger="Q1298", concept="INSTR", tier="1 - Text and patterns",
        title="The surnames with the most customers",
        prompt=(
            "A personal customer's name is a first name, one space, and"
            " a surname. For each surname: how many personal customers"
            " carry it. Keep the surnames with 20 customers or more."
            " INSTR to find the space, SUBSTR to cut.\n\n"
            "Return: surname, customers"
        ),
        solution=("SELECT SUBSTR(name, INSTR(name, ' ') + 1) AS surname, COUNT(*) FROM customers"
                  " WHERE kind = 'personal' GROUP BY surname HAVING COUNT(*) >= 20"),
        trap_sql=("SELECT SUBSTR(name, INSTR(name, ' ')) AS surname, COUNT(*) FROM customers"
                  " WHERE kind = 'personal' GROUP BY surname HAVING COUNT(*) >= 20"),
        note="INSTR(name, ' ') is the position of the first space,"
             " counting from 1, and SUBSTR with two arguments runs from"
             " a position to the end. The + 1 steps over the space"
             " itself: without it, the trap, every surname comes back"
             " with a space in front -- ' Sowerby' -- which looks right"
             " on screen and is a different string. The businesses are"
             " filtered out because their first word is the family"
             " name, not their last.",
        claims=[("eleven surnames, Sowerby on 27",
                 lambda rows, c: len(rows) == 11 and ("Sowerby", 27) in rows)],
    ),
    dict(
        id=3, ledger="Q1299", concept="RTRIM", tier="1 - Text and patterns",
        title="Customers by postcode town",
        prompt=(
            "A postcode_area is one or two letters and then digits: NG5,"
            " DE22, S1. The letters alone name the town. For each town:"
            " how many customers, and how many of them are businesses."
            " Customers with no postcode_area are a group of their own."
            " RTRIM takes a second argument.\n\n"
            "Return: town, customers, businesses"
        ),
        solution=("SELECT RTRIM(postcode_area, '0123456789') AS town, COUNT(*), SUM(kind = 'business')"
                  " FROM customers GROUP BY town"),
        trap_sql=("SELECT SUBSTR(postcode_area, 1, 2) AS town, COUNT(*), SUM(kind = 'business')"
                  " FROM customers GROUP BY town"),
        note="RTRIM(text, characters) strips from the right-hand end"
             " every character that appears in the second argument, in"
             " any order, and stops at the first one that does not: the"
             " digits go and the letters stay, however many of each."
             " Taking the first two characters, the trap, is right for"
             " NG and DE and wrong for Sheffield, which splits into S1"
             " and S8. RTRIM of NULL is NULL, and GROUP BY gives the 73"
             " NULLs one row.",
        claims=[("five rows, NG with 296 customers and 102 businesses",
                 lambda rows, c: len(rows) == 5 and ("NG", 296, 102) in rows),
                ("73 customers have no area",
                 lambda rows, c: (None, 73, 31) in rows)],
    ),
    # ================================================== 2 Windows and shares
    dict(
        id=4, ledger="Q1300", concept="FIRSTV", tier="2 - Windows and shares",
        title="How long after the depot's first hire",
        prompt=(
            "For every courier: how many days after their depot's FIRST"
            " hire they were taken on, as a whole number -- 0 for the"
            " first hire itself. Couriers who have left count like"
            " anyone else. FIRST_VALUE over a window per depot, and"
            " julianday for the gap.\n\n"
            "Return: courier, depot, days_after_first"
        ),
        solution=("SELECT c.name, d.name, CAST(julianday(c.hired_on) - julianday(FIRST_VALUE(c.hired_on)"
                  " OVER (PARTITION BY c.depot_id ORDER BY c.hired_on)) AS INTEGER)"
                  " FROM couriers c JOIN depots d ON d.depot_id = c.depot_id"),
        trap_sql=("SELECT c.name, d.name, CAST(julianday(c.hired_on) - julianday(FIRST_VALUE(c.hired_on)"
                  " OVER (ORDER BY c.hired_on)) AS INTEGER)"
                  " FROM couriers c JOIN depots d ON d.depot_id = c.depot_id"),
        note="FIRST_VALUE(x) OVER (PARTITION BY ... ORDER BY ...) puts"
             " the first row's x beside every row of its partition, so"
             " each courier is compared with their own depot's earliest"
             " hire without a join or a subquery. Leave out PARTITION"
             " BY, the trap, and everyone is measured from the company's"
             " first hire in April 2018: one zero instead of ten."
             " MIN(hired_on) OVER (PARTITION BY depot_id) gives the same"
             " answer here; FIRST_VALUE is the one that can also fetch"
             " a different column of that first row.",
        claims=[("sixty couriers, ten of them a depot's first",
                 lambda rows, c: len(rows) == 60 and sum(r[2] == 0 for r in rows) == 10),
                ("the longest wait was 2,761 days, at Docklands",
                 lambda rows, c: max(rows, key=lambda r: r[2]) == ("Aisha Chowdhury", "Docklands", 2761))],
    ),
    dict(
        id=5, ledger="Q1301", concept="SHARE", tier="2 - Windows and shares",
        title="Each region's share of the postage",
        prompt=(
            "For each region -- the region of the depot where a parcel"
            " was collected: its parcels, and its share of ALL postage"
            " as a percentage to one decimal place. The grand total can"
            " sit beside the grouped rows: a window function over the"
            " whole result, its OVER left empty.\n\n"
            "Return: region, parcels, pct_of_postage"
        ),
        solution=("SELECT d.region, COUNT(*), ROUND(100.0 * SUM(p.postage_cents) / SUM(SUM(p.postage_cents)) OVER (), 1)"
                  " FROM parcels p JOIN depots d ON d.depot_id = p.origin_depot_id GROUP BY d.region"),
        trap_sql=("SELECT d.region, COUNT(*), 100 * SUM(p.postage_cents) / SUM(SUM(p.postage_cents)) OVER ()"
                  " FROM parcels p JOIN depots d ON d.depot_id = p.origin_depot_id GROUP BY d.region"),
        note="Window functions run after GROUP BY, so SUM(SUM(x)) OVER"
             " () reads: the inner SUM is each group's total, the outer"
             " one adds those totals across every row of the result. An"
             " empty OVER () is one partition holding everything. The"
             " trap divides integer by integer, which SQLite truncates:"
             " 20, 17, 16, 26, 19, adding up to 98. The 100.0 makes it"
             " real division. A scalar subquery for the total does the"
             " same job with a second pass over parcels.",
        claims=[("five regions, the south with 26.6 per cent",
                 lambda rows, c: len(rows) == 5 and ("south", 6386, 26.6) in rows),
                ("the shares add up to 100",
                 lambda rows, c: abs(sum(r[2] for r in rows) - 100) < 0.11)],
    ),
    dict(
        id=6, ledger="Q1302", concept="RANK", tier="2 - Windows and shares",
        title="June's biggest sender at each depot, ties included",
        prompt=(
            "For each depot: the customer who sent the most parcels"
            " collected in June 2026, the depot being the customer's"
            " HOME depot. Where two customers tie for first, list both."
            " RANK, partitioned, in a subquery so its result can be"
            " filtered.\n\n"
            "Return: depot, customer, parcels"
        ),
        solution=("SELECT depot, customer, n FROM (SELECT d.name AS depot, c.name AS customer, COUNT(*) AS n,"
                  " RANK() OVER (PARTITION BY c.depot_id ORDER BY COUNT(*) DESC) AS r"
                  " FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " JOIN depots d ON d.depot_id = c.depot_id"
                  " WHERE p.collected_at >= '2026-06-01' AND p.collected_at < '2026-07-01'"
                  " GROUP BY c.customer_id) WHERE r = 1"),
        trap_sql=("SELECT depot, customer, n FROM (SELECT d.name AS depot, c.name AS customer, COUNT(*) AS n,"
                  " ROW_NUMBER() OVER (PARTITION BY c.depot_id ORDER BY COUNT(*) DESC) AS r"
                  " FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " JOIN depots d ON d.depot_id = c.depot_id"
                  " WHERE p.collected_at >= '2026-06-01' AND p.collected_at < '2026-07-01'"
                  " GROUP BY c.customer_id) WHERE r = 1"),
        note="RANK gives equal values the same rank, so every customer"
             " tied for the top is rank 1 and r = 1 returns them all:"
             " thirteen rows for ten depots. ROW_NUMBER, the trap, must"
             " number them 1 and 2 and picks between equals arbitrarily"
             " -- exactly one row a depot, and which customer it drops"
             " is not defined. A window function cannot be used in"
             " WHERE, which is why the ranking sits in a subquery.",
        claims=[("thirteen rows: three depots have a tie",
                 lambda rows, c: len(rows) == 13 and len({r[0] for r in rows}) == 10),
                ("Northgate's two leaders sent 17 each",
                 lambda rows, c: sorted(r[2] for r in rows if r[0] == "Northgate") == [17, 17])],
    ),
    # ======================================================= 3 Rows as values
    dict(
        id=7, ledger="Q1303", concept="VALUES", tier="3 - Rows as values",
        title="How much of the postage is the weight surcharge",
        prompt=(
            "Postage is a base price for the service plus a surcharge"
            " for weight. The base prices are in no table: economy 350,"
            " standard 500, express 900 cents. For each service: its"
            " parcels, and the surcharge collected in total -- postage"
            " above the base. Write the price list as an inline table"
            " with VALUES, named in a CTE, and join to it.\n\n"
            "Return: service, parcels, surcharge_cents"
        ),
        solution=("WITH rates(service, base) AS (VALUES ('economy', 350), ('standard', 500), ('express', 900))"
                  " SELECT p.service, COUNT(*), SUM(p.postage_cents - r.base)"
                  " FROM parcels p JOIN rates r ON r.service = p.service GROUP BY p.service"),
        trap_sql=("SELECT service, COUNT(*), SUM(postage_cents - CASE service WHEN 'express' THEN 900 ELSE 350 END)"
                  " FROM parcels GROUP BY service"),
        note="VALUES (..), (..) is a table written on the spot, and a"
             " CTE with a column list -- rates(service, base) -- gives"
             " it names to join on. A lookup table keeps data out of"
             " the logic: a fourth service is one more row, not one"
             " more WHEN. The trap's CASE forgets standard and lets it"
             " fall to the ELSE, overstating that surcharge by 150"
             " cents a parcel; an inner join to the list would have"
             " dropped an unknown service where the CASE mis-prices it.",
        claims=[("three services, economy's surcharge 1,970,760 cents",
                 lambda rows, c: len(rows) == 3 and ("economy", 12005, 1970760) in rows),
                ("standard's is 1,809,360",
                 lambda rows, c: ("standard", 7259, 1809360) in rows)],
    ),
    dict(
        id=8, ledger="Q1304", concept="ROWVAL", tier="3 - Rows as values",
        title="Every parcel on parcel 1's route",
        prompt=(
            "Parcel 1 went from one depot to another. For each service:"
            " how many parcels have made exactly that journey -- the"
            " same origin AND the same destination, parcel 1 included."
            " Compare the two columns as ONE row value with a subquery"
            " that returns two columns.\n\n"
            "Return: service, parcels"
        ),
        solution=("SELECT service, COUNT(*) FROM parcels WHERE (origin_depot_id, dest_depot_id) ="
                  " (SELECT origin_depot_id, dest_depot_id FROM parcels WHERE parcel_id = 1) GROUP BY service"),
        trap_sql=("SELECT service, COUNT(*) FROM parcels WHERE origin_depot_id ="
                  " (SELECT origin_depot_id FROM parcels WHERE parcel_id = 1) GROUP BY service"),
        note="(a, b) = (SELECT x, y ...) compares a pair with a pair:"
             " true only when both parts match. It reads parcel 1 once"
             " and cannot mix up which column goes with which, where"
             " two separate scalar subqueries read it twice. The trap"
             " matches the origin alone and counts everything Docklands"
             " ever collected, 2,261 parcels instead of the 115 that"
             " went on to Old Foundry. Row values also work with IN,"
             " against a subquery returning many pairs.",
        claims=[("three services, 115 parcels on the route",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 115),
                ("66 of them economy",
                 lambda rows, c: ("economy", 66) in rows)],
    ),
    dict(
        id=9, ledger="Q1305", concept="UNION", tier="3 - Rows as values",
        title="How many depots a customer's post has touched",
        prompt=(
            "A parcel touches two depots, where it was collected and"
            " where it was delivered to. For each customer, count the"
            " DIFFERENT depots their parcels have touched at either end;"
            " then say how many customers there are for each count."
            " Walk-ins are left out. Two lists of (customer, depot)"
            " stacked by the set operator that drops duplicates.\n\n"
            "Return: depots_touched, customers"
        ),
        solution=("SELECT n, COUNT(*) FROM (SELECT customer_id, COUNT(*) AS n FROM"
                  " (SELECT customer_id, origin_depot_id FROM parcels WHERE customer_id IS NOT NULL"
                  " UNION SELECT customer_id, dest_depot_id FROM parcels WHERE customer_id IS NOT NULL)"
                  " GROUP BY customer_id) GROUP BY n"),
        trap_sql=("SELECT n, COUNT(*) FROM (SELECT customer_id, COUNT(*) AS n FROM"
                  " (SELECT customer_id, origin_depot_id FROM parcels WHERE customer_id IS NOT NULL"
                  " UNION ALL SELECT customer_id, dest_depot_id FROM parcels WHERE customer_id IS NOT NULL)"
                  " GROUP BY customer_id) GROUP BY n"),
        note="UNION stacks two results and removes duplicate rows, so a"
             " (customer, depot) pair appears once whether the depot"
             " was an origin, a destination, or both, a hundred times"
             " over. Counting the rows per customer is then counting"
             " distinct depots. UNION ALL, the trap, keeps every row:"
             " its count is twice the customer's parcels. The columns"
             " take their names from the first SELECT, which is why"
             " dest_depot_id can sit under origin_depot_id.",
        claims=[("seven different counts, from four depots to all ten",
                 lambda rows, c: len(rows) == 7 and min(rows)[0] == 4 and max(rows)[0] == 10),
                ("85 customers have touched all ten, of 620 senders",
                 lambda rows, c: (10, 85) in rows and sum(r[1] for r in rows) == 620)],
    ),
    # ======================================================== 4 Changing rows
    dict(
        id=10, ledger="Q1306", concept="SETROW", tier="4 - Changing rows",
        kind="script",
        title="Old Foundry's debts, settled",
        prompt=(
            "The customers of the closed depot have settled up. Mark"
            " every UNPAID invoice of a customer whose home depot is Old"
            " Foundry as paid on 2026-07-01 by transfer. The table's"
            " CHECK refuses an invoice that has only one of paid_on and"
            " method, so both are set in ONE UPDATE; which customers is"
            " a subquery's business.\n\n"
            "Checked: invoices and cents for each method, the unpaid"
            " included"
        ),
        solution=("UPDATE invoices SET (paid_on, method) = ('2026-07-01', 'transfer')\n"
                  "WHERE paid_on IS NULL\n"
                  "  AND customer_id IN (SELECT c.customer_id FROM customers c\n"
                  "                      JOIN depots d ON d.depot_id = c.depot_id\n"
                  "                      WHERE d.name = 'Old Foundry');"),
        trap_sql="UPDATE invoices SET (paid_on, method) = ('2026-07-01', 'transfer') WHERE paid_on IS NULL;",
        probe_sql="SELECT method, COUNT(*), SUM(amount_cents) FROM invoices GROUP BY method",
        note="SET (a, b) = (x, y) assigns a row value: both columns"
             " change in the same statement, which the CHECK needs --"
             " it is tested once per row after the whole SET, so a"
             " paid_on with no method never exists. SET paid_on = ...,"
             " method = ... is the same thing spelled the long way; two"
             " separate UPDATEs are not, and the first is refused. The"
             " trap has no subquery and pays off every unpaid invoice"
             " in the company, 332 instead of 38.",
        claims=[("38 invoices settled: 294 still unpaid",
                 lambda rows, c: (None, 294, 930070) in rows),
                ("transfers up to 1,382",
                 lambda rows, c: ("transfer", 1382, 4355220) in rows)],
    ),
    dict(
        id=11, ledger="Q1307", concept="IGNORE", tier="4 - Changing rows",
        kind="script",
        title="A minimum charge for the quiet accounts",
        prompt=(
            "Every business customer whose home depot is Northgate"
            " (depot 3) must have an invoice for period 2026-05. Those"
            " without one get a minimum charge: 500 cents, issued"
            " 2026-06-01, not yet paid. Those who already have one keep"
            " it exactly as it is. One INSERT ... SELECT that offers a"
            " row for every such business and lets the table's UNIQUE"
            " (customer_id, period) turn away the ones already there:"
            " INSERT has a conflict clause for that.\n\n"
            "Checked: the invoices for 2026-05: how many, their cents"
            " added up, how many unpaid"
        ),
        solution=("INSERT OR IGNORE INTO invoices (customer_id, period, amount_cents, issued_on)\n"
                  "SELECT customer_id, '2026-05', 500, '2026-06-01'\n"
                  "FROM customers WHERE depot_id = 3 AND kind = 'business';"),
        trap_sql=("INSERT OR REPLACE INTO invoices (customer_id, period, amount_cents, issued_on)\n"
                  "SELECT customer_id, '2026-05', 500, '2026-06-01'\n"
                  "FROM customers WHERE depot_id = 3 AND kind = 'business';"),
        probe_sql="SELECT COUNT(*), SUM(amount_cents), SUM(paid_on IS NULL) FROM invoices WHERE period = '2026-05'",
        note="INSERT OR IGNORE skips any row that would break a UNIQUE"
             " or PRIMARY KEY constraint and carries on with the rest,"
             " so 27 rows are offered and the ten businesses with no"
             " May invoice are the ones that get in. OR REPLACE, the"
             " trap, resolves the same conflict the other way: it"
             " DELETES the existing invoice and inserts the new one, so"
             " seventeen real bills become 500 cents, unpaid. ON"
             " CONFLICT DO NOTHING is the same as OR IGNORE; a NOT"
             " EXISTS in the SELECT gets there without the constraint.",
        claims=[("ten invoices added: 167 for May, 86 unpaid",
                 lambda rows, c: rows == [(167, 493830, 86)])],
    ),
    dict(
        id=12, ledger="Q1308", concept="DEDUPE", tier="4 - Changing rows",
        kind="script",
        title="One failed attempt per parcel is enough",
        prompt=(
            "Some parcels have two 'failed' scans. For each parcel keep"
            " the failed scan with the lowest scan_id and delete its"
            " other failed scans. Scans of every other status stay. A"
            " DELETE whose WHERE holds a grouped subquery: the ids to"
            " keep.\n\n"
            "Checked: scans left, and how many of them are failures"
        ),
        solution=("DELETE FROM scans\n"
                  "WHERE status = 'failed'\n"
                  "  AND scan_id NOT IN (SELECT MIN(scan_id) FROM scans\n"
                  "                      WHERE status = 'failed' GROUP BY parcel_id);"),
        trap_sql=("DELETE FROM scans\n"
                  "WHERE status = 'failed'\n"
                  "  AND scan_id NOT IN (SELECT MIN(scan_id) FROM scans GROUP BY parcel_id);"),
        probe_sql="SELECT COUNT(*), SUM(status = 'failed') FROM scans",
        note="This is the standard way to remove duplicates: a subquery"
             " picks one survivor per group, MIN(id) GROUP BY the thing"
             " that should be unique, and the DELETE removes everything"
             " in scope that is not a survivor. The subquery must look"
             " at the same rows as the DELETE: the trap forgets its"
             " status filter, so each parcel's survivor is its very"
             " first scan, a 'collected' one, and all 3,417 failures"
             " go. Run the subquery's logic as a SELECT COUNT first;"
             " a DELETE has no preview.",
        claims=[("72 repeats deleted, 3,345 failures kept",
                 lambda rows, c: rows == [(112306, 3345)])],
    ),
    # =========================================================== 5 Procedures
    dict(
        id=13, ledger="Q1309", concept="TXN", tier="5 - Procedures",
        kind="script",
        title="Closing Southfield, all or nothing",
        prompt=(
            "SQLite has no stored procedures; the nearest thing is a"
            " script whose steps stand or fall together. Southfield"
            " (depot 7) closes on 2026-07-01. In ONE transaction:"
            " record the closing date on the depot; move its couriers"
            " who are still employed to Millbank (depot 8); move every"
            " customer whose home depot it is to Millbank. Couriers who"
            " have already left stay on Southfield's books. The"
            " question then issues a ROLLBACK: committed work survives"
            " it, work left in an open transaction does not.\n\n"
            "Checked: Southfield's closing date, couriers still listed"
            " there, couriers at Millbank, customers at Millbank"
        ),
        solution=("BEGIN;\n"
                  "UPDATE depots SET closed_on = '2026-07-01' WHERE depot_id = 7;\n"
                  "UPDATE couriers SET depot_id = 8 WHERE depot_id = 7 AND left_on IS NULL;\n"
                  "UPDATE customers SET depot_id = 8 WHERE depot_id = 7;\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE depots SET closed_on = '2026-07-01' WHERE depot_id = 7;\n"
                  "UPDATE couriers SET depot_id = 8 WHERE depot_id = 7 AND left_on IS NULL;\n"
                  "UPDATE customers SET depot_id = 8 WHERE depot_id = 7;"),
        driver_sql="ROLLBACK;",
        probe_sql=("SELECT (SELECT closed_on FROM depots WHERE depot_id = 7),"
                   " (SELECT COUNT(*) FROM couriers WHERE depot_id = 7),"
                   " (SELECT COUNT(*) FROM couriers WHERE depot_id = 8),"
                   " (SELECT COUNT(*) FROM customers WHERE depot_id = 8)"),
        note="BEGIN opens a transaction and COMMIT makes everything"
             " since then permanent in one step, so no reader ever sees"
             " a depot that is closed but still has its couriers. Until"
             " COMMIT nothing is safe: the trap stops one line short,"
             " and the question's ROLLBACK undoes all three UPDATEs."
             " After a COMMIT that ROLLBACK has nothing of yours left"
             " to undo. Four couriers remain at Southfield: the ones"
             " who left before it closed, and whose history should"
             " still say where they worked.",
        claims=[("closed, four former couriers left behind, Millbank at 12 and 145",
                 lambda rows, c: rows == [("2026-07-01", 4, 12, 145)])],
    ),
    dict(
        id=14, ledger="Q1310", concept="ORDER", tier="5 - Procedures",
        kind="script",
        title="Lost parcels, archived and then removed",
        prompt=(
            "A parcel is LOST when it was never delivered and has a"
            " 'failed' scan. Write the procedure that clears the lost"
            " parcels out, as one transaction, in an order that works:"
            " create a table lost_parcels holding the parcel_id,"
            " customer_id and postage_cents of every lost parcel"
            " (CREATE TABLE ... AS); delete those parcels' scans;"
            " delete the parcels. Foreign keys are on, so a parcel"
            " that still has scans cannot be deleted -- and once its"
            " scans are gone, they can no longer say it was lost.\n\n"
            "Checked: rows in lost_parcels and their postage added up,"
            " parcels left, scans left"
        ),
        solution=("BEGIN;\n"
                  "CREATE TABLE lost_parcels AS\n"
                  "  SELECT parcel_id, customer_id, postage_cents FROM parcels\n"
                  "  WHERE delivered_at IS NULL\n"
                  "    AND parcel_id IN (SELECT parcel_id FROM scans WHERE status = 'failed');\n"
                  "DELETE FROM scans WHERE parcel_id IN (SELECT parcel_id FROM lost_parcels);\n"
                  "DELETE FROM parcels WHERE parcel_id IN (SELECT parcel_id FROM lost_parcels);\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "CREATE TABLE lost_parcels AS\n"
                  "  SELECT parcel_id, customer_id, postage_cents FROM parcels\n"
                  "  WHERE delivered_at IS NULL\n"
                  "    AND parcel_id IN (SELECT parcel_id FROM scans WHERE status = 'failed');\n"
                  "DELETE FROM scans WHERE parcel_id IN (SELECT parcel_id FROM lost_parcels);\n"
                  "DELETE FROM parcels WHERE delivered_at IS NULL\n"
                  "  AND parcel_id IN (SELECT parcel_id FROM scans WHERE status = 'failed');\n"
                  "COMMIT;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM lost_parcels), (SELECT SUM(postage_cents) FROM lost_parcels),"
                   " (SELECT COUNT(*) FROM parcels), (SELECT COUNT(*) FROM scans)"),
        note="A procedure is its order. The archive comes first because"
             " it is the only step that can still see what 'lost'"
             " means; after that it IS the list, and both DELETEs read"
             " their ids from it. Scans go before parcels because the"
             " foreign key forbids a scan whose parcel is missing. The"
             " trap asks the original question again for the last step:"
             " by then no failed scan of a lost parcel exists, the"
             " DELETE matches nothing, and 113 parcels are left with no"
             " history at all. CREATE TABLE ... AS copies values and"
             " column names, not keys or constraints.",
        claims=[("113 parcels archived and gone, with their 523 scans",
                 lambda rows, c: rows == [(113, 79650, 24000 - 113, 112378 - 523)])],
    ),
    dict(
        id=15, ledger="Q1311", concept="INSTEAD", tier="5 - Procedures",
        kind="script",
        title="A delivery procedure you call with INSERT",
        prompt=(
            "A trigger body is the one place SQLite stores a procedure."
            " Create a view deliveries showing the parcel_id, courier_id"
            " and delivered_at of every delivered parcel, and an INSTEAD"
            " OF INSERT trigger on it that does two things with the row"
            " it is offered: records the courier and the time on that"
            " parcel, and adds a 'delivered' scan for it at the parcel's"
            " DESTINATION depot, with the same courier and time. The"
            " question then delivers two lost parcels, 40 and 122, by"
            " inserting into the view.\n\n"
            "Checked: for parcels 40 and 122: the courier, the delivery"
            " time, and the depot and status of any scan dated July"
        ),
        solution=("CREATE VIEW deliveries AS\n"
                  "  SELECT parcel_id, courier_id, delivered_at FROM parcels\n"
                  "  WHERE delivered_at IS NOT NULL;\n"
                  "CREATE TRIGGER deliver INSTEAD OF INSERT ON deliveries\n"
                  "BEGIN\n"
                  "  UPDATE parcels SET courier_id = NEW.courier_id, delivered_at = NEW.delivered_at\n"
                  "  WHERE parcel_id = NEW.parcel_id;\n"
                  "  INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status)\n"
                  "  SELECT parcel_id, dest_depot_id, NEW.courier_id, NEW.delivered_at, 'delivered'\n"
                  "  FROM parcels WHERE parcel_id = NEW.parcel_id;\n"
                  "END;"),
        trap_sql=("CREATE VIEW deliveries AS\n"
                  "  SELECT parcel_id, courier_id, delivered_at FROM parcels\n"
                  "  WHERE delivered_at IS NOT NULL;\n"
                  "CREATE TRIGGER deliver INSTEAD OF INSERT ON deliveries\n"
                  "BEGIN\n"
                  "  UPDATE parcels SET courier_id = NEW.courier_id, delivered_at = NEW.delivered_at\n"
                  "  WHERE parcel_id = NEW.parcel_id;\n"
                  "END;"),
        driver_sql=("INSERT INTO deliveries (parcel_id, courier_id, delivered_at) VALUES (40, 6, '2026-07-01 09:30');\n"
                    "INSERT INTO deliveries (parcel_id, courier_id, delivered_at) VALUES (122, 20, '2026-07-01 11:15');"),
        probe_sql=("SELECT p.parcel_id, p.courier_id, p.delivered_at, s.depot_id, s.status FROM parcels p"
                   " LEFT JOIN scans s ON s.parcel_id = p.parcel_id AND s.scanned_at >= '2026-07-01'"
                   " WHERE p.parcel_id IN (40, 122)"),
        note="A view cannot be written to, so INSERT INTO a view is an"
             " error -- unless it has an INSTEAD OF trigger, in which"
             " case the trigger's body runs INSTEAD and the INSERT's"
             " values arrive as NEW. That makes the view a procedure"
             " with named parameters: one INSERT, and both tables are"
             " updated in the same statement, so they cannot disagree."
             " The trap's procedure does half the job, a parcel marked"
             " delivered with no scan to show for it. The scan's depot"
             " is read from the parcel, not passed in: the caller"
             " cannot get it wrong.",
        claims=[("both parcels delivered, each with a scan at its destination",
                 lambda rows, c: sorted(rows) == [(40, 6, "2026-07-01 09:30", 5, "delivered"),
                                                  (122, 20, "2026-07-01 11:15", 1, "delivered")])],
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
