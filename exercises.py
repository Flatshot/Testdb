"""Practice exercises: fifteen questions on the hotel-group schema.

The third set on the hotel schema (SEED 1356): eight hotels, their
rooms, guests, bookings, the extras charged to a stay, the payments made
against it and the reviews left afterwards. Nine questions read and six
change the data, the last three of them procedures. Ten of the fifteen
use a tool these tables have not met; five bring back what the second
set found hard -- what a window is partitioned by, where an outer join's
conditions go, a grand total laid over a grouped query, the fan-out of
two child tables, an upsert -- in a different task. The prompts name the
tool but do not write the statement. Hotels and their rooms -- rooms
priced above their own hotel's average by a window aggregate, each
guest's first stay at each hotel by a numbering restarted per pair, a
closing hotel night by night from a calendar made by a recursive CTE.
Guests -- email domains by string functions, a stay extended by a second
booking found with a self-join, guests who have tried every hotel by
COUNT(DISTINCT) against a counted subquery. Money and time -- arrivals
by day of the week with strftime, each channel's share of revenue by a
window with empty brackets, a bill printed line by line with UNION ALL.

Changing rows, three single statements:

  * an UPDATE whose increase is chosen by a CASE expression
  * an UPDATE ... FROM, which joins a second table into the UPDATE
  * a DELETE of whole groups, picked by GROUP BY and HAVING

Procedures, three scripts of several steps. SQLite has no CREATE
PROCEDURE; what it has is a transaction, whose steps stand or fall
together, a view, which is a query stored under a name, and a trigger
body, which is stored and runs when called:

  * a view of every bill, then an INSERT that reads the view
  * rows archived with CREATE TABLE ... AS SELECT, then deleted in
    the order foreign keys allow
  * a totals table, filled once and then kept right by a trigger

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

_REV = "(julianday(check_out) - julianday(check_in)) * rate_cents"
_Y2025 = "status = 'stayed' AND check_in >= '2025-01-01' AND check_in < '2026-01-01'"

EXERCISES = [
    # ======================================== 1 Hotels and their rooms
    dict(
        id=1, ledger="Q1372", concept="ABOVE", tier="1 - Hotels and their rooms",
        title="Rooms priced well above their own hotel",
        prompt=(
            "Each hotel has its own level of prices: a dear room at"
            " Fellfoot Inn costs less than a cheap one at Spa Gardens."
            " List the rooms whose list price (rack_cents) is more than"
            " one and a quarter times the average list price of THEIR"
            " OWN hotel, with the hotel's name and that average beside"
            " them. A window aggregate: an average with OVER and a"
            " partition, but no ORDER BY, gives every row its group's"
            " figure without collapsing the rows. As with any window,"
            " the test on it goes in an outer query. The average is"
            " compared to two decimal places.\n\n"
            "Return: hotel, room_no, rack_cents, hotel_avg"
        ),
        solution=("SELECT h.name, x.room_no, x.rack_cents, x.hotel_avg FROM"
                  " (SELECT r.hotel_id, r.room_no, r.rack_cents,"
                  " AVG(r.rack_cents) OVER (PARTITION BY r.hotel_id) AS hotel_avg FROM rooms r) x"
                  " JOIN hotels h ON h.hotel_id = x.hotel_id WHERE x.rack_cents > 1.25 * x.hotel_avg"),
        trap_sql=("SELECT h.name, x.room_no, x.rack_cents, x.hotel_avg FROM"
                  " (SELECT r.hotel_id, r.room_no, r.rack_cents,"
                  " AVG(r.rack_cents) OVER () AS hotel_avg FROM rooms r) x"
                  " JOIN hotels h ON h.hotel_id = x.hotel_id WHERE x.rack_cents > 1.25 * x.hotel_avg"),
        note="GROUP BY would give one row per hotel and lose the rooms."
             " AVG(...) OVER (PARTITION BY hotel_id) keeps every room"
             " and writes its hotel's average beside it, so the two"
             " can be compared on one row. Leave the partition out,"
             " the trap, and every room is measured against the"
             " average of all 176: 43 rooms pass, 32 of them at Spa"
             " Gardens, where nearly every room is dear by the"
             " group's standard, and Fellfoot Inn's two dearest"
             " vanish because 7,950 is cheap by it. A"
             " correlated subquery in the WHERE gets the same answer;"
             " the window reads the table once.",
        claims=[("fourteen rooms in seven hotels, none of them at Abbey Steps",
                 lambda rows, c: len(rows) == 14 and len({r[0] for r in rows}) == 7
                 and all(r[0] != "Abbey Steps" for r in rows)),
                ("Fellfoot Inn's rooms 103 and 106 are there, against an average of 5,821.43",
                 lambda rows, c: sorted((r[1], r[2], round(r[3], 2)) for r in rows if r[0] == "Fellfoot Inn")
                 == [("103", 7950, 5821.43), ("106", 7700, 5821.43)])],
    ),
    dict(
        id=2, ledger="Q1373", concept="FIRST", tier="1 - Hotels and their rooms",
        title="How each hotel's guests first found it",
        prompt=(
            "A guest's first stay at a hotel says how that hotel won"
            " them. Take stays only (status 'stayed'). For each guest"
            " and each hotel, find the first stay that guest made AT"
            " THAT HOTEL: the earliest check_in, and the lower"
            " booking_id if two begin on the same day. Then count"
            " those first stays by hotel name and channel. A numbering"
            " window function, whose numbering restarts for every pair"
            " of guest and hotel -- not for every guest, and not for"
            " every hotel.\n\n"
            "Return: hotel, channel, first_stays"
        ),
        solution=("SELECT h.name, x.channel, COUNT(*) FROM"
                  " (SELECT r.hotel_id, b.channel, ROW_NUMBER() OVER (PARTITION BY b.guest_id, r.hotel_id"
                  " ORDER BY b.check_in, b.booking_id) AS n FROM bookings b JOIN rooms r ON r.room_id = b.room_id"
                  " WHERE b.status = 'stayed') x JOIN hotels h ON h.hotel_id = x.hotel_id"
                  " WHERE x.n = 1 GROUP BY h.name, x.channel"),
        trap_sql=("SELECT h.name, x.channel, COUNT(*) FROM"
                  " (SELECT r.hotel_id, b.channel, ROW_NUMBER() OVER (PARTITION BY b.guest_id"
                  " ORDER BY b.check_in, b.booking_id) AS n FROM bookings b JOIN rooms r ON r.room_id = b.room_id"
                  " WHERE b.status = 'stayed') x JOIN hotels h ON h.hotel_id = x.hotel_id"
                  " WHERE x.n = 1 GROUP BY h.name, x.channel"),
        note="PARTITION BY takes a list. With guest_id and hotel_id"
             " together the count restarts for each pair, so number 1"
             " is that guest's first stay at that hotel: 6,728 pairs,"
             " 6,728 first stays. Partition by the guest alone, the"
             " trap, and each guest has one number 1 in the whole"
             " group -- 1,501 rows, and a hotel is credited only with"
             " guests who had never stayed anywhere before. Partition"
             " by the hotel alone and eight rows survive. The window"
             " is in a subquery because n = 1 cannot be tested where n"
             " is made; the GROUP BY outside then counts what is left.",
        claims=[("32 rows, eight hotels by four channels, 6,728 first stays in all",
                 lambda rows, c: len(rows) == 32 and sum(r[2] for r in rows) == 6728),
                ("Spa Gardens won 575 guests through the web",
                 lambda rows, c: ("Spa Gardens", "web", 575) in rows)],
    ),
    dict(
        id=3, ledger="Q1374", concept="CALENDAR", tier="1 - Hotels and their rooms",
        title="Abbey Steps, night by night, to the end",
        prompt=(
            "Abbey Steps is hotel 4 and closed on 2026-03-01. For each"
            " of the ten nights from 2026-02-23 to 2026-03-04: how"
            " many of its rooms were occupied by a stay (status"
            " 'stayed')? A guest is in the house on night d when"
            " check_in <= d < check_out. Every one of the ten nights"
            " must have a row, the empty ones with 0. No table holds"
            " one row per date, so make one: a recursive CTE (WITH"
            " RECURSIVE) begins with a first row and keeps adding a"
            " day to the row before until a stop date. Then an outer"
            " join from the nights to the bookings -- and remember"
            " where the conditions on the booking have to be written"
            " for an empty night to survive them.\n\n"
            "Return: night, rooms_sold"
        ),
        solution=("WITH RECURSIVE nights(night) AS (SELECT '2026-02-23' UNION ALL"
                  " SELECT date(night, '+1 day') FROM nights WHERE night < '2026-03-04')"
                  " SELECT n.night, COUNT(b.booking_id) FROM nights n LEFT JOIN bookings b"
                  " ON b.check_in <= n.night AND n.night < b.check_out AND b.status = 'stayed'"
                  " AND b.room_id IN (SELECT room_id FROM rooms WHERE hotel_id = 4)"
                  " GROUP BY n.night"),
        trap_sql=("WITH RECURSIVE nights(night) AS (SELECT '2026-02-23' UNION ALL"
                  " SELECT date(night, '+1 day') FROM nights WHERE night < '2026-03-04')"
                  " SELECT n.night, COUNT(b.booking_id) FROM nights n LEFT JOIN bookings b"
                  " ON b.check_in <= n.night AND n.night < b.check_out"
                  " WHERE b.status = 'stayed' AND b.room_id IN (SELECT room_id FROM rooms WHERE hotel_id = 4)"
                  " GROUP BY n.night"),
        note="The CTE has two halves joined by UNION ALL: a SELECT"
             " that makes the first night, and a SELECT from the CTE"
             " itself that makes the next one from the last, with a"
             " WHERE to stop it. Ten rows, and now there is something"
             " to LEFT JOIN from. A night matches a booking when it"
             " falls inside the half-open range, and all four"
             " conditions on the booking sit in the ON. Move the"
             " status and the hotel into WHERE, the trap, and they"
             " are tested after the join, where an empty night's"
             " booking columns are NULL: the four nights after the"
             " hotel closed fall out and the answer has six rows. It"
             " is the same mistake as the empty rooms of Fellfoot"
             " Inn, with dates in place of rooms.",
        claims=[("ten nights, seven rooms on the last night of trading",
                 lambda rows, c: len(rows) == 10 and ("2026-02-28", 7) in rows),
                ("the four nights from 1 March are there, with 0",
                 lambda rows, c: sorted(r for r in rows if r[0] >= "2026-03-01")
                 == [("2026-03-01", 0), ("2026-03-02", 0), ("2026-03-03", 0), ("2026-03-04", 0)])],
    ),
    # ======================================================== 2 Guests
    dict(
        id=4, ledger="Q1375", concept="DOMAIN", tier="2 - Guests",
        title="Where the guests' email lives",
        prompt=(
            "The part of an email address after the @ is its domain."
            " For each domain: how many guests use it, and how many of"
            " those are in the loyalty scheme (tier is not NULL)."
            " Guests with no email are left out altogether, not shown"
            " as a group of their own. Two string functions: one finds"
            " the position of a character inside a text, the other"
            " takes the part of a text from a given position on.\n\n"
            "Return: domain, guests, members"
        ),
        solution=("SELECT substr(email, instr(email, '@') + 1), COUNT(*), COUNT(tier) FROM guests"
                  " WHERE email IS NOT NULL GROUP BY 1"),
        trap_sql=("SELECT substr(email, instr(email, '@') + 1), COUNT(*), COUNT(tier) FROM guests"
                  " GROUP BY 1"),
        note="instr(email, '@') is the position of the @, counted"
             " from 1, and substr(email, that + 1) is everything after"
             " it; without the + 1 the @ comes too. Both give NULL for"
             " a NULL email, and GROUP BY puts all the NULLs in one"
             " group: the trap returns a fifth row, a domain of"
             " nothing with 279 guests in it. COUNT(tier) counts the"
             " rows where tier is not NULL, which is how one query"
             " gives both the guests and the members.",
        claims=[("four domains, 1,321 guests between them",
                 lambda rows, c: len(rows) == 4 and sum(r[1] for r in rows) == 1321),
                ("example.net has the most guests, 347, and the fewest members, 68",
                 lambda rows, c: ("example.net", 347, 68) in rows
                 and max(r[1] for r in rows) == 347 and min(r[2] for r in rows) == 68)],
    ),
    dict(
        id=5, ledger="Q1376", concept="EXTEND", tier="2 - Guests",
        title="A stay extended by booking again",
        prompt=(
            "When a guest extends a stay the desk sometimes enters a"
            " second booking instead of changing the first: the same"
            " guest, in the same room, checking in on the very day the"
            " first booking checks out. Find those pairs, both"
            " bookings being stays (status 'stayed'). A self-join: the"
            " bookings table joined to itself under two aliases, one"
            " playing the earlier stay and one the later. Booking ids"
            " do not run in date order, so let the dates decide which"
            " is which.\n\n"
            "Return: guest_id, room_id, first_booking, second_booking,"
            " check_in, check_out -- the check_in of the earlier"
            " booking and the check_out of the later"
        ),
        solution=("SELECT a.guest_id, a.room_id, a.booking_id, b.booking_id, a.check_in, b.check_out"
                  " FROM bookings a JOIN bookings b ON b.guest_id = a.guest_id AND b.room_id = a.room_id"
                  " AND b.check_in = a.check_out WHERE a.status = 'stayed' AND b.status = 'stayed'"),
        trap_sql=("SELECT a.guest_id, a.room_id, a.booking_id, b.booking_id, a.check_in, b.check_out"
                  " FROM bookings a JOIN bookings b ON b.guest_id = a.guest_id"
                  " AND b.check_in = a.check_out WHERE a.status = 'stayed' AND b.status = 'stayed'"),
        note="A table can be joined to itself as long as each copy has"
             " its own alias: here a is the earlier stay and b the"
             " later, and the ON says what ties them -- same guest,"
             " same room, b beginning the day a ends. Every column"
             " must then say which copy it comes from. The trap"
             " leaves out the room and finds 332 pairs: guests who"
             " left one room, or one hotel, and checked into another"
             " the same day. Because the dates order the pair, each"
             " pair appears once; a self-join on equality alone would"
             " need a.booking_id < b.booking_id to stop it listing"
             " every pair twice and every row beside itself.",
        claims=[("three pairs",
                 lambda rows, c: len(rows) == 3),
                ("guest 54 in room 127: booking 3406 then 3327, 16 to 22 April 2025",
                 lambda rows, c: (54, 127, 3406, 3327, "2025-04-16", "2025-04-22") in rows)],
    ),
    dict(
        id=6, ledger="Q1377", concept="EVERY", tier="2 - Guests",
        title="Guests who have tried every hotel",
        prompt=(
            "Which guests have stayed (status 'stayed') at every hotel"
            " the group has ever had, Abbey Steps included? Give each"
            " with their total number of stays. Do not type the number"
            " of hotels: compare the count of DIFFERENT hotels a guest"
            " has stayed at with a subquery that counts the hotels"
            " table. The test is on a group, so it belongs in"
            " HAVING.\n\n"
            "Return: guest_id, name, stays"
        ),
        solution=("SELECT g.guest_id, g.name, COUNT(*) FROM guests g JOIN bookings b ON b.guest_id = g.guest_id"
                  " JOIN rooms r ON r.room_id = b.room_id WHERE b.status = 'stayed' GROUP BY g.guest_id"
                  " HAVING COUNT(DISTINCT r.hotel_id) = (SELECT COUNT(*) FROM hotels)"),
        trap_sql=("SELECT g.guest_id, g.name, COUNT(*) FROM guests g JOIN bookings b ON b.guest_id = g.guest_id"
                  " JOIN rooms r ON r.room_id = b.room_id WHERE b.status = 'stayed' GROUP BY g.guest_id"
                  " HAVING COUNT(r.hotel_id) >= (SELECT COUNT(*) FROM hotels)"),
        note="'Every' is a count in disguise: a guest has been to"
             " every hotel when the number of different hotels in"
             " their stays equals the number of hotels there are."
             " COUNT(DISTINCT r.hotel_id) counts each hotel once"
             " however often it was visited, and the subquery keeps"
             " the 8 out of the statement, so it stays right when a"
             " ninth hotel opens. Without DISTINCT, the trap, the"
             " count is of stays: 560 guests have eight stays or"
             " more, most of them at three or four favourite hotels."
             " Two aggregates sit side by side here, COUNT(*) for the"
             " answer and COUNT(DISTINCT) for the test.",
        claims=[("71 guests",
                 lambda rows, c: len(rows) == 71),
                ("Pavel Ivanova, guest 598, did it in the fewest stays: eleven",
                 lambda rows, c: min(r[2] for r in rows) == 11 and (598, "Pavel Ivanova", 11) in rows)],
    ),
    # ================================================ 3 Money and time
    dict(
        id=7, ledger="Q1378", concept="WDAY", tier="3 - Money and time",
        title="Which day of the week guests arrive",
        prompt=(
            "For stays (status 'stayed') that began in 2025: group"
            " them by the day of the week of check_in, and give the"
            " number of arrivals and the average length of stay in"
            " nights. strftime turns a date into text in a format you"
            " choose, and one of its codes is the day of the week as a"
            " digit, '0' for Sunday to '6' for Saturday. Return the"
            " digit as strftime gives it, which is text. The average"
            " is compared to two decimal places.\n\n"
            "Return: weekday, arrivals, avg_nights"
        ),
        solution=("SELECT strftime('%w', check_in), COUNT(*), AVG(julianday(check_out) - julianday(check_in))"
                  " FROM bookings WHERE " + _Y2025 + " GROUP BY 1"),
        trap_sql=("SELECT strftime('%w', booked_at), COUNT(*), AVG(julianday(check_out) - julianday(check_in))"
                  " FROM bookings WHERE " + _Y2025 + " GROUP BY 1"),
        note="strftime('%w', check_in) is the weekday of that date,"
             " and grouping by it folds a year of dates into seven"
             " rows. Fridays and Saturdays lead, with 1,472 and 1,402"
             " arrivals; the other five days lie between 1,242 and"
             " 1,313. The trap takes the weekday of booked_at:"
             " the day the guest picked up the phone, not the day"
             " they arrived, and that is spread almost evenly, so the"
             " weekend disappears. '%m' gives the month and '%Y' the"
             " year the same way. The result is text: '5', not 5.",
        claims=[("seven rows, 9,191 arrivals",
                 lambda rows, c: len(rows) == 7 and sum(r[1] for r in rows) == 9191),
                ("Friday, '5', is the busiest with 1,472",
                 lambda rows, c: max(rows, key=lambda r: r[1])[:2] == ("5", 1472))],
    ),
    dict(
        id=8, ledger="Q1379", concept="PCT", tier="3 - Money and time",
        title="Each channel's share of the room revenue",
        prompt=(
            "For stays (status 'stayed') that began in 2025, room"
            " revenue is nights times rate_cents. For each channel:"
            " its room revenue, and that revenue as a percentage of"
            " all four channels together, rounded to one decimal"
            " place. The total has to appear on every row beside the"
            " group's own figure. A window with empty brackets, OVER"
            " (), spans the whole result, and it can be laid over a"
            " grouped query as the running total was last time.\n\n"
            "Return: channel, room_cents, pct"
        ),
        solution=("SELECT channel, SUM(" + _REV + "), ROUND(100.0 * SUM(" + _REV + ")"
                  " / SUM(SUM(" + _REV + ")) OVER (), 1) FROM bookings WHERE " + _Y2025 + " GROUP BY channel"),
        trap_sql=("SELECT channel, SUM(" + _REV + "), ROUND(100.0 * SUM(" + _REV + ")"
                  " / (SELECT SUM(" + _REV + ") FROM bookings WHERE status = 'stayed'), 1)"
                  " FROM bookings WHERE " + _Y2025 + " GROUP BY channel"),
        note="GROUP BY has already made four rows by the time the"
             " window runs, so SUM(SUM(...)) OVER () adds up the four"
             " group totals and writes the result on each row: the"
             " inner SUM belongs to the GROUP BY, the outer one to"
             " the window. Empty brackets mean one partition, no"
             " order, everything. The older way is a scalar subquery"
             " for the total, and its danger is the trap: the"
             " subquery is a separate query and has to repeat the"
             " filter. Forget the year there and each 2025 figure is"
             " divided by the revenue of every year, and the four"
             " shares add up to well under a hundred. Multiplying by"
             " 100.0, not 100, keeps the division out of whole"
             " numbers.",
        claims=[("four channels whose shares add up to 100.0",
                 lambda rows, c: len(rows) == 4 and round(sum(r[2] for r in rows), 1) == 100.0),
                ("the web brings 134,581,250 cents, 48.9 per cent",
                 lambda rows, c: [(r[1], r[2]) for r in rows if r[0] == "web"] == [(134581250, 48.9)])],
    ),
    dict(
        id=9, ledger="Q1380", concept="BILL", tier="3 - Money and time",
        title="The bill for booking 15410, line by line",
        prompt=(
            "Print the bill for booking 15410, three nights at Station"
            " House. One line for the room: the item 'room' and nights"
            " times rate_cents as the amount. One line for EVERY"
            " charge, the item being its kind. One line for EVERY"
            " payment, the item 'paid' and the amount made NEGATIVE,"
            " so that a settled bill adds up to nothing. Three SELECTs"
            " stacked into one result. There are two words for"
            " stacking, and one of them quietly throws away lines that"
            " look alike: this guest had breakfast three times.\n\n"
            "Return: item, cents"
        ),
        solution=("SELECT 'room', (julianday(check_out) - julianday(check_in)) * rate_cents FROM bookings"
                  " WHERE booking_id = 15410"
                  " UNION ALL SELECT kind, amount_cents FROM charges WHERE booking_id = 15410"
                  " UNION ALL SELECT 'paid', -amount_cents FROM payments WHERE booking_id = 15410"),
        trap_sql=("SELECT 'room', (julianday(check_out) - julianday(check_in)) * rate_cents FROM bookings"
                  " WHERE booking_id = 15410"
                  " UNION SELECT kind, amount_cents FROM charges WHERE booking_id = 15410"
                  " UNION SELECT 'paid', -amount_cents FROM payments WHERE booking_id = 15410"),
        note="UNION ALL puts one result under another; the SELECTs"
             " need only the same number of columns, and the first"
             " one names them. Three tables with nothing in common"
             " but a booking_id become one list of twelve lines that"
             " sums to zero. Plain UNION, the trap, also removes"
             " duplicate rows, as DISTINCT does, and on a bill two"
             " lines that look alike are two things bought: three"
             " breakfasts at 1,200 become one, three nights' parking"
             " become one, and the bill is 4,400 cents out. UNION is"
             " for lists where a repeat means the same thing twice;"
             " for lines of money it is almost always UNION ALL.",
        claims=[("twelve lines that add up to nothing",
                 lambda rows, c: len(rows) == 12 and sum(r[1] for r in rows) == 0),
                ("three breakfasts at 1,200 and three payments",
                 lambda rows, c: rows.count(("breakfast", 1200)) == 3 and sum(r[0] == "paid" for r in rows) == 3)],
    ),
    # ================================================= 4 Changing rows
    dict(
        id=10, ledger="Q1381", concept="UPLIFT", tier="4 - Changing rows",
        kind="script",
        title="Fellfoot Inn puts its prices up, by kind of room",
        prompt=(
            "Fellfoot Inn (hotel 8) raises its list prices: singles by"
            " 250 cents, twins by 400, and every other kind of room by"
            " 600. In ONE UPDATE statement. A CASE expression can"
            " stand wherever a value can, including on the right of"
            " SET, and its ELSE takes care of 'every other'. No other"
            " hotel's prices change.\n\n"
            "Checked: rooms and total list price by kind, for Fellfoot"
            " Inn and for the other hotels together"
        ),
        solution=("UPDATE rooms SET rack_cents = rack_cents +\n"
                  "  CASE kind WHEN 'single' THEN 250 WHEN 'twin' THEN 400 ELSE 600 END\n"
                  "WHERE hotel_id = 8;"),
        trap_sql=("UPDATE rooms SET rack_cents = rack_cents +\n"
                  "  CASE kind WHEN 'single' THEN 250 WHEN 'twin' THEN 400 ELSE 600 END;"),
        probe_sql="SELECT hotel_id = 8, kind, COUNT(*), SUM(rack_cents) FROM rooms GROUP BY 1, 2",
        note="The CASE is worked out afresh for each row the UPDATE"
             " visits, so one statement gives three different rises."
             " Three UPDATEs would do it too, but one statement cannot"
             " be left a third done. Two things go wrong quietly. A"
             " CASE with no ELSE gives NULL for the kinds it does not"
             " name, and a price plus NULL is NULL -- here the NOT"
             " NULL on rack_cents would stop it, loudly, which is the"
             " constraint earning its keep. And the CASE decides how"
             " much, not which rows: without the WHERE, the trap,"
             " all 176 rooms in the group go up, not Fellfoot Inn's"
             " fourteen.",
        claims=[("Fellfoot Inn: six singles at 30,300 in all, four twins 26,250, two doubles 13,600, two family 16,850",
                 lambda rows, c: sorted(r[1:] for r in rows if r[0] == 1)
                 == [("double", 2, 13600), ("family", 2, 16850), ("single", 6, 30300), ("twin", 4, 26250)]),
                ("the other seven hotels' totals are as they were",
                 lambda rows, c: sorted(r[1:] for r in rows if r[0] == 0)
                 == [("double", 72, 648250), ("family", 24, 322800), ("single", 24, 167900),
                     ("suite", 8, 148600), ("twin", 34, 307150)])],
    ),
    dict(
        id=11, ledger="Q1382", concept="CAP", tier="4 - Changing rows",
        kind="script",
        title="Nobody pays over the list price at Station House",
        prompt=(
            "Station House (hotel 6) has promised that no future guest"
            " will pay more than the list price. For its bookings not"
            " yet arrived (status 'booked') whose rate_cents is above"
            " the rack_cents of the room booked, bring the rate down"
            " to that list price. Rates already at or below it stay as"
            " they are, and so does every other hotel. The new value"
            " lives in another table: UPDATE ... FROM joins that table"
            " into the UPDATE, so that SET can use its columns"
            " directly. It does with a join what the correlated"
            " subquery did last time.\n\n"
            "Checked: for Station House and for the other hotels"
            " together, by status: bookings, the total of their rates,"
            " and how many are above the list price"
        ),
        solution=("UPDATE bookings SET rate_cents = r.rack_cents\n"
                  "FROM rooms r\n"
                  "WHERE r.room_id = bookings.room_id AND r.hotel_id = 6\n"
                  "  AND bookings.status = 'booked' AND bookings.rate_cents > r.rack_cents;"),
        trap_sql=("UPDATE bookings SET rate_cents = r.rack_cents\n"
                  "FROM rooms r\n"
                  "WHERE r.room_id = bookings.room_id AND r.hotel_id = 6\n"
                  "  AND bookings.status = 'booked';"),
        probe_sql=("SELECT r.hotel_id = 6, b.status, COUNT(*), SUM(b.rate_cents), SUM(b.rate_cents > r.rack_cents)"
                   " FROM bookings b JOIN rooms r ON r.room_id = b.room_id GROUP BY 1, 2"),
        note="UPDATE bookings ... FROM rooms r WHERE r.room_id ="
             " bookings.room_id pairs each booking with its room, and"
             " after that r.rack_cents is simply there to be used: in"
             " SET as the new value, in WHERE as the test, and to pick"
             " the hotel, with no subquery repeated three times. The"
             " join condition goes in the WHERE; without it every"
             " booking meets every room. 149 of Station House's 206"
             " future bookings come down, by 121,100 cents between"
             " them. The trap drops the test that the rate is above"
             " the list price and sets all 206 to it, which RAISES"
             " the 51 guests who had been promised less, by 44,650.",
        claims=[("Station House's 206 future bookings now total 1,489,200 cents, none above the list price",
                 lambda rows, c: [r[2:] for r in rows if r[:2] == (1, "booked")] == [(206, 1489200, 0)]),
                ("its past stays and the other hotels' future bookings are as they were",
                 lambda rows, c: (1, "stayed", 1526, 10688450, 312) in rows
                 and (0, "booked", 1661, 17789850, 1226) in rows)],
    ),
    dict(
        id=12, ledger="Q1383", concept="ZERO", tier="4 - Changing rows",
        kind="script",
        title="Deposits paid and refunded in full",
        prompt=(
            "When a booking is cancelled in good time its deposit is"
            " refunded, and its two payments -- one positive, one"
            " negative -- add up to nothing. The accountant wants"
            " those rows gone: delete every payment that belongs to a"
            " booking whose payments sum to exactly zero. A booking"
            " whose payments do not cancel out keeps all of them, and"
            " that includes the cancelled bookings where the deposit"
            " was kept. The test is on a whole group of rows, so find"
            " the booking_ids with GROUP BY and HAVING and let the"
            " DELETE take every row that carries one of them. One"
            " statement.\n\n"
            "Checked: by booking status: payment rows left, bookings"
            " with a payment left, the total left, and refunds left"
        ),
        solution=("DELETE FROM payments WHERE booking_id IN\n"
                  "  (SELECT booking_id FROM payments GROUP BY booking_id HAVING SUM(amount_cents) = 0);"),
        trap_sql=("DELETE FROM payments WHERE booking_id IN\n"
                  "  (SELECT booking_id FROM bookings WHERE status = 'cancelled');"),
        probe_sql=("SELECT b.status, COUNT(*), COUNT(DISTINCT p.booking_id), SUM(p.amount_cents),"
                   " SUM(p.amount_cents < 0) FROM payments p JOIN bookings b ON b.booking_id = p.booking_id"
                   " GROUP BY b.status"),
        note="A DELETE works a row at a time, but the rule here is"
             " about a booking's payments taken together. So the"
             " subquery groups payments by booking, HAVING keeps the"
             " groups that sum to zero, and what comes out is a list"
             " of booking_ids; the DELETE then removes every row"
             " wearing one of them, 1,956 rows for 978 bookings."
             " Nothing but the payments table is needed. The trap"
             " reasons that refunds belong to cancelled bookings and"
             " deletes all of theirs, which also takes the 258"
             " deposits the group kept: 2,315,000 cents of real"
             " income gone from the books. Deleting groups that sum"
             " to zero cannot change the total, and that is the"
             " check.",
        claims=[("cancelled bookings keep 258 payments, the kept deposits: 2,315,000 cents and no refunds",
                 lambda rows, c: [r[1:] for r in rows if r[0] == "cancelled"] == [(258, 258, 2315000, 0)]),
                ("23,899 payments are left and they still total 529,424,790",
                 lambda rows, c: sum(r[1] for r in rows) == 23899 and sum(r[3] for r in rows) == 529424790)],
    ),
    # ==================================================== 5 Procedures
    dict(
        id=13, ledger="Q1384", concept="BILLS", tier="5 - Procedures",
        kind="script",
        title="A view of every bill, and a night audit that reads it",
        prompt=(
            "Two steps. First create a VIEW called bills, with one row"
            " for each stay (status 'stayed') and exactly these"
            " columns: booking_id, check_out, room_cents (nights times"
            " rate_cents), extras_cents (the sum of its charges, 0 if"
            " it has none) and paid_cents (the sum of its payments, 0"
            " if none). A view is a SELECT stored under a name and"
            " read like a table. A stay has many charges and many"
            " payments: beware the fan-out that counts each once for"
            " every row of the other. Then use the view. For every"
            " stay still in the house when the data ends (check_out"
            " after '2026-06-30') that owes money, INSERT one payment"
            " of exactly what it owes, by 'card', paid_at '2026-06-30"
            " 23:30'. What a stay owes is room plus extras less"
            " paid.\n\n"
            "Checked: the view's rows and its three totals; payments"
            " made at 23:30; stays in the house still owing; stays"
            " owing anywhere"
        ),
        solution=("CREATE VIEW bills AS\n"
                  "SELECT b.booking_id, b.check_out,\n"
                  "  CAST(julianday(b.check_out) - julianday(b.check_in) AS INTEGER) * b.rate_cents AS room_cents,\n"
                  "  COALESCE((SELECT SUM(c.amount_cents) FROM charges c WHERE c.booking_id = b.booking_id), 0)"
                  " AS extras_cents,\n"
                  "  COALESCE((SELECT SUM(p.amount_cents) FROM payments p WHERE p.booking_id = b.booking_id), 0)"
                  " AS paid_cents\n"
                  "FROM bookings b WHERE b.status = 'stayed';\n"
                  "INSERT INTO payments (booking_id, paid_at, amount_cents, method)\n"
                  "SELECT booking_id, '2026-06-30 23:30', room_cents + extras_cents - paid_cents, 'card'\n"
                  "FROM bills WHERE check_out > '2026-06-30' AND room_cents + extras_cents - paid_cents > 0;"),
        trap_sql=("CREATE VIEW bills AS\n"
                  "SELECT b.booking_id, b.check_out,\n"
                  "  CAST(julianday(b.check_out) - julianday(b.check_in) AS INTEGER) * b.rate_cents AS room_cents,\n"
                  "  COALESCE(SUM(c.amount_cents), 0) AS extras_cents,\n"
                  "  COALESCE(SUM(p.amount_cents), 0) AS paid_cents\n"
                  "FROM bookings b LEFT JOIN charges c ON c.booking_id = b.booking_id\n"
                  "  LEFT JOIN payments p ON p.booking_id = b.booking_id\n"
                  "WHERE b.status = 'stayed' GROUP BY b.booking_id;\n"
                  "INSERT INTO payments (booking_id, paid_at, amount_cents, method)\n"
                  "SELECT booking_id, '2026-06-30 23:30', room_cents + extras_cents - paid_cents, 'card'\n"
                  "FROM bills WHERE check_out > '2026-06-30' AND room_cents + extras_cents - paid_cents > 0;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM bills),"
                   " (SELECT CAST(SUM(room_cents) AS INTEGER) FROM bills),"
                   " (SELECT SUM(extras_cents) FROM bills),"
                   " (SELECT SUM(paid_cents) FROM bills),"
                   " (SELECT COUNT(*) FROM payments WHERE paid_at = '2026-06-30 23:30'),"
                   " (SELECT COUNT(*) FROM bills WHERE check_out > '2026-06-30'"
                   " AND room_cents + extras_cents <> paid_cents),"
                   " (SELECT COUNT(*) FROM bills WHERE room_cents + extras_cents <> paid_cents)"),
        note="CREATE VIEW stores the query, not its result. The hard"
             " thinking -- nights, the two sums, each worked out on"
             " its own so that neither multiplies the other -- is done"
             " once and given a name, and the INSERT that follows is"
             " three plain lines reading bills as if it were a table."
             " Because the view is run afresh every time it is read,"
             " the 79 payments the INSERT makes show up in paid_cents"
             " at once, and no stay in the house owes anything; the"
             " 886 that left without settling still do. The trap"
             " builds the view by joining both child tables and"
             " grouping: every charge is counted once per payment and"
             " every payment once per charge, the totals come out"
             " several times too large, and the night audit collects"
             " the wrong amounts from the wrong stays. A view hides"
             " its query, so a mistake inside one is inherited by"
             " everything that reads it.",
        claims=[("13,625 bills; 79 payments at 23:30; nobody in the house owes; 886 stays elsewhere still do",
                 lambda rows, c: len(rows) == 1 and rows[0][0] == 13625 and rows[0][4:] == (79, 0, 886)),
                ("room 399,130,750, extras 146,785,270, and paid 514,381,270 with the 4,009,680 collected",
                 lambda rows, c: rows[0][1:4] == (399130750, 146785270, 514381270))],
    ),
    dict(
        id=14, ledger="Q1385", concept="ARCHIVE", tier="5 - Procedures",
        kind="script",
        title="Abbey Steps' dead bookings leave the live tables",
        prompt=(
            "Abbey Steps (hotel 4) has closed, and its bookings that"
            " never became stays -- status 'cancelled' or 'no_show' --"
            " are to move out of the live tables, and their payments"
            " with them. In ONE transaction: create a table"
            " old_bookings holding those booking rows, all columns;"
            " create a table old_payments holding every payment of"
            " those bookings, all columns; then delete the same rows"
            " from payments and from bookings. CREATE TABLE ... AS"
            " SELECT makes a table out of a query's result. Two orders"
            " matter. A row has to be copied before it is deleted."
            " And foreign keys are enforced, so a booking that still"
            " has payments cannot be deleted. The question then issues"
            " a ROLLBACK: committed work survives it.\n\n"
            "Checked: rows in old_bookings; rows and total in"
            " old_payments; rows left in bookings; rows and total left"
            " in payments"
        ),
        solution=("BEGIN;\n"
                  "CREATE TABLE old_bookings AS\n"
                  "SELECT b.* FROM bookings b JOIN rooms r ON r.room_id = b.room_id\n"
                  "WHERE r.hotel_id = 4 AND b.status IN ('cancelled', 'no_show');\n"
                  "CREATE TABLE old_payments AS\n"
                  "SELECT * FROM payments WHERE booking_id IN (SELECT booking_id FROM old_bookings);\n"
                  "DELETE FROM payments WHERE booking_id IN (SELECT booking_id FROM old_bookings);\n"
                  "DELETE FROM bookings WHERE booking_id IN (SELECT booking_id FROM old_bookings);\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "CREATE TABLE old_bookings AS\n"
                  "SELECT b.* FROM bookings b JOIN rooms r ON r.room_id = b.room_id\n"
                  "WHERE r.hotel_id = 4 AND b.status IN ('cancelled', 'no_show');\n"
                  "DELETE FROM payments WHERE booking_id IN (SELECT booking_id FROM old_bookings);\n"
                  "DELETE FROM bookings WHERE booking_id IN (SELECT booking_id FROM old_bookings);\n"
                  "CREATE TABLE old_payments AS\n"
                  "SELECT * FROM payments WHERE booking_id IN (SELECT booking_id FROM old_bookings);\n"
                  "COMMIT;"),
        driver_sql="ROLLBACK;",
        probe_sql=("SELECT (SELECT COUNT(*) FROM old_bookings), (SELECT COUNT(*) FROM old_payments),"
                   " (SELECT SUM(amount_cents) FROM old_payments), (SELECT COUNT(*) FROM bookings),"
                   " (SELECT COUNT(*) FROM payments), (SELECT SUM(amount_cents) FROM payments)"),
        note="CREATE TABLE ... AS SELECT takes its columns and its"
             " rows from the query, so the archive is made and filled"
             " in one step; it copies no keys or constraints, which"
             " is why old_payments can outlive the bookings it"
             " mentions. Once old_bookings exists it is the list of"
             " what is moving, and the other three statements all"
             " read it. The order is copy, copy, delete the children,"
             " delete the parents. Deleting bookings before their"
             " payments fails loudly on the foreign key. Deleting the"
             " payments before copying them, the trap, fails"
             " silently: old_payments is created, empty, and 101"
             " payments worth 121,600 cents are in neither table."
             " Inside one transaction the creates and the deletes"
             " stand or fall together -- in SQLite even CREATE TABLE"
             " can be rolled back.",
        claims=[("75 bookings and their 101 payments, 121,600 cents, are in the archive",
                 lambda rows, c: len(rows) == 1 and rows[0][:3] == (75, 101, 121600)),
                ("17,404 bookings and 25,754 payments remain; nothing was lost between the two payment tables",
                 lambda rows, c: rows[0][3:5] == (17404, 25754) and rows[0][2] + rows[0][5] == 529424790)],
    ),
    dict(
        id=15, ledger="Q1386", concept="TOTALS", tier="5 - Procedures",
        kind="script",
        title="A total of extras that keeps itself up to date",
        prompt=(
            "The bar wants each booking's extras total without adding"
            " up its charges every time. Three steps. Create a table"
            " extras_totals with booking_id as its PRIMARY KEY and"
            " total_cents. Fill it from the charges already there, one"
            " row for each booking that has any. Then create a trigger"
            " that fires AFTER INSERT ON charges and keeps the table"
            " right: a booking already in it has the new amount added"
            " to its total, and a booking not yet in it gets a row."
            " That is the upsert of the last set, written inside a"
            " trigger body, where NEW is the row just inserted. The"
            " question then inserts four charges: two for booking"
            " 15170, which has 40,900 cents of extras already, and two"
            " for booking 14148, which has none.\n\n"
            "Checked: the number of rows in extras_totals and their"
            " grand total; the rows for bookings 15170 and 14148"
        ),
        solution=("CREATE TABLE extras_totals (booking_id INTEGER PRIMARY KEY, total_cents INTEGER NOT NULL);\n"
                  "INSERT INTO extras_totals (booking_id, total_cents)\n"
                  "SELECT booking_id, SUM(amount_cents) FROM charges GROUP BY booking_id;\n"
                  "CREATE TRIGGER charges_keep_total AFTER INSERT ON charges\n"
                  "BEGIN\n"
                  "  INSERT INTO extras_totals (booking_id, total_cents)\n"
                  "  VALUES (NEW.booking_id, NEW.amount_cents)\n"
                  "  ON CONFLICT (booking_id) DO UPDATE SET total_cents = total_cents + excluded.total_cents;\n"
                  "END;"),
        trap_sql=("CREATE TABLE extras_totals (booking_id INTEGER PRIMARY KEY, total_cents INTEGER NOT NULL);\n"
                  "INSERT INTO extras_totals (booking_id, total_cents)\n"
                  "SELECT booking_id, SUM(amount_cents) FROM charges GROUP BY booking_id;\n"
                  "CREATE TRIGGER charges_keep_total AFTER INSERT ON charges\n"
                  "BEGIN\n"
                  "  INSERT OR REPLACE INTO extras_totals (booking_id, total_cents)\n"
                  "  VALUES (NEW.booking_id, NEW.amount_cents);\n"
                  "END;"),
        driver_sql=("INSERT INTO charges (booking_id, kind, amount_cents, charged_on)"
                    " VALUES (15170, 'bar', 1850, '2026-06-30');\n"
                    "INSERT INTO charges (booking_id, kind, amount_cents, charged_on)"
                    " VALUES (14148, 'breakfast', 1400, '2026-06-30');\n"
                    "INSERT INTO charges (booking_id, kind, amount_cents, charged_on)"
                    " VALUES (15170, 'spa', 6000, '2026-06-30');\n"
                    "INSERT INTO charges (booking_id, kind, amount_cents, charged_on)"
                    " VALUES (14148, 'parking', 900, '2026-06-30');"),
        probe_sql=("SELECT 'all', COUNT(*), SUM(total_cents) FROM extras_totals"
                   " UNION ALL SELECT 'booking', booking_id, total_cents FROM extras_totals"
                   " WHERE booking_id IN (15170, 14148)"),
        note="A total kept in a table is quick to read and wrong the"
             " moment someone forgets to update it, so the updating"
             " is given to the database: the trigger runs for every"
             " charge inserted, whoever inserts it. Its body has two"
             " cases, a booking with a row and a booking without,"
             " and ON CONFLICT (booking_id) DO UPDATE handles both in"
             " one statement -- which is why booking_id has to be the"
             " primary key. Inside DO UPDATE, total_cents is the"
             " figure already stored and excluded.total_cents the one"
             " that was refused. INSERT OR REPLACE, the trap, throws"
             " the old row away: booking 15170 ends at 6,000, its"
             " last charge, when it should be 48,750. The fill comes"
             " first for the same reason; a trigger only knows about"
             " charges made after it existed.",
        claims=[("booking 15170 stands at 48,750 and booking 14148, new to the table, at 2,300",
                 lambda rows, c: sorted(r[1:] for r in rows if r[0] == "booking")
                 == [(14148, 2300), (15170, 48750)]),
                ("12,155 bookings have a total, and the totals come to 146,795,420: every charge, old and new",
                 lambda rows, c: [r[1:] for r in rows if r[0] == "all"] == [(12155, 146795420)])],
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
