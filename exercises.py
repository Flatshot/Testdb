"""Practice exercises: fifteen questions on the hospital schema.

The seventh set on the district hospital, beside the sixth Python set
(pyexercises.py), at the level of the two sets before it. Same data: SEED
731, not re-seeded. Twelve SELECT questions -- a ratio of sums against an
average of ratios, HAVING against a scalar subquery, common forenames,
readings that rose on the previous one, weekend arrivals, a stay split
into whole days and hours, idle gaps in one theatre, a ward at two
instants side by side, a surgeon in two theatres on one day, a LEFT JOIN
whose filter must stay in the ON, the reading before and after, and
CUME_DIST within a ward -- and three WRITABLE questions on constructs no
earlier writable stage used:

  * a view with a window function in it
  * a CHECK constraint built on GLOB
  * rows made from a JSON list with json_each

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the inserts your constraint
should sort.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q817", concept="A2", tier="1 - Warm-up",
        title="Pence per minute in theatre",
        prompt=(
            "For each category of procedure, the tariff earned per minute"
            " of theatre time, to two decimals: the TOTAL tariff of the"
            " procedures with a recorded duration, divided by their TOTAL"
            " minutes. One ratio of two sums, not an average of ratios.\n\n"
            "Return: category, pence_per_minute"
        ),
        solution=("SELECT t.category, ROUND(1.0 * SUM(t.tariff_pence) / SUM(p.duration_minutes), 2)"
                  " FROM procedures p JOIN procedure_types t ON t.code = p.code"
                  " WHERE p.duration_minutes IS NOT NULL GROUP BY t.category"),
        trap_sql=("SELECT t.category, ROUND(AVG(1.0 * t.tariff_pence / p.duration_minutes), 2)"
                  " FROM procedures p JOIN procedure_types t ON t.code = p.code"
                  " WHERE p.duration_minutes IS NOT NULL GROUP BY t.category"),
        note="A rate over a group is sum over sum: every minute weighs the"
             " same. The average of each procedure's own rate weighs a"
             " ten-minute procedure as much as a four-hour one, and the"
             " short ones -- which have the highest pence per minute --"
             " pull it far above the true rate, here by two thirds. The"
             " WHERE drops the NULL durations before either sum.",
        claims=[("three categories, surgery far ahead",
                 lambda rows, c: len(rows) == 3
                 and max(rows, key=lambda r: r[1])[0] == 'surgical'
                 and all(100 < r[1] < 5000 for r in rows))],
    ),
    dict(
        id=2, ledger="Q818", concept="A3", tier="1 - Warm-up",
        title="Wards above the hospital's pulse",
        prompt=(
            "Admitting wards whose observations average a higher heart"
            " rate than the hospital as a whole: ward_id, readings, and"
            " the ward's average to two decimals. The hospital average is"
            " a scalar subquery, and the comparison belongs in HAVING.\n\n"
            "Return: ward_id, readings, avg_hr"
        ),
        solution=("SELECT a.ward_id, COUNT(*), ROUND(AVG(o.heart_rate), 2)"
                  " FROM observations o JOIN admissions a ON a.admission_id = o.admission_id"
                  " GROUP BY a.ward_id HAVING AVG(o.heart_rate)"
                  " > (SELECT AVG(heart_rate) FROM observations)"),
        trap_sql=("SELECT a.ward_id, COUNT(*), ROUND(AVG(o.heart_rate), 2)"
                  " FROM observations o JOIN admissions a ON a.admission_id = o.admission_id"
                  " WHERE o.heart_rate > (SELECT AVG(heart_rate) FROM observations)"
                  " GROUP BY a.ward_id"),
        note="The subquery has no reference to the outer row, so it is"
             " evaluated once and compared against each group's average."
             " Put it in WHERE and it filters READINGS instead: every ward"
             " then averages only its above-average readings and all eight"
             " pass. The differences between wards are tiny -- a fraction"
             " of a beat -- which is why the question asks for two decimals.",
        claims=[("five wards, all a shade over the mean",
                 lambda rows, c: len(rows) == 5
                 and all(85.8 < r[2] < 86.5 for r in rows))],
    ),
    # ======================================== 2 Strings and sequences
    dict(
        id=3, ledger="Q819", concept="STR", tier="2 - Strings and sequences",
        title="The commonest forenames",
        prompt=(
            "Forenames shared by 80 or more patients, with the count. The"
            " forename is everything BEFORE the single space in the"
            " name.\n\n"
            "Return: forename, patients"
        ),
        solution=("SELECT substr(name, 1, instr(name, ' ') - 1), COUNT(*) FROM patients"
                  " GROUP BY 1 HAVING COUNT(*) >= 80"),
        trap_sql=("SELECT substr(name, 1, instr(name, ' ')), COUNT(*) FROM patients"
                  " GROUP BY 1 HAVING COUNT(*) >= 80"),
        note="substr(name, 1, n) takes n characters from the start, and"
             " the forename is one SHORTER than the position of the space"
             " -- so instr(name, ' ') - 1. Without the - 1 the space comes"
             " along: 'Cerys ' with a trailing blank, which groups fine and"
             " returns the wrong string. Mirror image of the surname"
             " question, where it was + 1.",
        claims=[("nine forenames, Cerys the commonest",
                 lambda rows, c: len(rows) == 9
                 and max(rows, key=lambda r: r[1])[0] == 'Cerys'
                 and all(r[0] == r[0].strip() for r in rows))],
    ),
    dict(
        id=4, ledger="Q820", concept="SEQ", tier="2 - Strings and sequences",
        title="Readings on the rise",
        prompt=(
            "For admissions 1 to 10: how many observations each has, how"
            " many of them recorded a heart rate HIGHER than the previous"
            " observation of the same admission, and the percentage to one"
            " decimal. The first reading has no previous and is not a"
            " rise.\n\n"
            "Return: admission_id, readings, rises, pct_rising"
        ),
        solution=("SELECT admission_id, COUNT(*), SUM(heart_rate > prev),"
                  " ROUND(100.0 * SUM(heart_rate > prev) / COUNT(*), 1) FROM (SELECT"
                  " admission_id, heart_rate, LAG(heart_rate) OVER (PARTITION BY admission_id"
                  " ORDER BY taken_at) prev FROM observations WHERE admission_id <= 10)"
                  " GROUP BY admission_id"),
        trap_sql=("SELECT admission_id, COUNT(*), SUM(heart_rate > prev),"
                  " ROUND(100.0 * SUM(heart_rate > prev) / COUNT(*), 1) FROM (SELECT"
                  " admission_id, heart_rate, LAG(heart_rate) OVER (ORDER BY admission_id,"
                  " taken_at) prev FROM observations WHERE admission_id <= 10)"
                  " GROUP BY admission_id"),
        note="LAG brings the previous row's value onto this row, and the"
             " comparison heart_rate > prev is then a plain column test"
             " that SUM can count. The partition makes 'previous' mean"
             " previous for THIS admission; without it the first reading"
             " of admission 2 is compared with the last of admission 1."
             " heart_rate > NULL is NULL, so the first reading counts as"
             " nothing, which is what the question says.",
        claims=[("ten admissions, rises never more than the readings",
                 lambda rows, c: len(rows) == 10
                 and all(0 <= r[2] < r[1] and 0 <= r[3] <= 100 for r in rows)
                 and sum(r[2] for r in rows) > 20)],
    ),
    # ============================================== 3 Dates and times
    dict(
        id=5, ledger="Q821", concept="D2", tier="3 - Dates and times",
        title="Arrived at the weekend",
        prompt=(
            "For each route of admission: how many admissions, how many"
            " arrived on a Saturday or a Sunday, and the percentage to one"
            " decimal. strftime('%w') is the weekday as text, '0' for"
            " Sunday to '6' for Saturday.\n\n"
            "Return: admitted_via, admissions, weekend, pct"
        ),
        solution=("SELECT admitted_via, COUNT(*), SUM(strftime('%w', admitted_at) IN ('0', '6')),"
                  " ROUND(100.0 * SUM(strftime('%w', admitted_at) IN ('0', '6')) / COUNT(*), 1)"
                  " FROM admissions GROUP BY admitted_via"),
        trap_sql=("SELECT admitted_via, COUNT(*), SUM(strftime('%w', admitted_at) IN ('6', '7')),"
                  " ROUND(100.0 * SUM(strftime('%w', admitted_at) IN ('6', '7')) / COUNT(*), 1)"
                  " FROM admissions GROUP BY admitted_via"),
        note="Sunday is '0' in %w, not '7' -- the week starts there, as it"
             " does in C. '7' never occurs, so the trap counts Saturdays"
             " only and the weekend share halves. The values are text,"
             " so the IN list is of strings; IN (0, 6) would also work"
             " because SQLite compares the text to the numbers by"
             " converting, but it is a habit worth not relying on.",
        claims=[("three routes, between a quarter and a third at the weekend",
                 lambda rows, c: len(rows) == 3
                 and all(25 < r[3] < 33 for r in rows))],
    ),
    dict(
        id=6, ledger="Q822", concept="D1", tier="3 - Dates and times",
        title="Days and hours, separately",
        prompt=(
            "For admissions 1 to 5, the length of stay as whole days and"
            " the hours left over, to one decimal -- 3 days and 20.8"
            " hours, not 3.9 days. The julianday difference is a number of"
            " days with a fraction; CAST it to INTEGER for the days and"
            " use the fraction for the hours.\n\n"
            "Return: admission_id, days, hours"
        ),
        solution=("SELECT admission_id, CAST(d AS INTEGER), ROUND((d - CAST(d AS INTEGER)) * 24, 1)"
                  " FROM (SELECT admission_id, julianday(discharged_at) - julianday(admitted_at) d"
                  " FROM admissions WHERE admission_id <= 5)"),
        trap_sql=("SELECT admission_id, ROUND(d), ROUND((d - ROUND(d)) * 24, 1)"
                  " FROM (SELECT admission_id, julianday(discharged_at) - julianday(admitted_at) d"
                  " FROM admissions WHERE admission_id <= 5)"),
        note="CAST(x AS INTEGER) truncates towards zero, which for a"
             " positive length is the whole days; ROUND(x) rounds to the"
             " nearest, so 3.87 days becomes 4 and the hours left over go"
             " negative. The subquery names the difference once so the"
             " outer query can use it three times. Days and hours this"
             " way is what strftime cannot do with a difference.",
        claims=[("five rows, hours always between 0 and 24",
                 lambda rows, c: len(rows) == 5
                 and all(0 <= r[2] < 24 and r[1] >= 0 for r in rows))],
    ),
    # ==================================== 4 Intervals and occupancy
    dict(
        id=7, ledger="Q823", concept="INT", tier="4 - Intervals and occupancy",
        title="Theatre 3 standing empty",
        prompt=(
            "In theatre 3, from June 2026 on, the gaps of more than 24"
            " hours between one procedure ENDING and the next BEGINNING,"
            " over procedures with a recorded duration: when the previous"
            " one ended, when the next began, and the gap in hours to one"
            " decimal. A procedure ends at datetime(performed_at, '+' ||"
            " duration_minutes || ' minutes').\n\n"
            "Return: previous_end, next_start, gap_hours"
        ),
        solution=("SELECT prev_end, performed_at, ROUND(24 * (julianday(performed_at)"
                  " - julianday(prev_end)), 1) FROM (SELECT performed_at,"
                  " LAG(datetime(performed_at, '+' || duration_minutes || ' minutes'))"
                  " OVER (ORDER BY performed_at) prev_end FROM procedures WHERE theatre = 3"
                  " AND duration_minutes IS NOT NULL AND performed_at >= '2026-06-01')"
                  " WHERE julianday(performed_at) - julianday(prev_end) > 1"),
        trap_sql=("SELECT prev_start, performed_at, ROUND(24 * (julianday(performed_at)"
                  " - julianday(prev_start)), 1) FROM (SELECT performed_at,"
                  " LAG(performed_at) OVER (ORDER BY performed_at) prev_start"
                  " FROM procedures WHERE theatre = 3 AND duration_minutes IS NOT NULL"
                  " AND performed_at >= '2026-06-01')"
                  " WHERE julianday(performed_at) - julianday(prev_start) > 1"),
        note="LAG can carry a computed value, here the previous"
             " procedure's END, built with datetime() and a modifier from"
             " the column. Measuring from the previous START overstates"
             " every gap by that procedure's length and lets a gap of"
             " twenty-two hours after a three-hour operation pass as"
             " twenty-five. The filter on the gap sits outside the"
             " subquery because the window has to run first.",
        claims=[("about a dozen gaps, the longest under three days",
                 lambda rows, c: 5 < len(rows) < 20
                 and all(24 < r[2] < 72 for r in rows))],
    ),
    dict(
        id=8, ledger="Q824", concept="INT", tier="4 - Intervals and occupancy",
        title="Two in the morning and two in the afternoon",
        prompt=(
            "For each ward, how many patients were on it at 02:00 and how"
            " many at 14:00 on 2026-06-30, as two columns from one query:"
            " a stay covers an instant if it began at or before it and had"
            " not ended, and an open stay has not ended.\n\n"
            "Return: ward_id, at_0200, at_1400"
        ),
        solution=("SELECT ward_id, SUM(from_at <= '2026-06-30 02:00'"
                  " AND COALESCE(to_at, '9999') > '2026-06-30 02:00'),"
                  " SUM(from_at <= '2026-06-30 14:00'"
                  " AND COALESCE(to_at, '9999') > '2026-06-30 14:00')"
                  " FROM ward_stays GROUP BY ward_id"),
        trap_sql=("SELECT ward_id, SUM(from_at <= '2026-06-30 02:00'"
                  " AND to_at > '2026-06-30 02:00'),"
                  " SUM(from_at <= '2026-06-30 14:00'"
                  " AND to_at > '2026-06-30 14:00')"
                  " FROM ward_stays GROUP BY ward_id"),
        note="Two instants in one pass: each is a conditional SUM over"
             " the same interval test. On the last day of the data most"
             " of the patients present are still in, with a NULL to_at,"
             " and NULL > anything is NULL -- the trap counts almost"
             " nobody. COALESCE to a far-future string is the fix, as in"
             " every open-interval question before.",
        claims=[("eight wards, a few patients at each instant",
                 lambda rows, c: len(rows) == 8
                 and all(0 < r[1] < 20 and 0 < r[2] < 20 for r in rows))],
    ),
    # ============================================== 5 Joins and grain
    dict(
        id=9, ledger="Q825", concept="J1", tier="5 - Joins and grain",
        title="Two theatres in one day",
        prompt=(
            "For each surgeon, on how many DAYS they operated in two or"
            " more different theatres. Pair each procedure with another by"
            " the same surgeon on the same date in a different theatre,"
            " then count the distinct dates.\n\n"
            "Return: surgeon_id, split_days"
        ),
        solution=("SELECT a.surgeon_id, COUNT(DISTINCT date(a.performed_at)) FROM procedures a"
                  " JOIN procedures b ON b.surgeon_id = a.surgeon_id"
                  " AND date(b.performed_at) = date(a.performed_at) AND b.theatre <> a.theatre"
                  " GROUP BY a.surgeon_id"),
        trap_sql=("SELECT a.surgeon_id, COUNT(*) FROM procedures a"
                  " JOIN procedures b ON b.surgeon_id = a.surgeon_id"
                  " AND date(b.performed_at) = date(a.performed_at) AND b.theatre <> a.theatre"
                  " GROUP BY a.surgeon_id"),
        note="A self-join on the same person and the same day, with an"
             " inequality on the theatre to keep only pairs that differ."
             " The join produces a row per PAIR, in both orders, and more"
             " when three procedures share a day -- COUNT(*) counts those"
             " pairs. The question asks for days, so COUNT(DISTINCT date)"
             " collapses the pairs back to one per day.",
        claims=[("every surgeon, a few dozen days each",
                 lambda rows, c: len(rows) == 26
                 and all(5 < r[1] < 60 for r in rows))],
    ),
    dict(
        id=10, ledger="Q826", concept="J2", tier="5 - Joins and grain",
        title="Theatre 6's tally, every type",
        prompt=(
            "Every procedure type with how many times it has been"
            " performed in theatre 6 -- all thirty types, with 0 for the"
            " ones never done there. The theatre condition has to live in"
            " the join's ON clause, not the WHERE.\n\n"
            "Return: code, in_theatre_6"
        ),
        solution=("SELECT t.code, COUNT(p.procedure_id) FROM procedure_types t"
                  " LEFT JOIN procedures p ON p.code = t.code AND p.theatre = 6"
                  " GROUP BY t.code"),
        trap_sql=("SELECT t.code, COUNT(p.procedure_id) FROM procedure_types t"
                  " LEFT JOIN procedures p ON p.code = t.code WHERE p.theatre = 6"
                  " GROUP BY t.code"),
        note="In a LEFT JOIN, a condition in ON decides which right-hand"
             " rows match; a condition in WHERE decides which joined rows"
             " survive. p.theatre = 6 in WHERE is false for the NULL rows"
             " that the LEFT JOIN made for unmatched types, so they vanish"
             " and the join is an inner one again -- 27 rows, not 30."
             " COUNT(p.procedure_id) counts matches and gives 0 for a"
             " type with none; COUNT(*) would give 1.",
        claims=[("thirty types, three with a zero",
                 lambda rows, c: len(rows) == 30
                 and sum(r[1] == 0 for r in rows) == 3)],
    ),
    # ============================================== 6 Window functions
    dict(
        id=11, ledger="Q827", concept="W1", tier="6 - Window functions",
        title="The reading before and the reading after",
        prompt=(
            "For admission 9, every observation in time order with the"
            " heart rate, the heart rate of the PREVIOUS observation and"
            " of the NEXT one -- NULL where there is none. LAG and LEAD"
            " over the same ordering.\n\n"
            "Return: taken_at, heart_rate, previous_hr, next_hr"
        ),
        solution=("SELECT taken_at, heart_rate, LAG(heart_rate) OVER (ORDER BY taken_at),"
                  " LEAD(heart_rate) OVER (ORDER BY taken_at) FROM observations"
                  " WHERE admission_id = 9"),
        trap_sql=("SELECT taken_at, heart_rate, LEAD(heart_rate) OVER (ORDER BY taken_at),"
                  " LAG(heart_rate) OVER (ORDER BY taken_at) FROM observations"
                  " WHERE admission_id = 9"),
        note="LAG looks back, LEAD looks forward, both along the ORDER BY"
             " of the window, and both return NULL where there is no such"
             " row. Swapping them is the whole trap: every row's columns"
             " are the right numbers in the wrong places. With a named"
             " WINDOW w AS (ORDER BY taken_at) the two share one"
             " definition and the query reads LAG(...) OVER w.",
        claims=[("twenty-five readings, one NULL at each end",
                 lambda rows, c: len(rows) == 25
                 and sum(r[2] is None for r in rows) == 1
                 and sum(r[3] is None for r in rows) == 1)],
    ),
    dict(
        id=12, ledger="Q828", concept="DST", tier="6 - Window functions",
        title="Where a stay sits on its ward",
        prompt=(
            "For admissions 1 to 10 that are completed: the length of"
            " stay to two decimals, and its CUME_DIST within the admitting"
            " ward's completed admissions ordered by length -- the share"
            " of that ward's stays that are this long or shorter, to two"
            " decimals.\n\n"
            "Return: admission_id, ward_id, days, cume_dist"
        ),
        solution=("SELECT admission_id, ward_id, ROUND(los, 2), ROUND(cd, 2) FROM (SELECT"
                  " admission_id, ward_id, los, CUME_DIST() OVER (PARTITION BY ward_id"
                  " ORDER BY los) cd FROM (SELECT admission_id, ward_id,"
                  " julianday(discharged_at) - julianday(admitted_at) los FROM admissions"
                  " WHERE discharged_at IS NOT NULL)) WHERE admission_id <= 10"),
        trap_sql=("SELECT admission_id, ward_id, ROUND(los, 2), ROUND(cd, 2) FROM (SELECT"
                  " admission_id, ward_id, los, CUME_DIST() OVER ("
                  " ORDER BY los) cd FROM (SELECT admission_id, ward_id,"
                  " julianday(discharged_at) - julianday(admitted_at) los FROM admissions"
                  " WHERE discharged_at IS NOT NULL)) WHERE admission_id <= 10"),
        note="CUME_DIST is the fraction of the partition at or below this"
             " row, so the longest stay on a ward scores 1.0 and the"
             " shortest 1 / n. 'Within the ward' is the PARTITION BY;"
             " without it the share is of the whole hospital's stays, a"
             " different distribution. The window runs over EVERY"
             " completed admission of the ward, which is why the filter"
             " to admissions 1 to 10 sits outside it. PERCENT_RANK is the"
             " close cousin that scores the shortest stay 0.",
        claims=[("ten rows, every cume_dist between 0 and 1 and never 0",
                 lambda rows, c: len(rows) == 10
                 and all(0 < r[3] <= 1 for r in rows))],
    ),
    # ============================================= 7 Changing the data
    dict(
        id=13, ledger="Q829", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="A ranking you can query",
        prompt=(
            "Create a view `june_ranking (ward_id, admissions, rank)` over"
            " admissions in June 2026, with RANK() by admissions, 1 for"
            " the most -- so that two wards with the same count share a"
            " rank. A window function works inside a view like anywhere"
            " else.\n\n"
            "Checked: the view's rows"
        ),
        solution=("CREATE VIEW june_ranking AS\n"
                  "  SELECT ward_id, COUNT(*) AS admissions,\n"
                  "         RANK() OVER (ORDER BY COUNT(*) DESC) AS rank\n"
                  "  FROM admissions\n"
                  "  WHERE admitted_at >= '2026-06-01' AND admitted_at < '2026-07-01'\n"
                  "  GROUP BY ward_id;"),
        trap_sql=("CREATE VIEW june_ranking AS\n"
                  "  SELECT ward_id, COUNT(*) AS admissions,\n"
                  "         ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rank\n"
                  "  FROM admissions\n"
                  "  WHERE admitted_at >= '2026-06-01' AND admitted_at < '2026-07-01'\n"
                  "  GROUP BY ward_id;"),
        probe_sql="SELECT ward_id, admissions, rank FROM june_ranking",
        note="A view is a saved SELECT, and anything a SELECT can do --"
             " GROUP BY, a window over the grouped rows -- it can hold."
             " Querying the view re-runs it, so the ranking is always"
             " current. RANK gives equal counts an equal place and skips"
             " the next; ROW_NUMBER breaks the tie by whichever row came"
             " first, which here is arbitrary -- two wards with 37"
             " admissions must both rank third.",
        claims=[("eight wards, two sharing a rank",
                 lambda rows, c: len(rows) == 8
                 and len({r[2] for r in rows}) == 7)],
    ),
    dict(
        id=14, ledger="Q830", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="A code with a shape",
        prompt=(
            "Create `gp_practices (code TEXT PRIMARY KEY, name TEXT NOT"
            " NULL)` where code must be a capital G followed by exactly"
            " five digits -- a CHECK using GLOB, whose [0-9] matches one"
            " digit and which is case-sensitive. After your script, the"
            " question inserts 'G12345', 'g12345', 'G1234' and"
            " 'G123456'.\n\n"
            "Checked: the codes that were accepted"
        ),
        solution=("CREATE TABLE gp_practices (\n"
                  "  code TEXT PRIMARY KEY CHECK (code GLOB 'G[0-9][0-9][0-9][0-9][0-9]'),\n"
                  "  name TEXT NOT NULL\n"
                  ");"),
        trap_sql=("CREATE TABLE gp_practices (\n"
                  "  code TEXT PRIMARY KEY CHECK (code LIKE 'G_____'),\n"
                  "  name TEXT NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO gp_practices VALUES ('G12345', 'Hyde Park');\n"
                    "INSERT INTO gp_practices VALUES ('g12345', 'lower case');\n"
                    "INSERT INTO gp_practices VALUES ('G1234', 'too short');\n"
                    "INSERT INTO gp_practices VALUES ('G123456', 'too long');"),
        probe_sql="SELECT code FROM gp_practices ORDER BY code",
        note="GLOB is the shell's pattern language: * any run, ? one"
             " character, [0-9] one character from a set, and it is"
             " case-sensitive. LIKE has only % and _ and ignores case for"
             " ASCII, so 'G_____' accepts 'g12345' and would accept"
             " 'Gabcde'. A CHECK with GLOB is how a table enforces a format"
             " without a trigger.",
        claims=[("only the well-formed code lands",
                 lambda rows, c: rows == [('G12345',)])],
    ),
    dict(
        id=15, ledger="Q831", concept="JSN", tier="7 - Changing the data",
        kind="script",
        title="Rows out of a JSON list",
        prompt=(
            "Create `ward_tags (tag_id INTEGER PRIMARY KEY, tag TEXT NOT"
            " NULL)` and fill it from the JSON list"
            " '[\"isolation\", \"bariatric\", \"paediatric\", \"step-down\"]'"
            " -- one row per element, in order -- with INSERT ... SELECT"
            " over json_each(), whose `value` column is each element.\n\n"
            "Checked: the tags, in tag_id order, and how many there are"
        ),
        solution=("CREATE TABLE ward_tags (\n"
                  "  tag_id INTEGER PRIMARY KEY,\n"
                  "  tag    TEXT NOT NULL\n"
                  ");\n"
                  "INSERT INTO ward_tags (tag)\n"
                  "SELECT value FROM json_each('[\"isolation\", \"bariatric\","
                  " \"paediatric\", \"step-down\"]');"),
        trap_sql=("CREATE TABLE ward_tags (\n"
                  "  tag_id INTEGER PRIMARY KEY,\n"
                  "  tag    TEXT NOT NULL\n"
                  ");\n"
                  "INSERT INTO ward_tags (tag)\n"
                  "VALUES ('[\"isolation\", \"bariatric\", \"paediatric\", \"step-down\"]');"),
        probe_sql=("SELECT (SELECT group_concat(tag, '|') FROM (SELECT tag FROM ward_tags"
                   " ORDER BY tag_id)), (SELECT COUNT(*) FROM ward_tags)"),
        note="json_each() is a table-valued function: it turns a JSON array"
             " into rows, one per element, with `value` holding the element"
             " and `key` its position. INSERT ... SELECT then loads them"
             " like any query result. Inserting the JSON text itself puts"
             " the whole list in one row as a string -- a list that still"
             " has to be parsed every time it is read.",
        claims=[("four tags in list order",
                 lambda rows, c: rows == [('isolation|bariatric|paediatric|step-down', 4)])],
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
