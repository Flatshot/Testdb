"""Practice exercises: thirty questions on the railway schema.

This set changes the buckets. After three familiar warm-ups, sixteen SELECT
questions cover four areas no earlier set touched -- JSON, hierarchies, NULL
logic and subquery forms, distributions -- then three familiar shapes. The
last eight are WRITABLE questions, graded on the state of the database after
your script runs, on constructs none of the four earlier writable stages
used --

  * CASE inside an UPDATE, and the NULL a CASE without ELSE returns
  * ON CONFLICT DO UPDATE ... WHERE: an upsert that only improves a row
  * CREATE TABLE with every kind of constraint, driven by inserts it refuses
  * the rebuild-a-table migration, with PRAGMA foreign_keys off and on
  * RAISE(IGNORE): a trigger that drops one row of a multi-row INSERT
  * a view whose SELECT starts with WITH RECURSIVE
  * CREATE UNIQUE INDEX as a constraint on an existing table
  * a STRICT table

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the inserts your constraint,
trigger, index or STRICT table should refuse or let through.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q672", concept="A1", tier="1 - Warm-up",
        title="Stations per town, surveyed or not",
        prompt=(
            "One row per town: how many stations it has, and how many of"
            " them have never been surveyed for step-free access.\n\n"
            "An unsurveyed station has step_free NULL.\n\n"
            "Return: town, stations, unsurveyed"
        ),
        solution=("SELECT town, COUNT(*), SUM(step_free IS NULL) FROM stations"
                  " GROUP BY 1"),
        trap_sql=("SELECT town, COUNT(*), COUNT(step_free) FROM stations"
                  " GROUP BY 1"),
        note="COUNT(column) counts the rows where the column is NOT NULL,"
             " so the trap reports the surveyed stations under an"
             " 'unsurveyed' heading. Counting NULLs takes a condition, and"
             " SUM(x IS NULL) is the shortest one: a comparison is 0 or 1"
             " in SQLite. COUNT(*) - COUNT(step_free) says the same thing.",
        claims=[("twenty towns, unsurveyed summing to the NULL count",
                 lambda rows, c: len(rows) == 20
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM stations WHERE step_free IS NULL"
                 ).fetchone()[0])],
    ),
    dict(
        id=2, ledger="Q673", concept="A2", tier="1 - Warm-up",
        title="Front and rear",
        prompt=(
            "One row per position in the train: how many workings there"
            " have been at that position -- rows of service_units -- and"
            " the average seats of the units that took it, to one"
            " decimal.\n\n"
            "Return: position, workings, avg_seats"
        ),
        solution=("SELECT su.position, COUNT(*), ROUND(AVG(r.seats), 1)"
                  " FROM service_units su JOIN rolling_stock r"
                  " ON r.unit_id = su.unit_id GROUP BY 1"),
        trap_sql=("SELECT su.position, COUNT(DISTINCT su.unit_id),"
                  " ROUND(AVG(r.seats), 1) FROM service_units su"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id GROUP BY 1"),
        note="A working is a row, so COUNT(*) is the count asked for. The"
             " trap counts DISTINCT units, which is how many different"
             " units have ever taken the position -- forty-odd, against"
             " ten thousand workings. COUNT(DISTINCT) is the right tool"
             " when a join has multiplied rows; here nothing has, and it"
             " answers a different question.",
        claims=[("two positions, the front worked more often",
                 lambda rows, c: len(rows) == 2
                 and dict((r[0], r[1]) for r in rows)[1]
                 > dict((r[0], r[1]) for r in rows)[2])],
    ),
    dict(
        id=3, ledger="Q674", concept="C2", tier="1 - Warm-up",
        title="Services and first-class sales, per line",
        prompt=(
            "For each line: how many services it scheduled, and how many"
            " first-class tickets it sold.\n\n"
            "Services with no tickets still count as services.\n\n"
            "Return: line_id, services, first_class"
        ),
        solution=("SELECT s.line_id, COUNT(DISTINCT s.service_id),"
                  " SUM(t.class = 'first') FROM services s LEFT JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY 1"),
        trap_sql=("SELECT s.line_id, COUNT(s.service_id),"
                  " SUM(t.class = 'first') FROM services s LEFT JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY 1"),
        note="The join is one row per TICKET, so COUNT(s.service_id) counts"
             " a service once per ticket it sold -- six thousand per line"
             " instead of nineteen hundred. COUNT(DISTINCT) repairs it. The"
             " LEFT JOIN keeps ticketless services in that count, and their"
             " NULL class contributes nothing to the SUM, because NULL ="
             " 'first' is NULL and SUM skips it.",
        claims=[("six lines, services summing to the timetable",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM services").fetchone()[0])],
    ),
    # ============================================================= 2 JSON
    dict(
        id=4, ledger="Q675", concept="JSN", tier="2 - JSON",
        title="A unit as a JSON object",
        prompt=(
            "Units 1 to 8, each as one JSON object with keys model, seats,"
            " built and refurbished -- numbers as numbers, and a unit never"
            " refurbished carrying a JSON null.\n\n"
            "Use json_object. Building JSON by gluing strings together is"
            " the trap.\n\n"
            "Return: unit_id, doc"
        ),
        solution=("SELECT unit_id, json_object('model', model, 'seats', seats,"
                  " 'built', built_year, 'refurbished', refurbished_year)"
                  " FROM rolling_stock WHERE unit_id <= 8"),
        trap_sql=("SELECT unit_id, '{\"model\":\"' || model || '\",\"seats\":'"
                  " || seats || ',\"built\":' || built_year"
                  " || ',\"refurbished\":' || refurbished_year || '}'"
                  " FROM rolling_stock WHERE unit_id <= 8"),
        note="json_object takes key, value, key, value and does the"
             " quoting, escaping and typing itself: an INTEGER column"
             " becomes a JSON number, TEXT a JSON string, and NULL the"
             " JSON null. The trap concatenates, and concatenating a NULL"
             " makes the WHOLE string NULL -- units 6 and 7 come back as"
             " no document at all. It would also break on a name with a"
             " quote in it. Never build JSON with ||.",
        claims=[("eight documents, all valid JSON, two with a null",
                 lambda rows, c: len(rows) == 8 and all(
                     r[1] is not None and c.execute(
                         "SELECT json_valid(?)", (r[1],)).fetchone()[0]
                     for r in rows)
                 and sum(1 for r in rows if '"refurbished":null' in r[1]) == 2)],
    ),
    dict(
        id=5, ledger="Q676", concept="JSN", tier="2 - JSON",
        title="A route as a JSON array",
        prompt=(
            "For the first service that ran (not cancelled) on each line --"
            " the lowest service_id -- its calling points as a JSON array of"
            " station NAMES in stop order.\n\n"
            "json_group_array is the aggregate. Give it the names and the"
            " order from a subquery that joins stops to stations first.\n\n"
            "Return: line_id, route"
        ),
        solution=("SELECT line_id, json_group_array(name ORDER BY stop_seq)"
                  " FROM (SELECT s.line_id, sp.stop_seq, st.name FROM services s"
                  " JOIN stops sp ON sp.service_id = s.service_id"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE s.service_id IN (SELECT MIN(service_id) FROM services"
                  " WHERE cancelled = 0 GROUP BY line_id)) GROUP BY line_id"),
        trap_sql=("SELECT line_id, '[' || group_concat(name, ',' ORDER BY stop_seq)"
                  " || ']' FROM (SELECT s.line_id, sp.stop_seq, st.name"
                  " FROM services s JOIN stops sp ON sp.service_id = s.service_id"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE s.service_id IN (SELECT MIN(service_id) FROM services"
                  " WHERE cancelled = 0 GROUP BY line_id)) GROUP BY line_id"),
        note="json_group_array is GROUP_CONCAT's JSON cousin: it quotes"
             " each string, escapes it, and wraps the lot in brackets. The"
             " trap wraps a group_concat in brackets by hand and produces"
             " [Fenwick Riverside,Langton Central,...] -- not JSON, as"
             " json_valid() will confirm. One caution for this SQLite"
             " build: json_group_array(st.name ORDER BY sp.stop_seq)"
             " straight over the join emits the SORT KEYS instead of the"
             " names; group_concat does not. Hence the subquery.",
        claims=[("six lines, each a valid array of six to ten names",
                 lambda rows, c: len(rows) == 6 and all(
                     c.execute("SELECT json_valid(?) AND json_array_length(?)"
                               " BETWEEN 6 AND 10", (r[1], r[1])).fetchone()[0]
                     for r in rows))],
    ),
    dict(
        id=6, ledger="Q677", concept="JSN", tier="2 - JSON",
        title="A list handed in as JSON",
        prompt=(
            "An app sends the station ids it wants as JSON text:"
            " '[5, 12, 40, 58]'. Return each of those stations' name and"
            " town, by unnesting the array with json_each and joining --"
            " no IN list typed by hand.\n\n"
            "Return: station_id, name, town"
        ),
        solution=("SELECT j.value, st.name, st.town FROM json_each('[5, 12, 40, 58]') j"
                  " JOIN stations st ON st.station_id = j.value"),
        trap_sql=("SELECT j.key, st.name, st.town FROM json_each('[5, 12, 40, 58]') j"
                  " JOIN stations st ON st.station_id = j.key"),
        note="json_each is a table-valued function: put it in FROM and it"
             " yields one row per element, with `value` holding the element"
             " and `key` its position (0, 1, 2...). The trap joins on key,"
             " so it fetches stations 1 to 3 and drops the 0. This is how"
             " a variable-length list gets into a query without building"
             " SQL text -- the JSON is one bound parameter.",
        claims=[("the four stations asked for",
                 lambda rows, c: sorted(r[0] for r in rows) == [5, 12, 40, 58])],
    ),
    dict(
        id=7, ledger="Q678", concept="JSN", tier="2 - JSON",
        title="A nested document per line",
        prompt=(
            "Each line as one JSON object: its name under 'line', its"
            " colour under 'colour', and under 'towns' a JSON array of the"
            " DISTINCT towns it calls in, alphabetical.\n\n"
            "A subquery builds the array; json_object nests it.\n\n"
            "Return: line_id, doc"
        ),
        solution=("SELECT l.line_id, json_object('line', l.name, 'colour', l.colour,"
                  " 'towns', (SELECT json_group_array(town ORDER BY town) FROM"
                  " (SELECT DISTINCT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE s.line_id = l.line_id)))"
                  " FROM lines l"),
        trap_sql=("SELECT l.line_id, json_object('line', l.name, 'colour', l.colour,"
                  " 'towns', (SELECT json_group_array(st.town ORDER BY st.town)"
                  " FROM stops sp JOIN services s ON s.service_id = sp.service_id"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE s.line_id = l.line_id)) FROM lines l"),
        note="A JSON value inside json_object stays JSON -- the array is"
             " nested, not stuffed in as a string -- because json_group_array"
             " returns a value SQLite knows is JSON. The trap forgets"
             " DISTINCT and the array holds one entry per STOP the line has"
             " ever made: tens of thousands of towns. Read a nested value"
             " back with json_extract(doc, '$.towns[0]') or the ->>"
             " operator.",
        claims=[("six documents, each with five to ten towns",
                 lambda rows, c: len(rows) == 6 and all(
                     5 <= c.execute("SELECT json_array_length(?, '$.towns')",
                                    (r[1],)).fetchone()[0] <= 10 for r in rows))],
    ),
    # ====================================================== 3 Hierarchies
    dict(
        id=8, ledger="Q679", concept="R1", tier="3 - Hierarchies",
        title="How far down the tree",
        prompt=(
            "Every member of staff with their depth in the reporting tree:"
            " 0 for the one person who reports to nobody, 1 for those who"
            " report to them, and so on. Forty rows.\n\n"
            "Return: staff_id, depth"
        ),
        solution=("WITH RECURSIVE t(staff_id, depth) AS (SELECT staff_id, 0"
                  " FROM staff WHERE reports_to IS NULL UNION ALL"
                  " SELECT s.staff_id, t.depth + 1 FROM staff s"
                  " JOIN t ON s.reports_to = t.staff_id) SELECT staff_id, depth"
                  " FROM t"),
        trap_sql=("WITH RECURSIVE t(staff_id, reports_to, depth) AS"
                  " (SELECT staff_id, reports_to, 0 FROM staff"
                  " WHERE reports_to IS NULL UNION ALL SELECT s.staff_id,"
                  " s.reports_to, t.depth + 1 FROM staff s"
                  " JOIN t ON s.staff_id = t.reports_to) SELECT staff_id, depth"
                  " FROM t"),
        note="A recursive CTE has an anchor -- the top -- and a step that"
             " joins the table to what the CTE has so far. The step's join"
             " direction is everything: s.reports_to = t.staff_id finds the"
             " people UNDER what is already there. The trap has it the"
             " other way round, looks for the person ABOVE the top, finds"
             " nobody, and returns one row. Depth is carried along by"
             " adding one at each step.",
        claims=[("forty people, one at depth 0, deepest at 4",
                 lambda rows, c: len(rows) == 40
                 and sum(1 for r in rows if r[1] == 0) == 1
                 and max(r[1] for r in rows) == 4)],
    ),
    dict(
        id=9, ledger="Q680", concept="R1", tier="3 - Hierarchies",
        title="The chain, written out",
        prompt=(
            "Every member of staff with the chain of names from the top of"
            " the tree down to them, joined by ' > ' -- so the top person's"
            " chain is just their own name.\n\n"
            "Return: staff_id, chain"
        ),
        solution=("WITH RECURSIVE t(staff_id, chain) AS (SELECT staff_id, name"
                  " FROM staff WHERE reports_to IS NULL UNION ALL"
                  " SELECT s.staff_id, t.chain || ' > ' || s.name FROM staff s"
                  " JOIN t ON s.reports_to = t.staff_id) SELECT staff_id, chain"
                  " FROM t"),
        trap_sql=("WITH RECURSIVE t(staff_id, chain) AS (SELECT staff_id, name"
                  " FROM staff WHERE reports_to IS NULL UNION ALL"
                  " SELECT s.staff_id, s.name || ' > ' || t.chain FROM staff s"
                  " JOIN t ON s.reports_to = t.staff_id) SELECT staff_id, chain"
                  " FROM t"),
        note="The recursion carries a string instead of a number, and each"
             " step appends the new name to the END. The trap prepends,"
             " so the chain reads from the person up to the top -- the"
             " same names, backwards. Which end you build from is a choice;"
             " the prompt made it. This is materialised-path in one query,"
             " and is what Postgres does with ltree.",
        claims=[("forty chains, all starting with the top person",
                 lambda rows, c: len(rows) == 40 and all(
                     r[1].startswith(c.execute(
                         "SELECT name FROM staff WHERE reports_to IS NULL"
                     ).fetchone()[0]) for r in rows))],
    ),
    dict(
        id=10, ledger="Q681", concept="R1", tier="3 - Hierarchies",
        title="Everyone above staff 37",
        prompt=(
            "The managers above staff member 37, all the way to the top,"
            " with how many steps up each one is: 1 for the direct"
            " manager.\n\n"
            "This walks UP the tree, so the step follows reports_to from"
            " the person, not from the top.\n\n"
            "Return: staff_id, name, steps_up"
        ),
        solution=("WITH RECURSIVE up(staff_id, steps) AS (SELECT reports_to, 1"
                  " FROM staff WHERE staff_id = 37 UNION ALL SELECT s.reports_to,"
                  " up.steps + 1 FROM staff s JOIN up ON s.staff_id = up.staff_id"
                  " WHERE s.reports_to IS NOT NULL) SELECT up.staff_id, s.name,"
                  " up.steps FROM up JOIN staff s ON s.staff_id = up.staff_id"),
        trap_sql=("SELECT m.staff_id, m.name, 1 FROM staff s JOIN staff m"
                  " ON m.staff_id = s.reports_to WHERE s.staff_id = 37"),
        note="The same recursion pointed upward: the anchor is 37's"
             " manager, and each step takes the manager's manager until"
             " reports_to runs out. The WHERE in the step is the stop"
             " condition; without it the top person's NULL reports_to"
             " would produce a row with no staff_id. The trap is a single"
             " self-join -- one level -- which is all a join without"
             " recursion can ever reach.",
        claims=[("a chain of managers ending at the top",
                 lambda rows, c: len(rows) == max(r[2] for r in rows)
                 and any(r[0] == c.execute(
                     "SELECT staff_id FROM staff WHERE reports_to IS NULL"
                 ).fetchone()[0] for r in rows))],
    ),
    dict(
        id=11, ledger="Q682", concept="R1", tier="3 - Hierarchies",
        title="Headcount below each manager",
        prompt=(
            "For everyone who has at least one person below them: how many"
            " people are under them at ANY depth -- reports, reports of"
            " reports, and so on.\n\n"
            "Seed the recursion with every person as their own root, then"
            " count what each root reaches.\n\n"
            "Return: staff_id, headcount_below"
        ),
        solution=("WITH RECURSIVE t(root, staff_id) AS (SELECT staff_id, staff_id"
                  " FROM staff UNION ALL SELECT t.root, s.staff_id FROM staff s"
                  " JOIN t ON s.reports_to = t.staff_id) SELECT root, COUNT(*) - 1"
                  " FROM t GROUP BY root HAVING COUNT(*) > 1"),
        trap_sql=("SELECT reports_to, COUNT(*) FROM staff"
                  " WHERE reports_to IS NOT NULL GROUP BY reports_to"),
        note="Forty recursions at once: the anchor puts every person in as"
             " a root, and each step extends every root's set. The result"
             " is one row per (root, descendant) pair, and counting per"
             " root -- minus the root itself -- is the headcount. The trap"
             " counts direct reports only: right for the bottom managers,"
             " and 4 instead of 39 for the top. Sub-tree sizes are this"
             " pattern; sub-tree SUMS are the same query with SUM.",
        claims=[("the top person has everyone below them",
                 lambda rows, c: dict(rows)[c.execute(
                     "SELECT staff_id FROM staff WHERE reports_to IS NULL"
                 ).fetchone()[0]] == 39 and len(rows) > 5)],
    ),
    # ===================================== 4 NULL logic and subqueries
    dict(
        id=12, ledger="Q683", concept="C7", tier="4 - NULL logic and subqueries",
        title="Not known to be long",
        prompt=(
            "Per kind of incident, how many are NOT over 30 minutes -- and"
            " an incident whose delay was never quantified is not over 30"
            " minutes either, so it counts.\n\n"
            "Return: kind, incidents"
        ),
        solution=("SELECT kind, COUNT(*) FROM incidents WHERE delay_minutes <= 30"
                  " OR delay_minutes IS NULL GROUP BY 1"),
        trap_sql=("SELECT kind, COUNT(*) FROM incidents"
                  " WHERE NOT (delay_minutes > 30) GROUP BY 1"),
        note="Three-valued logic. NULL > 30 is not false, it is UNKNOWN,"
             " and NOT UNKNOWN is still UNKNOWN -- and a WHERE keeps only"
             " rows that are TRUE. So the trap drops every unquantified"
             " incident, 178 of them, while looking like the exact negation"
             " of 'over 30'. A NULL has to be asked about by name: IS"
             " NULL, or COALESCE it to something first.",
        claims=[("five kinds, totalling every incident not known to exceed 30",
                 lambda rows, c: len(rows) == 5
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM incidents WHERE delay_minutes IS NULL"
                     " OR delay_minutes <= 30").fetchone()[0])],
    ),
    dict(
        id=13, ledger="Q684", concept="C7", tier="4 - NULL logic and subqueries",
        title="Never refurbished goes last",
        prompt=(
            "Every unit numbered by refurbishment year, earliest first --"
            " and the units NEVER refurbished numbered after all the others,"
            " not before. Ties by unit_id.\n\n"
            "Return: unit_id, refurbished_year, position"
        ),
        solution=("SELECT unit_id, refurbished_year, ROW_NUMBER() OVER"
                  " (ORDER BY refurbished_year NULLS LAST, unit_id)"
                  " FROM rolling_stock"),
        trap_sql=("SELECT unit_id, refurbished_year, ROW_NUMBER() OVER"
                  " (ORDER BY refurbished_year, unit_id) FROM rolling_stock"),
        note="SQLite sorts NULL before everything in ascending order, so"
             " the trap numbers the thirty never-refurbished units 1 to 30"
             " and the real years after. NULLS LAST (3.30+) says where they"
             " go without changing the direction. The older idiom is a"
             " two-key sort: ORDER BY refurbished_year IS NULL,"
             " refurbished_year -- the IS NULL is 0 or 1, and 0 sorts"
             " first. The window makes the order a graded column.",
        claims=[("fifty rows, the NULLs numbered last",
                 lambda rows, c: len(rows) == 50 and all(
                     (r[1] is None) == (r[2] > 20) for r in rows))],
    ),
    dict(
        id=14, ledger="Q685", concept="SUB", tier="4 - NULL logic and subqueries",
        title="As many seats as every Class 170",
        prompt=(
            "Units with at least as many seats as EVERY Class 170 unit --"
            " the biggest Class 170s themselves included.\n\n"
            "SQLite has no ALL or ANY. 'At least as many as every one of"
            " them' is a comparison with one number from a subquery --"
            " which number?\n\n"
            "Return: unit_id, model, seats"
        ),
        solution=("SELECT unit_id, model, seats FROM rolling_stock WHERE seats >="
                  " (SELECT MAX(seats) FROM rolling_stock WHERE model = 'Class 170')"),
        trap_sql=("SELECT unit_id, model, seats FROM rolling_stock WHERE seats >="
                  " (SELECT MIN(seats) FROM rolling_stock WHERE model = 'Class 170')"),
        note=">= ALL (set) is >= MAX(set); >= ANY (set) is >= MIN(set). The"
             " trap answers 'at least as many as SOME Class 170', which is"
             " the whole fleet. A scalar subquery -- one row, one column --"
             " can stand anywhere a value can, and an aggregate guarantees"
             " the one row. Postgres and SQL Server have the keywords; the"
             " MAX/MIN form is what they compile to.",
        claims=[("every returned unit matches or beats the biggest Class 170",
                 lambda rows, c: len(rows) > 5 and len({r[2] for r in rows}) > 1
                 and all(r[2] >= c.execute(
                     "SELECT MAX(seats) FROM rolling_stock WHERE model"
                     " = 'Class 170'").fetchone()[0] for r in rows))],
    ),
    dict(
        id=15, ledger="Q686", concept="SUB", tier="4 - NULL logic and subqueries",
        title="The average service's takings",
        prompt=(
            "For each line, the average revenue PER SERVICE, to the nearest"
            " penny -- add up each service's tickets first, then average"
            " those totals. Services with no tickets do not count.\n\n"
            "An aggregate of an aggregate needs two levels.\n\n"
            "Return: line_id, avg_service_revenue"
        ),
        solution=("SELECT line_id, ROUND(AVG(r)) FROM (SELECT s.line_id,"
                  " SUM(t.price_pence) r FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY s.service_id)"
                  " GROUP BY 1"),
        trap_sql=("SELECT s.line_id, ROUND(AVG(t.price_pence)) FROM services s"
                  " JOIN tickets t ON t.service_id = s.service_id GROUP BY 1"),
        note="AVG(price) is the average TICKET, about sixteen pounds; the"
             " average SERVICE is four times that, because a service sells"
             " several. You cannot write AVG(SUM(x)) in one level -- SQLite"
             " refuses the nesting -- so the inner query groups to one row"
             " per service and the outer one averages those rows. A CTE"
             " says the same thing with a name; a derived table says it"
             " inline.",
        claims=[("six lines, each average several thousand pence",
                 lambda rows, c: len(rows) == 6
                 and all(4000 < r[1] < 10000 for r in rows))],
    ),
    # ==================================================== 5 Distributions
    dict(
        id=16, ledger="Q687", concept="DST", tier="5 - Distributions",
        title="The fleet in three tiers",
        prompt=(
            "Split the fifty units into three tiers by seats -- tier 1 the"
            " smallest -- as evenly as possible, ties by unit_id. One row"
            " per tier with how many units it holds and its smallest and"
            " largest seat count.\n\n"
            "Return: tier, units, min_seats, max_seats"
        ),
        solution=("SELECT tier, COUNT(*), MIN(seats), MAX(seats) FROM (SELECT seats,"
                  " NTILE(3) OVER (ORDER BY seats, unit_id) tier FROM rolling_stock)"
                  " GROUP BY 1"),
        trap_sql=("SELECT tier, COUNT(*), MIN(seats), MAX(seats) FROM (SELECT seats,"
                  " NTILE(3) OVER (ORDER BY seats DESC, unit_id) tier"
                  " FROM rolling_stock) GROUP BY 1"),
        note="NTILE(n) deals the ordered rows into n buckets of equal size,"
             " the first buckets taking the extra row when it does not"
             " divide: 17, 17, 16. It is a rank, not a threshold, so two"
             " units with the same seats can land in different tiers --"
             " which is why the tiebreak matters. The trap orders DESC and"
             " tier 1 is the LARGEST units, with the same tidy counts.",
        claims=[("three tiers of 17, 17 and 16, tier 1 the smallest",
                 lambda rows, c: sorted(r[1] for r in rows) == [16, 17, 17]
                 and dict((r[0], r[2]) for r in rows)[1] == c.execute(
                     "SELECT MIN(seats) FROM rolling_stock").fetchone()[0])],
    ),
    dict(
        id=17, ledger="Q688", concept="DST", tier="5 - Distributions",
        title="Where a salary sits in its role",
        prompt=(
            "Every member of staff with their salary's PERCENT_RANK within"
            " their role, to three decimals: 0 for the lowest paid in the"
            " role, 1 for the highest.\n\n"
            "Return: staff_id, role, salary, pct_rank"
        ),
        solution=("SELECT staff_id, role, salary, ROUND(PERCENT_RANK() OVER"
                  " (PARTITION BY role ORDER BY salary), 3) FROM staff"),
        trap_sql=("SELECT staff_id, role, salary, ROUND(CUME_DIST() OVER"
                  " (PARTITION BY role ORDER BY salary), 3) FROM staff"),
        note="PERCENT_RANK is (rank - 1) / (rows - 1): the fraction of the"
             " group strictly below you, so the lowest is 0 and the"
             " highest 1. CUME_DIST is rows at or below you / rows: the"
             " lowest is 1/n, never 0. The trap swaps them and every value"
             " shifts up a step. Both are 'where do I sit'; only"
             " PERCENT_RANK spans the whole 0-to-1 range.",
        claims=[("forty rows, each role running from 0 to 1",
                 lambda rows, c: len(rows) == 40 and all(
                     min(r[3] for r in rows if r[1] == role) == 0
                     and max(r[3] for r in rows if r[1] == role) == 1
                     for role in {r[1] for r in rows}))],
    ),
    dict(
        id=18, ledger="Q689", concept="DST", tier="5 - Distributions",
        title="How spread out the prices are",
        prompt=(
            "For each class, the average ticket price and its population"
            " standard deviation, both in pence to one decimal.\n\n"
            "SQLite has no STDDEV. The variance is the mean of the squares"
            " minus the square of the mean; sqrt() is built in.\n\n"
            "Return: class, avg_price, stddev"
        ),
        solution=("SELECT class, ROUND(AVG(price_pence), 1),"
                  " ROUND(sqrt(AVG(price_pence * price_pence)"
                  " - AVG(price_pence) * AVG(price_pence)), 1) FROM tickets"
                  " GROUP BY 1"),
        trap_sql=("SELECT class, ROUND(AVG(price_pence), 1),"
                  " ROUND(sqrt(AVG(price_pence * price_pence)) - AVG(price_pence), 1)"
                  " FROM tickets GROUP BY 1"),
        note="E[x^2] - E[x]^2, then the square root of the whole thing. The"
             " trap takes the root of the first term only and subtracts the"
             " mean afterwards, giving a number thirty times too small. This"
             " is the POPULATION deviation; the sample version multiplies"
             " the variance by n / (n - 1) first. sqrt() and friends arrived"
             " in 3.35; older builds need the value squared instead.",
        claims=[("three classes, deviations in the low hundreds of pence",
                 lambda rows, c: len(rows) == 3
                 and all(150 < r[2] < 400 for r in rows))],
    ),
    dict(
        id=19, ledger="Q690", concept="DST", tier="5 - Distributions",
        title="Ticket prices in five-pound bands",
        prompt=(
            "A histogram of ticket prices: how many tickets fall in each"
            " five-pound band, the band labelled by where it starts in"
            " pounds -- 0, 5, 10... A ticket at exactly 10.00 belongs to"
            " the 10 band.\n\n"
            "Return: band, tickets"
        ),
        solution="SELECT price_pence / 500 * 5, COUNT(*) FROM tickets GROUP BY 1",
        trap_sql=("SELECT CAST(ROUND(price_pence / 500.0) AS INTEGER) * 5,"
                  " COUNT(*) FROM tickets GROUP BY 1"),
        note="Integer division floors, which is exactly what a band needs:"
             " 1499 / 500 is 2, so 14.99 is in the 10 band. The trap rounds"
             " instead, and 12.60 goes UP to the 15 band -- each band"
             " becomes 'nearest 5', centred instead of floored, and the 0"
             " band disappears. Multiplying back gives the label; dividing"
             " alone gives the bucket number, which is the same grouping"
             " with worse names.",
        claims=[("bands at multiples of five, totalling the tickets",
                 lambda rows, c: all(r[0] % 5 == 0 for r in rows)
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0])],
    ),
    # ===================================================== 6 Familiar mix
    dict(
        id=20, ledger="Q691", concept="W2", tier="6 - Familiar mix",
        title="Each line's worst service",
        prompt=(
            "For each line, the service that lost the most quantified delay"
            " minutes across its incidents, and how many. One row per line;"
            " ties by the lower service_id.\n\n"
            "Return: line_id, service_id, delay_minutes"
        ),
        solution=("SELECT line_id, service_id, d FROM (SELECT s.line_id,"
                  " s.service_id, SUM(i.delay_minutes) d, ROW_NUMBER() OVER"
                  " (PARTITION BY s.line_id ORDER BY SUM(i.delay_minutes) DESC,"
                  " s.service_id) rn FROM services s JOIN incidents i"
                  " ON i.service_id = s.service_id GROUP BY s.service_id)"
                  " WHERE rn = 1"),
        trap_sql=("SELECT line_id, service_id, d FROM (SELECT s.line_id,"
                  " s.service_id, SUM(i.delay_minutes) d, ROW_NUMBER() OVER"
                  " (PARTITION BY s.line_id ORDER BY SUM(i.delay_minutes),"
                  " s.service_id) rn FROM services s JOIN incidents i"
                  " ON i.service_id = s.service_id GROUP BY s.service_id)"
                  " WHERE rn = 1"),
        note="Top-1 per group: number within the partition, keep rn = 1."
             " The trap orders ascending and finds each line's LEAST"
             " delayed service -- with SUM skipping NULLs, a service whose"
             " only delay is unquantified sums to NULL and sorts first."
             " DESC, and a tiebreak, inside the OVER.",
        claims=[("one service per line, each with real delay",
                 lambda rows, c: len(rows) == 6
                 and len({r[0] for r in rows}) == 6
                 and all(r[2] and r[2] > 30 for r in rows))],
    ),
    dict(
        id=21, ledger="Q692", concept="J1", tier="6 - Familiar mix",
        title="Consecutive calls on line 1",
        prompt=(
            "The pairs of stations that line 1's services call at one"
            " after the other: each (this stop, next stop) pair once. Nine"
            " pairs for a ten-station route.\n\n"
            "Return: from_station, to_station"
        ),
        solution=("SELECT DISTINCT a.station_id, b.station_id FROM stops a"
                  " JOIN stops b ON b.service_id = a.service_id"
                  " AND b.stop_seq = a.stop_seq + 1 JOIN services s"
                  " ON s.service_id = a.service_id WHERE s.line_id = 1"),
        trap_sql=("SELECT DISTINCT a.station_id, b.station_id FROM stops a"
                  " JOIN stops b ON b.service_id = a.service_id"
                  " AND b.stop_seq > a.stop_seq JOIN services s"
                  " ON s.service_id = a.service_id WHERE s.line_id = 1"),
        note="A self-join on the sequence: the row for stop n joined to the"
             " row for stop n + 1 of the same service. The trap joins each"
             " stop to EVERY later one and returns 45 pairs -- every"
             " journey the line offers, which is a different and also"
             " useful question. LEAD(station_id) OVER (PARTITION BY"
             " service_id ORDER BY stop_seq) says the same thing without a"
             " join.",
        claims=[("one fewer pair than the route has stations",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(*) FROM stops WHERE service_id = (SELECT"
                     " MIN(service_id) FROM services WHERE line_id = 1"
                     " AND cancelled = 0)").fetchone()[0] - 1)],
    ),
    dict(
        id=22, ledger="Q693", concept="SPN", tier="6 - Familiar mix",
        title="Days with no incidents, per month",
        prompt=(
            "For each month of the timetable, how many days had NO incident"
            " reported at all. Eighteen months, every one of which has some"
            " quiet days.\n\n"
            "A day with nothing reported has no row anywhere; generate the"
            " days first.\n\n"
            "Return: month, quiet_days"
        ),
        solution=("WITH RECURSIVE d(day) AS (SELECT '2025-01-01' UNION ALL"
                  " SELECT date(day, '+1 day') FROM d WHERE day < '2026-06-30')"
                  " SELECT strftime('%Y-%m', day), COUNT(*) FROM d"
                  " WHERE NOT EXISTS (SELECT 1 FROM incidents i"
                  " WHERE i.reported_at = d.day) GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', reported_at),"
                  " COUNT(DISTINCT reported_at) FROM incidents GROUP BY 1"),
        note="You cannot count rows that do not exist, so the date spine"
             " manufactures one per day and NOT EXISTS keeps the days the"
             " incident table never mentions. The trap counts the days WITH"
             " incidents -- eighteen tidy rows, the exact complement. Any"
             " 'how many had none' question over a time range wants a"
             " spine; a LEFT JOIN from it with IS NULL is the same thing.",
        claims=[("eighteen months, totalling the days the log skips",
                 lambda rows, c: len(rows) == 18
                 and sum(r[1] for r in rows) == 546 - c.execute(
                     "SELECT COUNT(DISTINCT reported_at) FROM incidents"
                 ).fetchone()[0])],
    ),
    # ================================================ 7 Changing the data
    # Writable questions. The editor's script runs in a sandbox copy of the
    # database, then probe_sql reads the result and THAT is compared with the
    # reference. driver_sql, where present, is run by the question after the
    # script -- to fire a trigger, or to be refused by a constraint.
    dict(
        id=23, ledger="Q694", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="A raise that depends on the role",
        prompt=(
            "One UPDATE that gives every member of staff a raise by role:"
            " managers 2%, drivers 4%, everyone else 3%. Whole pounds:"
            " CAST(ROUND(salary * factor) AS INTEGER).\n\n"
            "The factor is a CASE expression. Think about what CASE returns"
            " for a role you did not list.\n\n"
            "Checked: total salary by role"
        ),
        solution=("UPDATE staff\n"
                  "SET salary = CAST(ROUND(salary * CASE role\n"
                  "                                   WHEN 'manager' THEN 1.02\n"
                  "                                   WHEN 'driver' THEN 1.04\n"
                  "                                   ELSE 1.03\n"
                  "                                 END) AS INTEGER);"),
        trap_sql=("UPDATE staff\n"
                  "SET salary = CAST(ROUND(salary * CASE role\n"
                  "                                   WHEN 'manager' THEN 1.02\n"
                  "                                   WHEN 'driver' THEN 1.04\n"
                  "                                 END) AS INTEGER);"),
        probe_sql="SELECT role, SUM(salary) FROM staff GROUP BY 1",
        note="A CASE with no ELSE returns NULL for anything it did not"
             " match, so the trap sets every guard's and dispatcher's salary"
             " to NULL -- and only the NOT NULL constraint on the column"
             " stops it, failing the statement. Without that constraint the"
             " UPDATE would succeed and 26 salaries would be gone. One"
             " statement instead of three keeps the change atomic and the"
             " row count honest: 40.",
        claims=[("every role up by its own rate",
                 lambda rows, c: dict(rows) == {'manager': 221942,
                                                'driver': 493800,
                                                'guard': 799552,
                                                'dispatcher': 580466})],
    ),
    dict(
        id=24, ledger="Q695", concept="UPS", tier="7 - Changing the data",
        kind="script",
        title="Update only if it is an improvement",
        prompt=(
            "Two revised q1 figures for station 3 arrive: 35000 for 2025"
            " and 90000 for 2024. Both rows exist. Write two UPSERTs that"
            " create the row if missing and otherwise update q1 -- but ONLY"
            " when the new figure is higher than the stored one. The 2025"
            " figure is lower and must be ignored.\n\n"
            "Use (3, 2025, 35000, 30136, 31843, 38990) and (3, 2024, 90000,"
            " 0, 0, 0) as the VALUES.\n\n"
            "Checked: station 3's year, q1 and q2"
        ),
        solution=("INSERT INTO station_footfall (station_id, year, q1, q2, q3, q4)\n"
                  "VALUES (3, 2025, 35000, 30136, 31843, 38990)\n"
                  "ON CONFLICT (station_id, year) DO UPDATE SET q1 = excluded.q1\n"
                  "WHERE excluded.q1 > q1;\n"
                  "INSERT INTO station_footfall (station_id, year, q1, q2, q3, q4)\n"
                  "VALUES (3, 2024, 90000, 0, 0, 0)\n"
                  "ON CONFLICT (station_id, year) DO UPDATE SET q1 = excluded.q1\n"
                  "WHERE excluded.q1 > q1;"),
        trap_sql=("INSERT INTO station_footfall (station_id, year, q1, q2, q3, q4)\n"
                  "VALUES (3, 2025, 35000, 30136, 31843, 38990)\n"
                  "ON CONFLICT (station_id, year) DO UPDATE SET q1 = excluded.q1;\n"
                  "INSERT INTO station_footfall (station_id, year, q1, q2, q3, q4)\n"
                  "VALUES (3, 2024, 90000, 0, 0, 0)\n"
                  "ON CONFLICT (station_id, year) DO UPDATE SET q1 = excluded.q1;"),
        probe_sql=("SELECT year, q1, q2 FROM station_footfall WHERE station_id = 3"
                   " ORDER BY 1"),
        note="DO UPDATE takes a WHERE of its own, evaluated on the conflict:"
             " `excluded` is the row that tried to go in, and a bare column"
             " is the row already there. When the WHERE is false the"
             " statement does nothing, quietly -- 'rows changed: 1' for two"
             " statements is the tell. The trap updates unconditionally and"
             " the 2025 figure goes DOWN. This is the conditional MERGE,"
             " and the guard is what makes an upsert safe to re-run.",
        claims=[("2024 raised, 2025 left alone",
                 lambda rows, c: rows == [(2023, 40092, 42838),
                                          (2024, 90000, 40437),
                                          (2025, 36020, 30136)])],
    ),
    dict(
        id=25, ledger="Q696", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="A table that defends itself",
        prompt=(
            "Create `station_notes`: note_id INTEGER PRIMARY KEY; station_id"
            " that must reference stations; note, TEXT, required, 1 to 80"
            " characters; noted_on, TEXT, defaulting to '2026-07-01'.\n\n"
            "After your script, the question inserts three notes: a good"
            " one for station 5, one for station 999, and an empty one."
            " Exactly one should land.\n\n"
            "Checked: SELECT * FROM station_notes"
        ),
        solution=("CREATE TABLE station_notes (\n"
                  "  note_id    INTEGER PRIMARY KEY,\n"
                  "  station_id INTEGER NOT NULL REFERENCES stations(station_id),\n"
                  "  note       TEXT NOT NULL CHECK (length(note) BETWEEN 1 AND 80),\n"
                  "  noted_on   TEXT NOT NULL DEFAULT '2026-07-01'\n"
                  ");"),
        trap_sql=("CREATE TABLE station_notes (\n"
                  "  note_id    INTEGER PRIMARY KEY,\n"
                  "  station_id INTEGER NOT NULL REFERENCES stations(station_id),\n"
                  "  note       TEXT NOT NULL,\n"
                  "  noted_on   TEXT NOT NULL DEFAULT '2026-07-01'\n"
                  ");"),
        driver_sql=("INSERT INTO station_notes (station_id, note)"
                    " VALUES (5, 'Lift out of order');\n"
                    "INSERT INTO station_notes (station_id, note)"
                    " VALUES (999, 'Ghost station');\n"
                    "INSERT INTO station_notes (station_id, note) VALUES (5, '');"),
        probe_sql=("SELECT note_id, station_id, note, noted_on FROM station_notes"
                   " ORDER BY 1"),
        note="Four kinds of constraint in one table: PRIMARY KEY, a FOREIGN"
             " KEY (REFERENCES), NOT NULL, and CHECK -- plus a DEFAULT, which"
             " is not a constraint but fills a column the insert left out."
             " NOT NULL does not reject the empty string; '' is a value."
             " The trap has no CHECK, so the empty note lands. The foreign"
             " key works only because the sandbox turns PRAGMA foreign_keys"
             " on; SQLite's default is off.",
        claims=[("one note, for station 5, dated by default",
                 lambda rows, c: rows == [(1, 5, 'Lift out of order',
                                           '2026-07-01')])],
    ),
    dict(
        id=26, ledger="Q697", concept="MIG", tier="7 - Changing the data",
        kind="script",
        title="Add a constraint by rebuilding the table",
        prompt=(
            "`operators` needs a CHECK (since_year >= 1900). ALTER TABLE"
            " cannot add one, so rebuild: create the new table, copy the"
            " rows, drop the old one, rename the new one into place.\n\n"
            "Services reference operators, so DROP TABLE is refused while"
            " foreign keys are on. Turn them off for the rebuild and back"
            " on after -- a PRAGMA, not a transaction, since PRAGMA"
            " foreign_keys is a no-op inside one.\n\n"
            "Checked: the row count, whether the table's SQL now has a"
            " CHECK, and how many services would be orphaned"
        ),
        solution=("PRAGMA foreign_keys = OFF;\n"
                  "CREATE TABLE operators_new (\n"
                  "  operator_id INTEGER PRIMARY KEY,\n"
                  "  name        TEXT NOT NULL UNIQUE,\n"
                  "  since_year  INTEGER NOT NULL CHECK (since_year >= 1900)\n"
                  ");\n"
                  "INSERT INTO operators_new SELECT operator_id, name, since_year"
                  " FROM operators;\n"
                  "DROP TABLE operators;\n"
                  "ALTER TABLE operators_new RENAME TO operators;\n"
                  "PRAGMA foreign_keys = ON;"),
        trap_sql=("CREATE TABLE operators_new (\n"
                  "  operator_id INTEGER PRIMARY KEY,\n"
                  "  name        TEXT NOT NULL UNIQUE,\n"
                  "  since_year  INTEGER NOT NULL CHECK (since_year >= 1900)\n"
                  ");\n"
                  "INSERT INTO operators_new SELECT operator_id, name, since_year"
                  " FROM operators;\n"
                  "DROP TABLE operators;\n"
                  "ALTER TABLE operators_new RENAME TO operators;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM operators),"
                   " (SELECT instr(sql, 'CHECK') > 0 FROM sqlite_master"
                   " WHERE type = 'table' AND name = 'operators'),"
                   " (SELECT COUNT(*) FROM services s LEFT JOIN operators o"
                   " ON o.operator_id = s.operator_id WHERE o.operator_id IS NULL)"),
        note="This is SQLite's official recipe for any change ALTER TABLE"
             " cannot make -- a new constraint, a changed type, a dropped"
             " primary key. DROP TABLE is an implicit DELETE of every row,"
             " and with foreign keys on, deleting a referenced operator is"
             " refused: the trap stops there. With them off, the rows are"
             " copied first so nothing is orphaned, and the rename brings"
             " the references back into line. sqlite_master holds each"
             " table's CREATE statement, which is how the probe checks.",
        claims=[("four operators, a CHECK in place, nothing orphaned",
                 lambda rows, c: rows == [(4, 1, 0)])],
    ),
    dict(
        id=27, ledger="Q698", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="Drop the bad row, keep the rest",
        prompt=(
            "Write a trigger that silently discards any ticket inserted"
            " with a price of 0 -- no error, the other rows of the same"
            " INSERT still land.\n\n"
            "After your script, the question inserts three tickets in ONE"
            " statement; the middle one is free. Two should land.\n\n"
            "Checked: id and price of every ticket after the last existing"
            " one"
        ),
        solution=("CREATE TRIGGER drop_free_tickets\n"
                  "BEFORE INSERT ON tickets\n"
                  "WHEN NEW.price_pence = 0\n"
                  "BEGIN\n"
                  "  SELECT RAISE(IGNORE);\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER drop_free_tickets\n"
                  "BEFORE INSERT ON tickets\n"
                  "WHEN NEW.price_pence = 0\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'free ticket');\n"
                  "END;"),
        driver_sql=("INSERT INTO tickets (service_id, from_station, to_station,"
                    " class, price_pence, sold_at) VALUES\n"
                    "  (1, 33, 31, 'standard', 1200, '2025-01-01'),\n"
                    "  (1, 33, 35, 'standard', 0, '2025-01-01'),\n"
                    "  (1, 33, 4, 'first', 2500, '2025-01-01');"),
        probe_sql=("SELECT ticket_id, price_pence FROM tickets"
                   " WHERE ticket_id > 34460 ORDER BY 1"),
        note="RAISE has four forms. ABORT (and FAIL) raise an error and"
             " undo the statement -- all three rows, in the trap, because"
             " one statement is one unit. ROLLBACK undoes the whole"
             " transaction. IGNORE is the odd one: it skips the current"
             " row and carries on with no error, which is exactly a"
             " 'silently discard' rule. Use it sparingly; a row that"
             " vanishes without a message is hard to debug later.",
        claims=[("two tickets landed, the free one did not",
                 lambda rows, c: rows == [(34461, 1200), (34462, 2500)])],
    ),
    dict(
        id=28, ledger="Q699", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="A calendar that stores nothing",
        prompt=(
            "Create a view `calendar (day)` that yields every date from"
            " 2025-01-01 to 2026-06-30 inclusive -- 546 rows -- generated"
            " by a recursive CTE inside the view. It stores no rows.\n\n"
            "Checked: the count, first and last day, and how many days in"
            " it have no incident"
        ),
        solution=("CREATE VIEW calendar AS\n"
                  "WITH RECURSIVE d(day) AS (\n"
                  "  SELECT '2025-01-01'\n"
                  "  UNION ALL\n"
                  "  SELECT date(day, '+1 day') FROM d WHERE day < '2026-06-30')\n"
                  "SELECT day FROM d;"),
        trap_sql=("CREATE VIEW calendar AS\n"
                  "WITH RECURSIVE d(day) AS (\n"
                  "  SELECT '2025-01-01'\n"
                  "  UNION ALL\n"
                  "  SELECT date(day, '+1 day') FROM d WHERE day < '2026-06-29')\n"
                  "SELECT day FROM d;"),
        probe_sql=("SELECT COUNT(*), MIN(day), MAX(day), (SELECT COUNT(*)"
                   " FROM calendar c WHERE NOT EXISTS (SELECT 1 FROM incidents i"
                   " WHERE i.reported_at = c.day)) FROM calendar"),
        note="A view's SELECT may start with WITH, recursive or not, so the"
             " spine from question 22 becomes a permanent table-shaped"
             " thing that costs no storage and is never stale. The step"
             " reads the current day and emits the next, so the stop"
             " condition is < the last day wanted; the trap's 29th stops"
             " one short. Views like this are what generate_series"
             " provides where it is compiled in.",
        claims=[("546 days, the ends right, quiet days matching the log",
                 lambda rows, c: rows[0][:3] == (546, '2025-01-01', '2026-06-30')
                 and rows[0][3] == 546 - c.execute(
                     "SELECT COUNT(DISTINCT reported_at) FROM incidents"
                 ).fetchone()[0])],
    ),
    dict(
        id=29, ledger="Q700", concept="IDX", tier="7 - Changing the data",
        kind="script",
        title="One service per slot",
        prompt=(
            "No two services may share a line, date and departure time."
            " Enforce that with a UNIQUE index on `services`.\n\n"
            "After your script, the question inserts two services on line"
            " 4 for 2025-01-01: one at 06:09, which service 10 already"
            " holds, and one at 06:10. Exactly one should be refused.\n\n"
            "Checked: line 4's services that day, and how many unique"
            " indexes services has beyond its primary key"
        ),
        solution=("CREATE UNIQUE INDEX idx_services_slot\n"
                  "ON services (line_id, run_date, depart_time);"),
        trap_sql=("CREATE INDEX idx_services_slot\n"
                  "ON services (line_id, run_date, depart_time);"),
        driver_sql=("INSERT INTO services (line_id, operator_id, run_date,"
                    " depart_time) VALUES (4, 1, '2025-01-01', '06:09');\n"
                    "INSERT INTO services (line_id, operator_id, run_date,"
                    " depart_time) VALUES (4, 1, '2025-01-01', '06:10');"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM services WHERE line_id = 4"
                   " AND run_date = '2025-01-01'), (SELECT COUNT(*)"
                   " FROM pragma_index_list('services') WHERE \"unique\" = 1"
                   " AND origin = 'c')"),
        note="A UNIQUE index is a constraint and an index at once: the"
             " duplicate is refused with 'UNIQUE constraint failed', and"
             " lookups by (line, date) get faster as a side effect. The"
             " trap builds the same index without UNIQUE, which speeds the"
             " lookup and stops nothing. A UNIQUE clause in CREATE TABLE"
             " makes the same index automatically; on an existing table,"
             " CREATE UNIQUE INDEX is how you add one. It fails if"
             " duplicates already exist -- here there are none.",
        claims=[("one new service, one unique index",
                 lambda rows, c: rows == [(4, 1)])],
    ),
    dict(
        id=30, ledger="Q701", concept="SCT", tier="7 - Changing the data",
        kind="script",
        title="A table that refuses the wrong type",
        prompt=(
            "Create `unit_mileage (unit_id INTEGER PRIMARY KEY referencing"
            " rolling_stock, miles INTEGER NOT NULL)` as a STRICT table, so"
            " that a REAL can never be stored in the INTEGER column.\n\n"
            "After your script, the question inserts miles of 120500,"
            " 98000.5 and '77000' for units 1, 2 and 3. One should be"
            " refused; one should be converted.\n\n"
            "Checked: unit_id, miles and typeof(miles)"
        ),
        solution=("CREATE TABLE unit_mileage (\n"
                  "  unit_id INTEGER PRIMARY KEY REFERENCES rolling_stock(unit_id),\n"
                  "  miles   INTEGER NOT NULL\n"
                  ") STRICT;"),
        trap_sql=("CREATE TABLE unit_mileage (\n"
                  "  unit_id INTEGER PRIMARY KEY REFERENCES rolling_stock(unit_id),\n"
                  "  miles   INTEGER NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO unit_mileage VALUES (1, 120500);\n"
                    "INSERT INTO unit_mileage VALUES (2, 98000.5);\n"
                    "INSERT INTO unit_mileage VALUES (3, '77000');"),
        probe_sql=("SELECT unit_id, miles, typeof(miles) FROM unit_mileage"
                   " ORDER BY 1"),
        note="Ordinary SQLite columns have AFFINITY, not types: an INTEGER"
             " column stores 98000.5 as a REAL and says nothing -- the"
             " lesson of an earlier set's INSERT ... SELECT. STRICT (3.37+)"
             " makes the declared type a rule: the REAL is refused, while"
             " '77000' is still converted because it is losslessly an"
             " integer. STRICT allows only INT, INTEGER, REAL, TEXT, BLOB"
             " and ANY as types. It is the closest SQLite comes to a"
             " conventionally typed table.",
        claims=[("units 1 and 3 stored as integers, unit 2 refused",
                 lambda rows, c: rows == [(1, 120500, 'integer'),
                                          (3, 77000, 'integer')])],
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
