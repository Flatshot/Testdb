"""Practice exercises: fifteen questions on the hotel-group schema.

The fourth set on the hotel schema (SEED 1356): eight hotels, their
rooms, guests, bookings, the extras charged to a stay, the payments made
against it and the reviews left afterwards. Nine questions read and six
change the data, the last three of them procedures. Ten of the fifteen
go back to what the third set found hard, each in a new task: a table
joined to itself, a test on a whole group in HAVING, deleting from the
table the rows are actually in, a view that later statements read, and
carrying every condition a task states into the statement, down to the
exact value. Five use a tool these tables have not met: a row value
compared with a two-column subquery, INTERSECT and EXCEPT, a window
frame, ALTER TABLE ... ADD COLUMN, and a unique index, one of them
partial. The prompts name the tool but do not write the statement.
Hotels and their rooms -- interchangeable rooms by a self-join that
lists each pair once, rooms with fewer than two arrivals in a month by
an outer join and HAVING, the dearest let of each room by a row value.
Guests -- two bookings held for one day by a self-join in which the
status gives each copy its part, guests faithful to one hotel by two
tests in one HAVING, guests of both Keswick hotels by INTERSECT and
EXCEPT. Money and time -- stays whose extras outran the room by a sum
tested in HAVING, a three-month moving average by a window frame, 2026
against 2025 by a CTE joined to itself.

Changing rows, three single statements:

  * a DELETE from a child table, chosen by facts three tables away
  * an UPDATE fed by GROUP BY and HAVING, that must leave some rows be
  * an UPDATE of two columns at once, with four conditions to carry

Procedures, three scripts of several steps. SQLite has no CREATE
PROCEDURE; what it has is a script whose steps depend on each other, a
view, which is a query stored under a name, and an index, which is a
rule stored in the database:

  * a column added with ALTER TABLE, filled, and then used
  * a view of each hotel's reviews, and two UPDATEs that read it
  * duplicates cleared away, then two unique indexes, one partial

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

_NIGHTS = "(julianday(b.check_out) - julianday(b.check_in))"
_REV = "(julianday(check_out) - julianday(check_in)) * rate_cents"
_AT = "FROM bookings b JOIN rooms r ON r.room_id = b.room_id WHERE b.status = 'stayed' AND r.hotel_id = "

EXERCISES = [
    # ======================================== 1 Hotels and their rooms
    dict(
        id=1, ledger="Q1387", concept="PAIRS", tier="1 - Hotels and their rooms",
        title="Rooms that can stand in for each other",
        prompt=(
            "When a room is out of order the desk moves its guest to"
            " one exactly like it. List every pair of interchangeable"
            " rooms: two different rooms in the same hotel, of the"
            " same kind, on the same floor, with the same list price"
            " (rack_cents). A self-join again: rooms joined to itself"
            " under two aliases. Last time the dates said which copy"
            " played which part. Here nothing does, and a plain 'not"
            " the same room' lists every pair twice, once each way"
            " round. Each pair must appear once, the room with the"
            " lower room_id first.\n\n"
            "Return: hotel, first_room, second_room, rack_cents -- the"
            " hotel's name and the two room_no values"
        ),
        solution=("SELECT h.name, a.room_no, b.room_no, a.rack_cents FROM rooms a"
                  " JOIN rooms b ON b.hotel_id = a.hotel_id AND b.kind = a.kind AND b.floor = a.floor"
                  " AND b.rack_cents = a.rack_cents AND a.room_id < b.room_id"
                  " JOIN hotels h ON h.hotel_id = a.hotel_id"),
        trap_sql=("SELECT h.name, a.room_no, b.room_no, a.rack_cents FROM rooms a"
                  " JOIN rooms b ON b.hotel_id = a.hotel_id AND b.kind = a.kind AND b.floor = a.floor"
                  " AND b.rack_cents = a.rack_cents AND a.room_id <> b.room_id"
                  " JOIN hotels h ON h.hotel_id = a.hotel_id"),
        note="The ON carries four things the two rooms share and one"
             " that tells them apart. With only the four, every room"
             " pairs with itself. With a.room_id <> b.room_id, the"
             " trap, a room no longer meets itself but 101 meets 102"
             " and 102 meets 101: 168 rows for 84 pairs. a.room_id <"
             " b.room_id lets each pair through one way round only,"
             " and it also keeps a room from itself, so it does both"
             " jobs. Three rooms alike make three pairs, which is why"
             " Lakeside Lodge, with its rows of identical doubles,"
             " has 27 of the 84.",
        claims=[("84 pairs, 27 of them at Lakeside Lodge and 2 at Abbey Steps",
                 lambda rows, c: len(rows) == 84 and sum(r[0] == "Lakeside Lodge" for r in rows) == 27
                 and sum(r[0] == "Abbey Steps" for r in rows) == 2),
                ("no pair appears both ways round",
                 lambda rows, c: not any((r[0], r[2], r[1], r[3]) in rows for r in rows))],
    ),
    dict(
        id=2, ledger="Q1388", concept="QUIET", tier="1 - Hotels and their rooms",
        title="Rooms February nearly forgot",
        prompt=(
            "February is the quiet month. Which rooms, in any hotel,"
            " had fewer than two stays (status 'stayed') ARRIVING in"
            " February 2026 -- check_in from 2026-02-01 up to but not"
            " including 2026-03-01? A room with no such stay at all"
            " belongs in the answer, with 0. Two things met before,"
            " now together: an outer join from the rooms, with the"
            " conditions on the booking written where an empty room"
            " survives them, and a test on the group's count, which"
            " belongs in HAVING. Mind what you count: one of the two"
            " ways of counting gives an empty room 1.\n\n"
            "Return: hotel, room_no, stays -- hotel is its name"
        ),
        solution=("SELECT h.name, r.room_no, COUNT(b.booking_id) FROM rooms r"
                  " JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " LEFT JOIN bookings b ON b.room_id = r.room_id AND b.status = 'stayed'"
                  " AND b.check_in >= '2026-02-01' AND b.check_in < '2026-03-01'"
                  " GROUP BY r.room_id HAVING COUNT(b.booking_id) < 2"),
        trap_sql=("SELECT h.name, r.room_no, COUNT(*) FROM rooms r"
                  " JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " LEFT JOIN bookings b ON b.room_id = r.room_id AND b.status = 'stayed'"
                  " AND b.check_in >= '2026-02-01' AND b.check_in < '2026-03-01'"
                  " GROUP BY r.room_id HAVING COUNT(*) < 2"),
        note="The LEFT JOIN keeps every room, and because the status"
             " and the dates are in the ON, a room with no February"
             " stay still has its one row, with NULLs where the"
             " booking would be. COUNT(b.booking_id) counts the rows"
             " where a booking is really there, so that room scores"
             " 0. COUNT(*), the trap, counts rows, and the row of"
             " NULLs is a row: room 312 at Spa Gardens comes out with"
             " 1, indistinguishable from the ten rooms that did have"
             " one guest. HAVING then tests the count after the"
             " grouping; WHERE could not, because when WHERE runs"
             " there is no count yet.",
        claims=[("eleven rooms, three of them at Spa Gardens and three at Fellfoot Inn",
                 lambda rows, c: len(rows) == 11 and sum(r[0] == "Spa Gardens" for r in rows) == 3
                 and sum(r[0] == "Fellfoot Inn" for r in rows) == 3),
                ("one room had nobody: 312 at Spa Gardens",
                 lambda rows, c: [r for r in rows if r[2] == 0] == [("Spa Gardens", "312", 0)])],
    ),
    dict(
        id=3, ledger="Q1389", concept="TOPRATE", tier="1 - Hotels and their rooms",
        title="The best price each room ever fetched",
        prompt=(
            "For each room at Fellfoot Inn (hotel 8), find the stay or"
            " stays (status 'stayed') that paid the highest rate_cents"
            " that room has ever been let for. A room whose top rate"
            " was paid more than once has a row for each of those"
            " stays. A grouped query gives each room its top rate."
            " The bookings wanted are those that match it on BOTH"
            " things at once, the room and the rate. A row value --"
            " two columns in brackets -- can be compared with a"
            " subquery that returns two columns.\n\n"
            "Return: room_no, booking_id, check_in, rate_cents"
        ),
        solution=("SELECT r.room_no, b.booking_id, b.check_in, b.rate_cents FROM bookings b"
                  " JOIN rooms r ON r.room_id = b.room_id WHERE r.hotel_id = 8 AND b.status = 'stayed'"
                  " AND (b.room_id, b.rate_cents) IN"
                  " (SELECT room_id, MAX(rate_cents) FROM bookings WHERE status = 'stayed' GROUP BY room_id)"),
        trap_sql=("SELECT r.room_no, b.booking_id, b.check_in, b.rate_cents FROM bookings b"
                  " JOIN rooms r ON r.room_id = b.room_id WHERE r.hotel_id = 8 AND b.status = 'stayed'"
                  " AND b.rate_cents IN"
                  " (SELECT MAX(rate_cents) FROM bookings WHERE status = 'stayed' GROUP BY room_id)"),
        note="(b.room_id, b.rate_cents) IN (SELECT room_id, MAX(...)"
             " ... GROUP BY room_id) asks whether this booking's PAIR"
             " is one of the pairs in the list: this room, at this"
             " room's top rate. The trap compares the rate alone with"
             " a list of every room's top rate, so a booking gets in"
             " if its rate happens to be the best that ANY room"
             " fetched. Room 204's record is 5,300, a figure other"
             " rooms take on an ordinary night: 129 rows where there"
             " should be 25. A join to the grouped query on both"
             " columns does the same work; the row value says it in"
             " one line. No LIMIT could do this, since the number of"
             " rows wanted differs from room to room.",
        claims=[("25 stays for the 14 rooms; room 102's top rate was paid five times",
                 lambda rows, c: len(rows) == 25 and len({r[0] for r in rows}) == 14
                 and sum(r[0] == "102" for r in rows) == 5),
                ("room 101's best was booking 11204 at 5,550; room 103's record is 8,750",
                 lambda rows, c: [r for r in rows if r[0] == "101"] == [("101", 11204, "2025-12-18", 5550)]
                 and {r[3] for r in rows if r[0] == "103"} == {8750})],
    ),
    # ======================================================== 2 Guests
    dict(
        id=4, ledger="Q1390", concept="TWOHELD", tier="2 - Guests",
        title="Two bookings held, one let go",
        prompt=(
            "Some guests hold two bookings for the same arrival day"
            " and let one of them go. Find every pair of bookings by"
            " the same guest with the same check_in in which one was"
            " cancelled (status 'cancelled') and the other became a"
            " stay (status 'stayed'). The self-join once more:"
            " bookings under two aliases, and this time it is the"
            " status that gives each copy its part, so every pair"
            " comes out once. Put the nightly rate of the booking"
            " that was dropped beside the rate of the one that was"
            " kept.\n\n"
            "Return: guest_id, check_in, cancelled_booking,"
            " stay_booking, cancelled_rate, stay_rate"
        ),
        solution=("SELECT a.guest_id, a.check_in, a.booking_id, b.booking_id, a.rate_cents, b.rate_cents"
                  " FROM bookings a JOIN bookings b ON b.guest_id = a.guest_id AND b.check_in = a.check_in"
                  " WHERE a.status = 'cancelled' AND b.status = 'stayed'"),
        trap_sql=("SELECT a.guest_id, a.check_in, a.booking_id, b.booking_id, a.rate_cents, b.rate_cents"
                  " FROM bookings a JOIN bookings b ON b.guest_id = a.guest_id AND b.check_in = a.check_in"
                  " AND b.booking_id <> a.booking_id WHERE a.status = 'cancelled'"),
        note="Alias a is the booking that was cancelled and alias b"
             " the one that was slept in. The ON says what joins them"
             " -- same guest, same arrival day -- and the WHERE gives"
             " each alias its status. Because the two statuses"
             " differ, a row can never pair with itself and no pair"
             " can come out both ways round, so no a.booking_id <"
             " b.booking_id is needed. The trap pins down only the"
             " cancelled side and lets b be any other booking: 44"
             " rows, the extra five being pairs where the second"
             " booking was also cancelled or has not arrived yet. In"
             " 24 of the 39 pairs the guest kept the cheaper room.",
        claims=[("39 pairs",
                 lambda rows, c: len(rows) == 39),
                ("in 24 the stay cost less a night than the booking given up, in 14 more",
                 lambda rows, c: sum(r[5] < r[4] for r in rows) == 24 and sum(r[5] > r[4] for r in rows) == 14),
                ("guest 14 dropped booking 4777 at 9,050 and kept 4371 at 7,550",
                 lambda rows, c: (14, "2025-06-27", 4777, 4371, 9050, 7550) in rows)],
    ),
    dict(
        id=5, ledger="Q1391", concept="FAITHFUL", tier="2 - Guests",
        title="Guests who never try anywhere else",
        prompt=(
            "Most guests move round the group. Which guests have"
            " stayed (status 'stayed') at least three times and"
            " always at the SAME hotel? Two tests on one group, both"
            " in the same HAVING: one on how many stays the guest"
            " has, one on how many DIFFERENT hotels they were at. The"
            " group is the guest, not the guest and the hotel. Give"
            " the hotel's name as well; in a group with only one"
            " hotel in it, MIN or MAX of the name is that hotel.\n\n"
            "Return: guest_id, name, hotel, stays -- name is the"
            " guest's, hotel is the hotel's name"
        ),
        solution=("SELECT g.guest_id, g.name, MIN(h.name), COUNT(*) FROM guests g"
                  " JOIN bookings b ON b.guest_id = g.guest_id JOIN rooms r ON r.room_id = b.room_id"
                  " JOIN hotels h ON h.hotel_id = r.hotel_id WHERE b.status = 'stayed'"
                  " GROUP BY g.guest_id HAVING COUNT(*) >= 3 AND COUNT(DISTINCT r.hotel_id) = 1"),
        trap_sql=("SELECT g.guest_id, g.name, MIN(h.name), COUNT(*) FROM guests g"
                  " JOIN bookings b ON b.guest_id = g.guest_id JOIN rooms r ON r.room_id = b.room_id"
                  " JOIN hotels h ON h.hotel_id = r.hotel_id WHERE b.status = 'stayed'"
                  " GROUP BY g.guest_id, r.hotel_id HAVING COUNT(*) >= 3"),
        note="'Always at the same hotel' is a count again: the number"
             " of different hotels among the guest's stays is 1."
             " HAVING takes both tests joined by AND, as WHERE would"
             " for rows. The trap groups by guest AND hotel, which"
             " makes one group for every pair, and then every group"
             " has one hotel in it by construction: it answers 'has"
             " stayed three times at some hotel', 1,635 rows, and a"
             " guest with three stays at each of two hotels is listed"
             " twice. What you group by decides what a row of the"
             " answer IS, so it has to be settled first. Only five"
             " guests are this faithful, four of them to Spa"
             " Gardens.",
        claims=[("five guests, four of them at Spa Gardens and one at Lakeside Lodge",
                 lambda rows, c: len(rows) == 5 and sorted(r[2] for r in rows)
                 == ["Lakeside Lodge"] + ["Spa Gardens"] * 4),
                ("Fatima Qureshi and Hugo Wetherby have four stays each, the other three have three",
                 lambda rows, c: sorted((r[1], r[3]) for r in rows if r[3] == 4)
                 == [("Fatima Qureshi", 4), ("Hugo Wetherby", 4)] and sum(r[3] == 3 for r in rows) == 3)],
    ),
    dict(
        id=6, ledger="Q1392", concept="BOTH", tier="2 - Guests",
        title="Both Keswick hotels, never Spa Gardens",
        prompt=(
            "Keswick has two hotels, Lakeside Lodge (hotel 7) and"
            " Fellfoot Inn (hotel 8). Which guests have stayed"
            " (status 'stayed') at BOTH of them and have never stayed"
            " at Spa Gardens (hotel 5)? UNION ALL stacked one list on"
            " another; its relatives compare lists. INTERSECT keeps"
            " what is in both of two lists, and EXCEPT takes one list"
            " away from another. Three lists of guest_ids, one for"
            " each hotel, with those two words between them.\n\n"
            "Return: guest_id"
        ),
        solution=("SELECT b.guest_id " + _AT + "7"
                  " INTERSECT SELECT b.guest_id " + _AT + "8"
                  " EXCEPT SELECT b.guest_id " + _AT + "5"),
        trap_sql=("SELECT b.guest_id FROM bookings b JOIN rooms r ON r.room_id = b.room_id"
                  " WHERE b.status = 'stayed' AND r.hotel_id IN (7, 8)"
                  " EXCEPT SELECT b.guest_id " + _AT + "5"),
        note="No single booking is at two hotels, so 'both' cannot be"
             " a WHERE on one row: hotel_id = 7 AND hotel_id = 8 is"
             " never true, and hotel_id IN (7, 8), the trap, means"
             " EITHER -- 223 guests, not 37. INTERSECT works on whole"
             " lists: the guests of one hotel, the guests of the"
             " other, and what the two have in common, 286 of them."
             " EXCEPT then removes anyone on the Spa Gardens list."
             " Both words drop duplicates as UNION does, so each"
             " guest appears once however often they stayed, and the"
             " three are worked from left to right. The HAVING of the"
             " last question could do it too; this reads the way the"
             " question is asked.",
        claims=[("37 guests, each once",
                 lambda rows, c: len(rows) == 37 and len(set(rows)) == 37),
                ("the lowest guest_id is 277 and the highest 1378",
                 lambda rows, c: min(r[0] for r in rows) == 277 and max(r[0] for r in rows) == 1378)],
    ),
    # ================================================ 3 Money and time
    dict(
        id=7, ledger="Q1393", concept="DOUBLE", tier="3 - Money and time",
        title="Stays where the extras outran the room",
        prompt=(
            "Now and then a guest takes a cheap room and lives well."
            " Find the bookings whose extras -- ALL their charges"
            " added together -- come to more than twice the cost of"
            " the room, which is nights times rate_cents. Charges"
            " exist only on stays, so no status test is needed. The"
            " test is on a booking's charges taken together, a whole"
            " group of rows, so it cannot be a WHERE on one charge:"
            " group, and test the sum in HAVING.\n\n"
            "Return: booking_id, room_cents, extras_cents"
        ),
        solution=("SELECT b.booking_id, " + _NIGHTS + " * b.rate_cents, SUM(c.amount_cents)"
                  " FROM bookings b JOIN charges c ON c.booking_id = b.booking_id GROUP BY b.booking_id"
                  " HAVING SUM(c.amount_cents) > 2 * " + _NIGHTS + " * b.rate_cents"),
        trap_sql=("SELECT b.booking_id, " + _NIGHTS + " * b.rate_cents, SUM(c.amount_cents)"
                  " FROM bookings b JOIN charges c ON c.booking_id = b.booking_id"
                  " WHERE c.amount_cents > 2 * " + _NIGHTS + " * b.rate_cents GROUP BY b.booking_id"),
        note="One table of children joined to its parent and grouped"
             " by the parent: no fan-out, since there is only one"
             " child table. WHERE is asked of each joined row before"
             " any grouping, HAVING of each group after it. The trap"
             " puts the test in WHERE, where it means 'a single"
             " charge more than twice the room': three bookings pass,"
             " and the extras shown for them are the sum of that one"
             " charge only, because the others were filtered out"
             " before they could be added. HAVING sees the total, and"
             " sixteen bookings pass. Booking 6044 leads: a room at"
             " 8,650 and 21,550 of extras, in three charges none of"
             " which would pass alone -- much like the payments"
             " that only summed to zero together.",
        claims=[("sixteen bookings",
                 lambda rows, c: len(rows) == 16),
                ("booking 6044 spent 21,550 on extras against 8,650 for the room",
                 lambda rows, c: (6044, 8650, 21550) in [(r[0], int(r[1]), r[2]) for r in rows]
                 and max(r[2] for r in rows) == 21550)],
    ),
    dict(
        id=8, ledger="Q1394", concept="MOVING", tier="3 - Money and time",
        title="A three-month moving average of room revenue",
        prompt=(
            "Room revenue is nights times rate_cents, for stays"
            " (status 'stayed'). Give it for each month of check_in,"
            " written 'YYYY-MM', for all eighteen months of data."
            " Beside it put the average of that month and the two"
            " months before it, a three-month moving average, which"
            " smooths the seasons out. The first month has nothing"
            " before it and averages itself alone; the second"
            " averages two. A window frame: after the window's ORDER"
            " BY, a ROWS BETWEEN clause says how far back from the"
            " current row the window reaches. It is laid over a"
            " grouped query, as the running total was. The average is"
            " compared to two decimal places.\n\n"
            "Return: month, room_cents, avg3"
        ),
        solution=("SELECT strftime('%Y-%m', check_in), SUM(" + _REV + "),"
                  " AVG(SUM(" + _REV + ")) OVER (ORDER BY strftime('%Y-%m', check_in)"
                  " ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)"
                  " FROM bookings WHERE status = 'stayed' GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', check_in), SUM(" + _REV + "),"
                  " AVG(SUM(" + _REV + ")) OVER (ORDER BY strftime('%Y-%m', check_in))"
                  " FROM bookings WHERE status = 'stayed' GROUP BY 1"),
        note="A window with an ORDER BY and no frame runs from the"
             " first row to the current one, which is what made the"
             " running total. ROWS BETWEEN 2 PRECEDING AND CURRENT"
             " ROW narrows it to three rows that slide down the"
             " result, and near the top, where two rows back do not"
             " exist, it uses what there is. The trap leaves the"
             " frame out and gets the average of every month so far:"
             " the same for the first three rows, then it flattens,"
             " and by June 2026 it says 22,173,931 when the last"
             " three months averaged 23,491,083. As before, the inner"
             " SUM belongs to the GROUP BY and the AVG round it to"
             " the window.",
        claims=[("eighteen months, the first two averaging what there is",
                 lambda rows, c: len(rows) == 18
                 and [(r[0], round(r[2], 2)) for r in sorted(rows)[:2]]
                 == [("2025-01", 15318950.0), ("2025-02", 14765050.0)]),
                ("March 2025 took 21,727,500 and its average is 17,085,866.67",
                 lambda rows, c: [(int(r[1]), round(r[2], 2)) for r in rows if r[0] == "2025-03"]
                 == [(21727500, 17085866.67)]),
                ("June 2026's average is 23,491,083.33",
                 lambda rows, c: [round(r[2], 2) for r in rows if r[0] == "2026-06"] == [23491083.33])],
    ),
    dict(
        id=9, ledger="Q1395", concept="YEARAGO", tier="3 - Money and time",
        title="This year against last, month by month",
        prompt=(
            "Is 2026 ahead of 2025? Count the stays (status 'stayed')"
            " by the year and the month of check_in, once, in a CTE."
            " Then join that CTE to ITSELF: one alias plays 2025 and"
            " the other 2026, matched month to month, for January to"
            " June, the six months 2026 has. A named query can be"
            " joined to itself exactly as a table can. Give the month"
            " as strftime writes it, two characters of text, and the"
            " change as 2026 minus 2025.\n\n"
            "Return: month, stays_2025, stays_2026, change"
        ),
        solution=("WITH m AS (SELECT strftime('%Y', check_in) AS y, strftime('%m', check_in) AS mon,"
                  " COUNT(*) AS stays FROM bookings WHERE status = 'stayed' GROUP BY 1, 2)"
                  " SELECT a.mon, a.stays, b.stays, b.stays - a.stays FROM m a JOIN m b ON b.mon = a.mon"
                  " WHERE a.y = '2025' AND b.y = '2026'"),
        trap_sql=("WITH m AS (SELECT strftime('%Y', check_in) AS y, strftime('%m', check_in) AS mon,"
                  " COUNT(*) AS stays FROM bookings WHERE status = 'stayed' GROUP BY 1, 2)"
                  " SELECT a.mon, a.stays, b.stays, b.stays - a.stays FROM m a JOIN m b"
                  " ON a.y = '2025' AND b.y = '2026'"),
        note="The CTE does the counting once and has eighteen rows,"
             " one for each month of each year. Joined to itself, a"
             " is narrowed to 2025 and b to 2026 by the WHERE, and"
             " the ON lines them up by month, so January meets"
             " January. An inner join also drops July to December of"
             " 2025, which have no partner yet. The trap gives each"
             " alias its year and forgets the month: every month of"
             " 2025 beside every month of 2026, 72 rows. Two things"
             " tie the copies together in a self-join -- what they"
             " share and how they differ -- and both have to be"
             " written. 2026 is ahead in five months of six, by 93"
             " stays in February, and 15 behind in June.",
        claims=[("six rows, January to June",
                 lambda rows, c: sorted(r[0] for r in rows) == ["01", "02", "03", "04", "05", "06"]),
                ("February: 557 then 650, up 93; June: 804 then 789, down 15",
                 lambda rows, c: ("02", 557, 650, 93) in rows and ("06", 804, 789, -15) in rows)],
    ),
    # ================================================= 4 Changing rows
    dict(
        id=10, ledger="Q1396", concept="PARKING", tier="4 - Changing rows",
        kind="script",
        title="Gold members park free at Spa Gardens",
        prompt=(
            "Spa Gardens (hotel 5) has decided that gold members park"
            " free, back-dated to the start of 2026. Delete every"
            " charge of kind 'parking' with a charged_on of"
            " 2026-01-01 or later that sits on a booking at Spa"
            " Gardens made by a guest whose tier is 'gold'. The rows"
            " to go are charges and nothing else: the bookings, the"
            " guests and all their other charges stay. But the facts"
            " that pick them out are three tables away -- the tier is"
            " on the guest and the hotel is on the room -- so they"
            " are reached through a subquery on booking_id. One"
            " statement.\n\n"
            "Checked: charges, split by Spa Gardens or not, gold or"
            " not, and kind: how many, their total, and how many are"
            " dated 2026"
        ),
        solution=("DELETE FROM charges\n"
                  "WHERE kind = 'parking' AND charged_on >= '2026-01-01'\n"
                  "  AND booking_id IN (SELECT b.booking_id FROM bookings b\n"
                  "                     JOIN guests g ON g.guest_id = b.guest_id\n"
                  "                     JOIN rooms r ON r.room_id = b.room_id\n"
                  "                     WHERE g.tier = 'gold' AND r.hotel_id = 5);"),
        trap_sql=("DELETE FROM charges\n"
                  "WHERE kind = 'parking'\n"
                  "  AND booking_id IN (SELECT b.booking_id FROM bookings b\n"
                  "                     JOIN guests g ON g.guest_id = b.guest_id\n"
                  "                     JOIN rooms r ON r.room_id = b.room_id\n"
                  "                     WHERE g.tier = 'gold' AND r.hotel_id = 5);"),
        probe_sql=("SELECT r.hotel_id = 5, g.tier IS 'gold', c.kind, COUNT(*), SUM(c.amount_cents),"
                   " SUM(c.charged_on >= '2026-01-01') FROM charges c"
                   " JOIN bookings b ON b.booking_id = c.booking_id JOIN guests g ON g.guest_id = b.guest_id"
                   " JOIN rooms r ON r.room_id = b.room_id GROUP BY 1, 2, 3"),
        note="A DELETE names one table, and it is the table whose"
             " rows are to go: charges. Everything else is only"
             " looked at. Two of the four conditions are about the"
             " charge itself, its kind and its date, and sit in the"
             " DELETE's own WHERE; the other two are about the"
             " booking's guest and room, so a subquery joins those"
             " tables and hands back the booking_ids that qualify."
             " 34 charges go, 61,200 cents. The trap carries three"
             " conditions of the four and forgets the date, taking"
             " 2025's parking too: all 129 charges, 232,200 cents. Each"
             " condition in the task is one term in the statement,"
             " and it is worth counting them off. A DELETE has no"
             " undo outside a transaction, so run it as a SELECT"
             " COUNT(*) first.",
        claims=[("gold members' parking at Spa Gardens: 95 charges left, 171,000 cents, none dated 2026",
                 lambda rows, c: [r[3:] for r in rows if r[:3] == (1, 1, "parking")] == [(95, 171000, 0)]),
                ("their other charges, and other guests' parking there, are untouched",
                 lambda rows, c: (1, 0, "parking", 2407, 4332600, 797) in rows
                 and sum(r[3] for r in rows) == 55513)],
    ),
    dict(
        id=11, ledger="Q1397", concept="SEVEN", tier="4 - Changing rows",
        kind="script",
        title="Seven hotels makes you silver",
        prompt=(
            "The loyalty scheme gets a new way in: a guest who has"
            " stayed (status 'stayed') at seven or more DIFFERENT"
            " hotels becomes 'silver'. It applies only to guests who"
            " are in no tier yet (tier is NULL). Nobody who is"
            " already silver or gold is touched, least of all moved"
            " down. Find the guests with GROUP BY and HAVING, as a"
            " list of guest_ids, and let one UPDATE of the guests"
            " table use the list.\n\n"
            "Checked: for each tier, the number of guests and the sum"
            " of their guest_ids"
        ),
        solution=("UPDATE guests SET tier = 'silver'\n"
                  "WHERE tier IS NULL\n"
                  "  AND guest_id IN (SELECT b.guest_id FROM bookings b JOIN rooms r ON r.room_id = b.room_id\n"
                  "                   WHERE b.status = 'stayed' GROUP BY b.guest_id\n"
                  "                   HAVING COUNT(DISTINCT r.hotel_id) >= 7);"),
        trap_sql=("UPDATE guests SET tier = 'silver'\n"
                  "WHERE guest_id IN (SELECT b.guest_id FROM bookings b JOIN rooms r ON r.room_id = b.room_id\n"
                  "                   WHERE b.status = 'stayed' GROUP BY b.guest_id\n"
                  "                   HAVING COUNT(DISTINCT r.hotel_id) >= 7);"),
        probe_sql="SELECT tier, COUNT(*), SUM(guest_id) FROM guests GROUP BY tier",
        note="The subquery is the reading question of the last set"
             " turned into a list: bookings grouped by guest, HAVING"
             " keeping the groups with seven or more different"
             " hotels, 225 guests. The UPDATE names guests, the table"
             " whose rows change, and has a condition of its own as"
             " well: tier IS NULL -- IS, because nothing equals NULL."
             " 176 guests become silver. Without that condition, the"
             " trap, the statement also reaches the 49 on the list"
             " who are members already. For the 37 silver ones"
             " nothing changes, and the twelve gold ones are quietly"
             " demoted. An UPDATE has two questions to answer, which"
             " rows and what value, and 'which rows' usually has more"
             " parts than the task's first sentence.",
        claims=[("440 silver, 97 gold, and 1,063 guests still in no tier",
                 lambda rows, c: sorted((r[0] or "", r[1]) for r in rows)
                 == [("", 1063), ("gold", 97), ("silver", 440)])],
    ),
    dict(
        id=12, ledger="Q1398", concept="CLOSURE", tier="4 - Changing rows",
        kind="script",
        title="Lakeside Lodge shuts for a fortnight",
        prompt=(
            "Lakeside Lodge (hotel 7) closes for repairs. Nobody can"
            " sleep there on the nights of 2026-08-03 to 2026-08-16,"
            " and it reopens on the 17th. Cancel every booking not"
            " yet arrived (status 'booked') at that hotel that"
            " includes any of those nights: set its status to"
            " 'cancelled' and its cancelled_at to exactly '2026-06-30"
            " 12:00'. A stay is a half-open range, so a guest who"
            " checks OUT on 3 August, or checks IN on 17 August, is"
            " not affected -- and one who arrives on 1 August and"
            " leaves on the 5th is. The table has a CHECK that a"
            " booking is cancelled exactly when cancelled_at is"
            " filled in, so both columns change in the one UPDATE."
            " Count the conditions in this paragraph before you"
            " run it.\n\n"
            "Checked: for Lakeside Lodge and for the other hotels"
            " together, by status: bookings, how many have a"
            " cancelled_at, and how many were cancelled at"
            " '2026-06-30 12:00'"
        ),
        solution=("UPDATE bookings SET status = 'cancelled', cancelled_at = '2026-06-30 12:00'\n"
                  "WHERE status = 'booked'\n"
                  "  AND check_in < '2026-08-17' AND check_out > '2026-08-03'\n"
                  "  AND room_id IN (SELECT room_id FROM rooms WHERE hotel_id = 7);"),
        trap_sql=("UPDATE bookings SET status = 'cancelled', cancelled_at = '2026-06-30 12:00'\n"
                  "WHERE status = 'booked'\n"
                  "  AND check_in >= '2026-08-03' AND check_in < '2026-08-17'\n"
                  "  AND room_id IN (SELECT room_id FROM rooms WHERE hotel_id = 7);"),
        probe_sql=("SELECT r.hotel_id = 7, b.status, COUNT(*), COUNT(b.cancelled_at),"
                   " SUM(b.cancelled_at = '2026-06-30 12:00') FROM bookings b"
                   " JOIN rooms r ON r.room_id = b.room_id GROUP BY 1, 2"),
        note="SET takes a list, and here it must: change the status"
             " alone and the CHECK refuses the row. The WHERE has"
             " four parts -- the status, the hotel, and the two"
             " halves of the overlap test. A booking touches the"
             " closure when it starts before the closure ends AND"
             " ends after the closure starts: check_in < '2026-08-17'"
             " and check_out > '2026-08-03'. 46 bookings do. The trap"
             " asks only whether the guest ARRIVES during the"
             " closure, 38 bookings, and misses the eight who arrive"
             " in the days before and are still in bed when the"
             " builders come. The strict < and > are what leave alone"
             " the five who check out on the 3rd and the two who"
             " check in on the 17th. And the timestamp is checked to"
             " the minute: '2026-06-30' alone is a different value.",
        claims=[("Lakeside Lodge: 234 bookings still to arrive, and 270 cancelled, 46 of them at noon on 30 June",
                 lambda rows, c: (1, "booked", 234, 0, None) in rows and (1, "cancelled", 270, 270, 46) in rows),
                ("the other hotels' 1,587 future bookings are as they were",
                 lambda rows, c: (0, "booked", 1587, 0, None) in rows)],
    ),
    # ==================================================== 5 Procedures
    dict(
        id=13, ledger="Q1399", concept="LASTSTAY", tier="5 - Procedures",
        kind="script",
        title="A column for the last stay, and a shorter mailing list",
        prompt=(
            "Three steps, each needing the one before. The guests"
            " table is to remember when each guest last stayed. Add a"
            " column called last_stay to guests with ALTER TABLE ..."
            " ADD COLUMN; it will hold a date as text, and it starts"
            " out NULL in every row. Fill it: for each guest, the"
            " latest check_out among their stays (status 'stayed'),"
            " left NULL for a guest who has never stayed. Then use"
            " it. The mailing list is to drop everyone who has not"
            " stayed since the start of 2026: set email to NULL for"
            " every guest whose last_stay is before '2026-01-01',"
            " AND for every guest who has never stayed at all."
            " Remember what a comparison with NULL gives.\n\n"
            "Checked: guests; how many have a last_stay, the earliest"
            " and the latest; how many still have an email; and how"
            " many of those have no stay in 2026"
        ),
        solution=("ALTER TABLE guests ADD COLUMN last_stay TEXT;\n"
                  "UPDATE guests SET last_stay =\n"
                  "  (SELECT MAX(b.check_out) FROM bookings b\n"
                  "   WHERE b.guest_id = guests.guest_id AND b.status = 'stayed');\n"
                  "UPDATE guests SET email = NULL\n"
                  "WHERE last_stay < '2026-01-01' OR last_stay IS NULL;"),
        trap_sql=("ALTER TABLE guests ADD COLUMN last_stay TEXT;\n"
                  "UPDATE guests SET last_stay =\n"
                  "  (SELECT MAX(b.check_out) FROM bookings b\n"
                  "   WHERE b.guest_id = guests.guest_id AND b.status = 'stayed');\n"
                  "UPDATE guests SET email = NULL\n"
                  "WHERE last_stay < '2026-01-01';"),
        probe_sql=("SELECT COUNT(*), COUNT(last_stay), MIN(last_stay), MAX(last_stay), COUNT(email),"
                   " SUM(email IS NOT NULL AND (last_stay IS NULL OR last_stay < '2026-01-01')) FROM guests"),
        note="ALTER TABLE ... ADD COLUMN changes the table's shape:"
             " every existing row gets the new column, holding NULL"
             " unless a DEFAULT says otherwise. The fill is the"
             " correlated subquery of the price reset: for each"
             " guest, MAX(check_out) of their own stays. MAX over no"
             " rows is NULL, so the 99 guests who never stayed keep"
             " NULL without being asked. Step three reads the new"
             " column like any other. last_stay < '2026-01-01' is"
             " neither true nor false for a NULL, so on its own, the"
             " trap, it clears 145 emails and leaves the 82 people"
             " who never came at all still on the list, the very"
             " ones the rule was written for. OR last_stay IS NULL"
             " brings them in: 227 emails cleared, 1,094 left. A"
             " column that stores what a query could work out goes"
             " stale as soon as a guest stays again: it is quick"
             " to read and has to be kept up, as the totals table"
             " was by its trigger.",
        claims=[("1,501 of the 1,600 guests have a last_stay, from 2025-01-08 to 2026-07-12",
                 lambda rows, c: len(rows) == 1 and rows[0][:4] == (1600, 1501, "2025-01-08", "2026-07-12")),
                ("1,094 guests still have an email, every one of them with a stay in 2026",
                 lambda rows, c: rows[0][4:] == (1094, 0))],
    ),
    dict(
        id=14, ledger="Q1400", concept="STARS", tier="5 - Procedures",
        kind="script",
        title="Stars that follow the reviews",
        prompt=(
            "The group will let its guests decide the stars. First"
            " create a VIEW called hotel_scores with one row for each"
            " hotel and exactly these columns: hotel_id, reviews (how"
            " many reviews its stays have had) and avg_score (their"
            " average score). A review knows its booking, a booking"
            " its room, and a room its hotel. Then two UPDATEs of the"
            " hotels table, each reading the view. A hotel GAINS a"
            " star if its avg_score is 4.1 or more, AND it has at"
            " least 600 reviews, AND it has fewer than 5 stars. A"
            " hotel LOSES a star if its avg_score is below 3.78 AND"
            " it has more than 2 stars. A CHECK keeps stars between 2"
            " and 5, and one row that breaks it stops the whole"
            " statement. Five conditions; each is in the statement or"
            " it is not.\n\n"
            "Checked: each hotel's stars, with its reviews and"
            " avg_score (to three decimal places) from the view"
        ),
        solution=("CREATE VIEW hotel_scores AS\n"
                  "SELECT r.hotel_id, COUNT(*) AS reviews, AVG(v.score) AS avg_score\n"
                  "FROM reviews v JOIN bookings b ON b.booking_id = v.booking_id\n"
                  "  JOIN rooms r ON r.room_id = b.room_id\n"
                  "GROUP BY r.hotel_id;\n"
                  "UPDATE hotels SET stars = stars + 1\n"
                  "WHERE stars < 5\n"
                  "  AND hotel_id IN (SELECT hotel_id FROM hotel_scores WHERE avg_score >= 4.1 AND reviews >= 600);\n"
                  "UPDATE hotels SET stars = stars - 1\n"
                  "WHERE stars > 2\n"
                  "  AND hotel_id IN (SELECT hotel_id FROM hotel_scores WHERE avg_score < 3.78);"),
        trap_sql=("CREATE VIEW hotel_scores AS\n"
                  "SELECT r.hotel_id, COUNT(*) AS reviews, AVG(v.score) AS avg_score\n"
                  "FROM reviews v JOIN bookings b ON b.booking_id = v.booking_id\n"
                  "  JOIN rooms r ON r.room_id = b.room_id\n"
                  "GROUP BY r.hotel_id;\n"
                  "UPDATE hotels SET stars = stars + 1\n"
                  "WHERE stars < 5\n"
                  "  AND hotel_id IN (SELECT hotel_id FROM hotel_scores WHERE avg_score >= 4.1);\n"
                  "UPDATE hotels SET stars = stars - 1\n"
                  "WHERE stars > 2\n"
                  "  AND hotel_id IN (SELECT hotel_id FROM hotel_scores WHERE avg_score < 3.78);"),
        probe_sql=("SELECT h.hotel_id, h.stars, s.reviews, ROUND(s.avg_score, 3) FROM hotels h"
                   " JOIN hotel_scores s ON s.hotel_id = h.hotel_id"),
        note="The view is written once -- three tables joined,"
             " grouped by hotel, two aggregates with names -- and"
             " after that hotel_scores is read like a table of eight"
             " rows. Each UPDATE filters it with a WHERE of its own,"
             " and the conditions divide between the two tables:"
             " avg_score and reviews are columns of the view, stars"
             " is a column of hotels. Castle View alone gains a star:"
             " 4.115 from 723 reviews. Lakeside Lodge scores 4.193 but"
             " has 513 reviews, and the trap, which drops the 600,"
             " promotes it as well. Spa Gardens, at 4.60, is held at"
             " 5 by stars < 5; leave that out and the CHECK stops the"
             " statement, a loud failure where the missing 600 is a"
             " silent one. The Old Mill and Station House lose a"
             " star; Abbey Steps and Fellfoot Inn score lower still"
             " but are at 2 already.",
        claims=[("Castle View rises to 5 stars; Lakeside Lodge, with 513 reviews, stays at 4",
                 lambda rows, c: (1, 5, 723, 4.115) in rows and (7, 4, 513, 4.193) in rows),
                ("The Old Mill, at 3.777, and Station House fall to 2; Harbour Lights, at 3.794, keeps its 3",
                 lambda rows, c: (2, 2, 359, 3.777) in rows and (6, 2, 401, 3.753) in rows
                 and (3, 3, 535, 3.794) in rows),
                ("the stars of the eight hotels now add up to 25",
                 lambda rows, c: len(rows) == 8 and sum(r[1] for r in rows) == 25)],
    ),
    dict(
        id=15, ledger="Q1401", concept="UNIQUE", tier="5 - Procedures",
        kind="script",
        title="Two rules the database keeps by itself",
        prompt=(
            "Three steps. Rule one: no two guests share an email. One"
            " address is on two guests today, so first set email to"
            " NULL on every guest for whom ANOTHER guest exists with"
            " the same email and a lower guest_id -- a row compared"
            " with the rest of its own table, the self-join's idea"
            " inside an UPDATE. Then CREATE UNIQUE INDEX on the email"
            " column of guests; NULLs never count as equal, so guests"
            " with no email do not collide. Rule two: a room cannot"
            " have two LIVE bookings (status 'booked' or 'stayed')"
            " arriving on the same day. Cancelled bookings and"
            " no-shows often share a room and a day with a live one,"
            " so this unique index, on room_id and check_in together,"
            " needs a WHERE of its own: a partial index. The question"
            " then runs six statements, three of which the rules must"
            " refuse.\n\n"
            "Checked: guests, emails and different emails; the test"
            " guests who got in; room 170's bookings for 2026-07-19"
            " by status"
        ),
        solution=("UPDATE guests SET email = NULL\n"
                  "WHERE EXISTS (SELECT 1 FROM guests o\n"
                  "              WHERE o.email = guests.email AND o.guest_id < guests.guest_id);\n"
                  "CREATE UNIQUE INDEX guests_email ON guests (email);\n"
                  "CREATE UNIQUE INDEX one_live_booking ON bookings (room_id, check_in)\n"
                  "WHERE status IN ('booked', 'stayed');"),
        trap_sql=("UPDATE guests SET email = NULL\n"
                  "WHERE email IN (SELECT email FROM guests GROUP BY email HAVING COUNT(*) > 1);\n"
                  "CREATE UNIQUE INDEX guests_email ON guests (email);\n"
                  "CREATE UNIQUE INDEX one_live_booking ON bookings (room_id, check_in)\n"
                  "WHERE status IN ('booked', 'stayed');"),
        driver_sql=("INSERT INTO guests (name, country, email, joined_on)"
                    " VALUES ('Nora Quill', 'GB', 'mei.nightingale82@example.net', '2026-06-30');\n"
                    "INSERT INTO guests (name, country, email, joined_on)"
                    " VALUES ('Owen Reed', 'IE', NULL, '2026-06-30');\n"
                    "INSERT INTO guests (name, country, email, joined_on)"
                    " VALUES ('Petra Stone', 'DE', 'petra.stone@example.org', '2026-06-30');\n"
                    "INSERT INTO bookings (guest_id, room_id, booked_at, check_in, check_out, adults, children,"
                    " channel, rate_cents, status, cancelled_at)"
                    " VALUES (12, 170, '2026-06-30 10:00', '2026-07-19', '2026-07-21', 2, 0, 'phone', 6100,"
                    " 'booked', NULL);\n"
                    "INSERT INTO bookings (guest_id, room_id, booked_at, check_in, check_out, adults, children,"
                    " channel, rate_cents, status, cancelled_at)"
                    " VALUES (12, 170, '2026-06-30 10:05', '2026-07-19', '2026-07-21', 2, 0, 'phone', 6100,"
                    " 'cancelled', '2026-06-30 11:00');\n"
                    "UPDATE bookings SET status = 'booked', cancelled_at = NULL"
                    " WHERE room_id = 170 AND check_in = '2026-07-19' AND status = 'cancelled';"),
        probe_sql=("SELECT 'guests', COUNT(*), COUNT(email), COUNT(DISTINCT email) FROM guests"
                   " UNION ALL SELECT 'test guests', COUNT(*), COUNT(email), NULL FROM guests"
                   " WHERE name IN ('Nora Quill', 'Owen Reed', 'Petra Stone')"
                   " UNION ALL SELECT status, COUNT(*), NULL, NULL FROM bookings"
                   " WHERE room_id = 170 AND check_in = '2026-07-19' GROUP BY status"),
        note="A unique index is a constraint added after the table"
             " was made: from then on the database refuses any INSERT"
             " or UPDATE that would make two rows alike in the"
             " indexed columns. It cannot be created while"
             " duplicates exist, which is why the tidying comes"
             " first. EXISTS asks, for each guest, whether another"
             " row has the same email and a LOWER id; that is true of"
             " guest 1502 and not of guest 870, so exactly one"
             " address is cleared. The trap finds the shared email"
             " with GROUP BY and HAVING and clears every row that has"
             " it -- both guests lose the address, 1,320 emails left"
             " where there should be 1,321 after the test. The"
             " partial index only sees rows that pass its WHERE, so"
             " the 655 room-days that a cancelled booking shares"
             " with another are no obstacle. The six tests: an email"
             " already taken is refused, a NULL email and a new one"
             " go in; a second live booking for room 170 on 19 July"
             " is refused, a cancelled one goes in, and bringing it"
             " back to life is refused.",
        claims=[("1,602 guests with 1,321 emails, all different: Nora Quill was refused",
                 lambda rows, c: ("guests", 1602, 1321, 1321) in rows and ("test guests", 2, 1, None) in rows),
                ("room 170 on 19 July has one live booking and one cancelled",
                 lambda rows, c: sorted(r[:2] for r in rows if r[0] in ("booked", "cancelled", "stayed", "no_show"))
                 == [("booked", 1), ("cancelled", 1)])],
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
