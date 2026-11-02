"""Practice exercises: fifteen questions on the bike-hire schema.

The sixth set on the bike scheme (SEED 1206), two tools per question, the
tiers named by task, on tools no bike set has used. Shares and bands --
each zone's share of all rides by SUM(COUNT(*)) OVER (), rides in
kilometre bands by integer division as a GROUP BY key, the average PAID
fare by AVG over NULLIF. Rows that don't line up -- rides taken while a
job was open by a BETWEEN join, the second page of members by LIMIT and
OFFSET, stations above the average station by HAVING against a nested
aggregate. Scalar tools -- the days a bike was available inside the data
period by the two-argument MAX and MIN, words and letters in a name by
LENGTH and REPLACE, first names beginning with a vowel by GLOB's
character class. Across the calendar -- the first half of 2026 against
2025 by conditional sums, rebalancing moves by LAG of the previous END
station, members who joined at the weekend by strftime('%w'). And three
WRITABLE questions:

  * a partial UNIQUE INDEX that refuses a second payment for a ride
  * an UPDATE whose SET uses a CASE on another column
  * a SAVEPOINT that undoes one statement and keeps the one before it

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script.
"""

import sqlite3

EXERCISES = [
    # ==================================================== 1 Shares and bands
    dict(
        id=1, ledger="Q1147", concept="TOT", tier="1 - Shares and bands",
        title="Each zone's share of the rides",
        prompt=(
            "For each zone, of the start station: its rides, and its"
            " share of ALL rides as a percentage to one decimal. The"
            " grand total comes from a window over the grouped rows --"
            " SUM(COUNT(*)) OVER () -- so one query does both, and 100.0"
            " keeps the division real.\n\n"
            "Return: zone, rides, share"
        ),
        solution=("SELECT s.zone, COUNT(*), ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.zone"),
        trap_sql=("SELECT s.zone, COUNT(*), 100 * COUNT(*) / SUM(COUNT(*)) OVER ()"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.zone"),
        note="A window function runs AFTER the GROUP BY, over the grouped"
             " rows, so SUM(COUNT(*)) OVER () is the total of the five"
             " zone counts -- every ride -- on every row, with no second"
             " query. With an empty OVER () the window is the whole"
             " result. Both counts are integers, so 100 * a / b is"
             " integer division: the trap says 26 where the answer is"
             " 26.8, and the five shares add up to 97.",
        claims=[("five zones, the centre's share 26.8",
                 lambda rows, c: len(rows) == 5 and ("centre", 10361, 26.8) in rows),
                ("the shares add up to a hundred, near enough",
                 lambda rows, c: abs(sum(r[2] for r in rows) - 100) < 0.3)],
    ),
    dict(
        id=2, ledger="Q1148", concept="BKT", tier="1 - Shares and bands",
        title="Rides in kilometre bands",
        prompt=(
            "For the finished rides under ten kilometres: how many fall"
            " in each whole-kilometre band, and the band's average fare"
            " in dollars to two decimals. The band is the integer"
            " division distance_m / 1000 -- 0 for under a kilometre, 1"
            " for one to two -- used as the GROUP BY key; for once the"
            " truncation is the point.\n\n"
            "Return: km_band, rides, avg_fare"
        ),
        solution=("SELECT distance_m / 1000, COUNT(*), ROUND(AVG(fare_cents) / 100.0, 2)"
                  " FROM rides WHERE distance_m < 10000 GROUP BY distance_m / 1000"),
        trap_sql=("SELECT distance_m / 1000.0, COUNT(*), ROUND(AVG(fare_cents) / 100.0, 2)"
                  " FROM rides WHERE distance_m < 10000 GROUP BY distance_m / 1000.0"),
        note="Integer division throws the fraction away, and that is"
             " what turns 2,322 metres into band 2: the same operation"
             " that spoiled an average last set builds a histogram here."
             " Divide by 1000.0 and every distinct distance is its own"
             " group -- the trap returns 8,513 rows. WHERE distance_m <"
             " 10000 also drops the rides still out, whose distance is"
             " NULL. The fare climbs about 20 cents a kilometre.",
        claims=[("ten bands, band 1 the fullest",
                 lambda rows, c: len(rows) == 10 and max(rows, key=lambda r: r[1])[0] == 1),
                ("the fare rises with every band",
                 lambda rows, c: [r[2] for r in sorted(rows)] == sorted(r[2] for r in rows))],
    ),
    dict(
        id=3, ledger="Q1149", concept="NUL", tier="1 - Shares and bands",
        title="What a ride costs when it costs anything",
        prompt=(
            "For each plan: the average fare of its members' rides in"
            " dollars to two decimals, and the average of the rides that"
            " were CHARGED -- the free ones left out of the average"
            " rather than counted as zero. AVG(NULLIF(fare_cents, 0))"
            " turns a 0 into NULL, and AVG skips NULLs.\n\n"
            "Return: plan, avg_fare, avg_paid"
        ),
        solution=("SELECT m.plan, ROUND(AVG(r.fare_cents) / 100.0, 2), ROUND(AVG(NULLIF(r.fare_cents, 0)) / 100.0, 2)"
                  " FROM rides r JOIN members m ON m.member_id = r.member_id GROUP BY m.plan"),
        trap_sql=("SELECT m.plan, ROUND(AVG(r.fare_cents) / 100.0, 2), ROUND(AVG(r.fare_cents) / 100.0, 2)"
                  " FROM rides r JOIN members m ON m.member_id = r.member_id GROUP BY m.plan"),
        note="NULLIF(a, b) is NULL when a equals b and a otherwise, and"
             " since every aggregate but COUNT(*) ignores NULL, it is"
             " the way to leave a value out of an average without a"
             " WHERE that would also shrink the other columns. The"
             " subscribers' average fare is fifty cents because three"
             " quarters of their rides are free; the rides they do pay"
             " for cost two dollars, close to what pay-as-you-go riders"
             " pay for every ride.",
        claims=[("three plans, the annual average paid fare 2.02",
                 lambda rows, c: len(rows) == 3 and ("annual", 0.51, 2.02) in rows),
                ("paid is never below overall",
                 lambda rows, c: all(r[2] >= r[1] for r in rows))],
    ),
    # ============================================ 2 Rows that don't line up
    dict(
        id=4, ledger="Q1150", concept="NEQ", tier="2 - Rows that don't line up",
        title="Rides taken while the bike was in the shop",
        prompt=(
            "For each kind of job: how many rides started on the bike"
            " between the job being reported and being fixed. A join"
            " that is not on equal keys: rides to maintenance ON the"
            " same bike_id AND started_at BETWEEN reported_at AND"
            " fixed_at, counting the fixed jobs only.\n\n"
            "Return: kind, rides_during"
        ),
        solution=("SELECT m.kind, COUNT(*) FROM maintenance m"
                  " JOIN rides r ON r.bike_id = m.bike_id AND r.started_at BETWEEN m.reported_at AND m.fixed_at"
                  " WHERE m.fixed_at IS NOT NULL GROUP BY m.kind"),
        trap_sql=("SELECT m.kind, COUNT(*) FROM maintenance m"
                  " JOIN rides r ON r.bike_id = m.bike_id AND r.started_at >= m.reported_at"
                  " WHERE m.fixed_at IS NOT NULL GROUP BY m.kind"),
        note="A join condition can be any expression, and BETWEEN on"
             " the ride's start against the job's two timestamps pairs"
             " each ride with the jobs that were open when it began."
             " The trap keeps only the lower bound and pairs every ride"
             " with every earlier job on its bike: 24,000 punctures"
             " instead of 446. About a thousand rides went out on a bike"
             " that was supposedly off the road, roughly one per job.",
        claims=[("five kinds, 446 rides during a puncture job",
                 lambda rows, c: len(rows) == 5 and ("puncture", 446) in rows),
                ("about one ride per fixed job",
                 lambda rows, c: 900 < sum(r[1] for r in rows) < 1200)],
    ),
    dict(
        id=5, ledger="Q1151", concept="PAG", tier="2 - Rows that don't line up",
        title="The second page of members",
        prompt=(
            "The members in order of joining, ten to a page: page two."
            " ORDER BY joined_on, then member_id to settle the members"
            " who joined on the same day, LIMIT 10 OFFSET 10 -- the"
            " offset skips page one.\n\n"
            "Return: member_id, name, joined_on"
        ),
        solution=("SELECT member_id, name, joined_on FROM members ORDER BY joined_on, member_id LIMIT 10 OFFSET 10"),
        trap_sql=("SELECT member_id, name, joined_on FROM members ORDER BY joined_on, member_id LIMIT 10 OFFSET 11"),
        note="OFFSET counts rows to skip, so page n of size s is LIMIT s"
             " OFFSET (n - 1) * s: page two skips ten, not eleven -- the"
             " trap is one member out at each end. The tiebreak matters:"
             " three members joined on 2023-02-01, and without member_id"
             " in the ORDER BY the database may put them either way"
             " round, and a member could appear on both pages or"
             " neither.",
        claims=[("ten members, the page starting with 561",
                 lambda rows, c: len(rows) == 10 and any(r[0] == 561 for r in rows)),
                ("all joined in early 2023",
                 lambda rows, c: all(r[2] < '2023-03-01' for r in rows))],
    ),
    dict(
        id=6, ledger="Q1152", concept="HAV", tier="2 - Rows that don't line up",
        title="Stations busier than the average station",
        prompt=(
            "The stations where more rides have started than at the"
            " AVERAGE station, with their count. The average is an"
            " aggregate of an aggregate: a subquery counting rides per"
            " start station, AVG of those counts, compared with in"
            " HAVING.\n\n"
            "Return: name, starts"
        ),
        solution=("SELECT s.name, COUNT(*) FROM rides r JOIN stations s ON s.station_id = r.start_station_id"
                  " GROUP BY s.name HAVING COUNT(*) >"
                  " (SELECT AVG(n) FROM (SELECT COUNT(*) AS n FROM rides GROUP BY start_station_id))"),
        trap_sql=("SELECT s.name, COUNT(*) FROM rides r JOIN stations s ON s.station_id = r.start_station_id"
                  " GROUP BY s.name HAVING COUNT(*) >"
                  " (SELECT COUNT(*) FROM rides) / (SELECT COUNT(*) FROM stations WHERE closed_on IS NULL)"),
        note="HAVING can compare a group's aggregate with a scalar"
             " subquery, and the subquery can itself be an aggregate of"
             " grouped rows -- the average of the per-station counts,"
             " 3,217. The trap divides all rides by the eleven OPEN"
             " stations, but Old Mill's 2,500 rides are in the total too,"
             " so the bar is set at 3,509 and only Market Square clears"
             " it. Five stations are above average; the closed one is"
             " well below.",
        claims=[("five stations, Market Square among them",
                 lambda rows, c: len(rows) == 5 and any(r[0] == "Market Square" for r in rows)),
                ("every count above 3217",
                 lambda rows, c: all(r[1] > 3217 for r in rows))],
    ),
    # ======================================================== 3 Scalar tools
    dict(
        id=7, ledger="Q1153", concept="SCL", tier="3 - Scalar tools",
        title="Days each bike was there to be ridden",
        prompt=(
            "For each model: its bikes, and the average number of days"
            " they were available INSIDE the data period, 2025-01-01 to"
            " 2026-06-30. The two-argument MAX and MIN pick the later of"
            " two values and the earlier: MAX(acquired_on, '2025-01-01')"
            " is when the bike entered the period, MIN(COALESCE("
            "retired_on, '2026-06-30'), '2026-06-30') when it left;"
            " julianday of each, subtracted, averaged, to one decimal.\n\n"
            "Return: model, bikes, avg_days"
        ),
        solution=("SELECT model, COUNT(*), ROUND(AVG(julianday(MIN(COALESCE(retired_on, '2026-06-30'), '2026-06-30'))"
                  " - julianday(MAX(acquired_on, '2025-01-01'))), 1) FROM bikes GROUP BY model"),
        trap_sql=("SELECT model, COUNT(*), ROUND(AVG(julianday(COALESCE(retired_on, '2026-06-30'))"
                  " - julianday(acquired_on)), 1) FROM bikes GROUP BY model"),
        note="MAX(a, b) with two arguments is a scalar function, a"
             " different thing from the aggregate MAX(column): it"
             " compares the values in one row, and it is how a date is"
             " clamped to a range. 296 of the 320 bikes were acquired"
             " before the rides begin, so without the clamp the trap"
             " counts years of service that the data cannot see and"
             " doubles every average. Each model was available for about"
             " 520 of the period's 546 days.",
        claims=[("three models, each available 500 to 540 days",
                 lambda rows, c: len(rows) == 3 and all(500 <= r[2] <= 540 for r in rows)),
                ("320 bikes in all",
                 lambda rows, c: sum(r[1] for r in rows) == 320)],
    ),
    dict(
        id=8, ledger="Q1154", concept="WRD", tier="3 - Scalar tools",
        title="Words and letters in a station's name",
        prompt=(
            "For every station: how many words its name has, and how"
            " many letters. Words are spaces plus one -- LENGTH(name)"
            " minus LENGTH(REPLACE(name, ' ', '')) counts the spaces --"
            " and the letters are the length with the spaces taken out."
            "\n\n"
            "Return: name, words, letters"
        ),
        solution=("SELECT name, LENGTH(name) - LENGTH(REPLACE(name, ' ', '')) + 1, LENGTH(REPLACE(name, ' ', '')) FROM stations"),
        trap_sql=("SELECT name, LENGTH(name) - LENGTH(REPLACE(name, ' ', '')) + 1, LENGTH(name) FROM stations"),
        note="SQLite has no function that counts occurrences, but"
             " REPLACE removes them all and LENGTH measures what is"
             " left: the difference is the count, a trick that works for"
             " any single character. LENGTH(name) alone counts the"
             " spaces as letters, so the trap is one too many on every"
             " two-word name. Five stations have two words, and Station"
             " Approach is the longest name at fifteen letters.",
        claims=[("twelve stations, five of two words",
                 lambda rows, c: len(rows) == 12 and sum(r[1] == 2 for r in rows) == 5),
                ("Station Approach the longest at 15 letters",
                 lambda rows, c: ("Station Approach", 2, 15) in rows)],
    ),
    dict(
        id=9, ledger="Q1155", concept="GLB", tier="3 - Scalar tools",
        title="First names that start with a vowel",
        prompt=(
            "For each plan: its members, and how many of them have a"
            " first name starting with a vowel. GLOB takes a character"
            " class -- name GLOB '[AEIOU]*' -- where LIKE has only _ and"
            " %; SUM of the condition counts the matches.\n\n"
            "Return: plan, members, vowel_names"
        ),
        solution=("SELECT plan, COUNT(*), SUM(name GLOB '[AEIOU]*') FROM members GROUP BY plan"),
        trap_sql=("SELECT plan, COUNT(*), SUM(name LIKE '[AEIOU]%') FROM members GROUP BY plan"),
        note="LIKE knows two wildcards, _ and %, and is case-insensitive"
             " for ASCII; GLOB uses Unix patterns -- ? and * and [...]"
             " classes -- and is case-sensitive, which is why [AEIOU]"
             " needs the capitals. In a LIKE pattern, [AEIOU] is five"
             " literal characters inside square brackets, which no name"
             " contains, so the trap counts nobody. About a fifth of"
             " the members have a vowel-first name on every plan.",
        claims=[("three plans, 70 annual members with a vowel name",
                 lambda rows, c: len(rows) == 3 and ("annual", 324, 70) in rows),
                ("between 15 and 25 per cent on every plan",
                 lambda rows, c: all(0.15 <= r[2] / r[1] <= 0.25 for r in rows))],
    ),
    # ================================================= 4 Across the calendar
    dict(
        id=10, ledger="Q1156", concept="YOY", tier="4 - Across the calendar",
        title="This year against last, month by month",
        prompt=(
            "For each month of the first half of the year, January to"
            " June: the rides in 2025, the rides in 2026, and the change"
            " as a percentage of 2025 to one decimal. One GROUP BY on"
            " strftime('%m') with two conditional sums -- SUM(strftime("
            "'%Y', started_at) = '2025') and the same for 2026 -- and a"
            " WHERE that keeps the months the two years share.\n\n"
            "Return: month, y2025, y2026, change_pct"
        ),
        solution=("SELECT strftime('%m', started_at), SUM(strftime('%Y', started_at) = '2025'), SUM(strftime('%Y', started_at) = '2026'),"
                  " ROUND(100.0 * (SUM(strftime('%Y', started_at) = '2026') - SUM(strftime('%Y', started_at) = '2025'))"
                  " / SUM(strftime('%Y', started_at) = '2025'), 1)"
                  " FROM rides WHERE strftime('%m', started_at) <= '06' GROUP BY strftime('%m', started_at)"),
        trap_sql=("SELECT strftime('%m', started_at), SUM(strftime('%Y', started_at) = '2025'), SUM(strftime('%Y', started_at) = '2026'),"
                  " ROUND(100.0 * (SUM(strftime('%Y', started_at) = '2026') - SUM(strftime('%Y', started_at) = '2025'))"
                  " / SUM(strftime('%Y', started_at) = '2025'), 1)"
                  " FROM rides GROUP BY strftime('%m', started_at)"),
        note="Grouping on the month alone lines the two years up as"
             " columns, and a SUM of a comparison counts the rows that"
             " satisfy it -- a pivot in miniature. The data stops at the"
             " end of June 2026, so July to December would show a 100"
             " per cent fall that is not real: the trap reports twelve"
             " months, six of them collapsing. January grew by an eighth;"
             " the other five months are flat or down.",
        claims=[("six months, January up 12.4 per cent",
                 lambda rows, c: len(rows) == 6 and ("01", 1943, 2184, 12.4) in rows),
                ("every month of 2025 had over 1900 rides",
                 lambda rows, c: all(r[1] > 1900 for r in rows))],
    ),
    dict(
        id=11, ledger="Q1157", concept="HOP", tier="4 - Across the calendar",
        title="How often a bike is moved between rides",
        prompt=(
            "For each model: the rides that had a previous ride on the"
            " same bike, how many of them started somewhere other than"
            " where that previous ride ENDED -- the bike was moved by"
            " the crew in between -- and that as a percentage to one"
            " decimal. LAG(end_station_id) OVER (PARTITION BY bike_id"
            " ORDER BY started_at) in a CTE, compared with"
            " start_station_id.\n\n"
            "Return: model, rides, moved, moved_pct"
        ),
        solution=("WITH s AS (SELECT b.model, r.start_station_id,"
                  " LAG(r.end_station_id) OVER (PARTITION BY r.bike_id ORDER BY r.started_at) AS prev_end"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id)"
                  " SELECT model, COUNT(prev_end), SUM(prev_end <> start_station_id),"
                  " ROUND(100.0 * SUM(prev_end <> start_station_id) / COUNT(prev_end), 1) FROM s GROUP BY model"),
        trap_sql=("WITH s AS (SELECT b.model, r.start_station_id,"
                  " LAG(r.start_station_id) OVER (PARTITION BY r.bike_id ORDER BY r.started_at) AS prev_end"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id)"
                  " SELECT model, COUNT(prev_end), SUM(prev_end <> start_station_id),"
                  " ROUND(100.0 * SUM(prev_end <> start_station_id) / COUNT(prev_end), 1) FROM s GROUP BY model"),
        note="LAG can fetch any column of the previous row, not only the"
             " one being compared: here the previous ride's END is set"
             " against this ride's START, and a mismatch means the bike"
             " was moved. LAG of the start station asks a different"
             " question -- did it start somewhere new -- and the trap's"
             " numbers are close but wrong. Nine rides in ten begin"
             " somewhere other than where the bike was left, which says"
             " the data's rides are not chained: the crew is busy.",
        claims=[("three models, each moved about nine times in ten",
                 lambda rows, c: len(rows) == 3 and all(90 <= r[3] <= 93 for r in rows)),
                ("the classics' 24843 rides with a predecessor",
                 lambda rows, c: any(r[0] == "classic" and r[1] == 24843 for r in rows))],
    ),
    dict(
        id=12, ledger="Q1158", concept="DOW", tier="4 - Across the calendar",
        title="Members who joined at the weekend",
        prompt=(
            "For each plan: its members, how many joined on a Saturday"
            " or Sunday, and that as a percentage to one decimal."
            " strftime('%w', joined_on) is the day of the week as a"
            " digit, '0' for Sunday to '6' for Saturday; a SUM of IN"
            " ('0', '6') counts the weekend joiners.\n\n"
            "Return: plan, members, weekend, weekend_pct"
        ),
        solution=("SELECT plan, COUNT(*), SUM(strftime('%w', joined_on) IN ('0', '6')),"
                  " ROUND(100.0 * SUM(strftime('%w', joined_on) IN ('0', '6')) / COUNT(*), 1) FROM members GROUP BY plan"),
        trap_sql=("SELECT plan, COUNT(*), SUM(strftime('%w', joined_on) IN ('6', '7')),"
                  " ROUND(100.0 * SUM(strftime('%w', joined_on) IN ('6', '7')) / COUNT(*), 1) FROM members GROUP BY plan"),
        note="%w numbers the week from Sunday as 0, so there is no 7:"
             " the trap's IN ('6', '7') counts Saturdays only and halves"
             " every figure. The result is text, which is why the"
             " comparison is with '0' and '6' in quotes. Two days are"
             " two sevenths of the week, 28.6 per cent, and the plans"
             " fall within a few points of that either side.",
        claims=[("three plans, 100 annual weekend joiners",
                 lambda rows, c: len(rows) == 3 and ("annual", 324, 100, 30.9) in rows),
                ("every plan within ten points of two sevenths",
                 lambda rows, c: all(abs(r[3] - 28.6) < 10 for r in rows))],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1159", concept="UNQ", tier="5 - Changing the data",
        kind="script",
        title="One fare per ride, enforced",
        prompt=(
            "A ride must not be paid for twice. CREATE UNIQUE INDEX"
            " one_fare_per_ride ON payments(ride_id) WHERE ride_id IS"
            " NOT NULL -- a partial index, so the thousands of"
            " subscription payments with no ride are left out of it. The"
            " question then runs three inserts: a second fare for ride"
            " 12152, which the index must refuse, and two subscription"
            " payments for members 1 and 2 with no ride, which it must"
            " let through.\n\n"
            "Checked: how many payments there are, how many name a ride,"
            " and the highest payment_id"
        ),
        solution="CREATE UNIQUE INDEX one_fare_per_ride ON payments(ride_id) WHERE ride_id IS NOT NULL;",
        trap_sql="CREATE INDEX one_fare_per_ride ON payments(ride_id) WHERE ride_id IS NOT NULL;",
        driver_sql=("INSERT INTO payments (ride_id, amount_cents, paid_at, method) VALUES (12152, 300, '2026-07-01 09:00', 'card');\n"
                    "INSERT INTO payments (member_id, amount_cents, paid_at, method) VALUES (1, 9900, '2026-07-01 09:00', 'app');\n"
                    "INSERT INTO payments (member_id, amount_cents, paid_at, method) VALUES (2, 1200, '2026-07-01 09:00', 'card');"),
        probe_sql="SELECT COUNT(*), COUNT(ride_id), MAX(payment_id) FROM payments",
        note="A UNIQUE index is a constraint added after the table"
             " exists, and a WHERE on the index makes it partial: only"
             " the rows that match are indexed, so only they are held"
             " unique. Without UNIQUE the trap's index speeds up lookups"
             " and refuses nothing, and the duplicate fare gets in. The"
             " refusal is reported in the status bar, not treated as an"
             " error, because 'this row must be refused' is what the"
             " question tests.",
        claims=[("two subscriptions in, the duplicate fare refused",
                 lambda rows, c: rows == [(28533 + 2, 22732, 28533 + 2)])],
    ),
    dict(
        id=14, ledger="Q1160", concept="UPC", tier="5 - Changing the data",
        kind="script",
        title="More docks, more in the centre",
        prompt=(
            "Every station still open gets more docks: eight more in the"
            " centre zone, four more elsewhere. ONE UPDATE whose SET"
            " adds a CASE on zone -- docks = docks + CASE zone WHEN"
            " 'centre' THEN 8 ELSE 4 END -- with a WHERE that leaves the"
            " closed station alone.\n\n"
            "Checked: each zone's docks added up"
        ),
        solution="UPDATE stations SET docks = docks + CASE zone WHEN 'centre' THEN 8 ELSE 4 END WHERE closed_on IS NULL;",
        trap_sql="UPDATE stations SET docks = docks + CASE zone WHEN 'centre' THEN 8 ELSE 4 END;",
        probe_sql="SELECT zone, SUM(docks) FROM stations GROUP BY zone",
        note="A SET expression can read the row's other columns, and a"
             " CASE inside it makes one statement do what would"
             " otherwise be two UPDATEs with different WHEREs. The ELSE"
             " matters: without it a station in no listed zone would get"
             " NULL, and docks is NOT NULL. The trap forgets the WHERE"
             " and gives Old Mill, closed since March, four docks it will"
             " never use: south comes to 52 instead of 48.",
        claims=[("centre up 24, the other zones up 8 or 12",
                 lambda rows, c: sorted(rows) == [("centre", 124), ("east", 54), ("north", 80), ("south", 48), ("west", 56)])],
    ),
    dict(
        id=15, ledger="Q1161", concept="SAV", tier="5 - Changing the data",
        kind="script",
        title="An undo for one statement",
        prompt=(
            "Delete the 'other' jobs from maintenance -- that is the"
            " change you mean to keep. Then set a SAVEPOINT named s,"
            " run DELETE FROM maintenance with no WHERE (the mistake),"
            " and take it back with ROLLBACK TO s, then RELEASE s. Five"
            " statements; the probe should see every kind but 'other'"
            " still there.\n\n"
            "Checked: how many jobs of each kind remain"
        ),
        solution=("DELETE FROM maintenance WHERE kind = 'other';\n"
                  "SAVEPOINT s;\n"
                  "DELETE FROM maintenance;\n"
                  "ROLLBACK TO s;\n"
                  "RELEASE s;"),
        trap_sql=("DELETE FROM maintenance WHERE kind = 'other';\n"
                  "SAVEPOINT s;\n"
                  "DELETE FROM maintenance;\n"
                  "RELEASE s;"),
        probe_sql="SELECT kind, COUNT(*) FROM maintenance GROUP BY kind",
        note="A SAVEPOINT marks a point inside a transaction; ROLLBACK TO"
             " undoes everything since the mark and leaves the"
             " transaction open, and RELEASE forgets the mark and keeps"
             " what came before it. RELEASE on its own, the trap, commits"
             " the mistake along with the rest: the probe finds nothing."
             " A plain ROLLBACK would have undone the first DELETE too."
             " The sandbox opens a transaction for you, which is why no"
             " BEGIN is needed.",
        claims=[("four kinds left, 'other' gone",
                 lambda rows, c: sorted(rows) == [("battery", 24), ("brakes", 229), ("chain", 295), ("puncture", 452)])],
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
