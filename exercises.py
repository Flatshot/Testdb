"""Practice exercises: fifteen questions on the hotel-group schema.

The second set on the hotel schema (SEED 1356): eight hotels, their
rooms, guests, bookings, the extras charged to a stay, the payments made
against it and the reviews left afterwards. Nine questions read and six
change the data, the last three of them procedures. Ten of the fifteen
use a tool these tables have not met; five bring back what the first set
found hard -- the overlap of two ranges, EXISTS, arithmetic done row by
row before it is summed, a subquery that feeds an UPDATE -- in a
different task. The prompts name the tool but do not write the
statement. Rooms and what they cost -- the dearest rooms of each hotel
by RANK, rooms free for given nights by NOT EXISTS over an overlap, every
room with its stays in a week by an outer join whose conditions sit in
the ON. Guests over time -- the gap between one stay and the next by
LAG, guests banded by how often they stay by a CTE grouped twice, guests
who came and did not return by EXISTS beside NOT EXISTS. Money in and
out -- discounts as a sum of nights times a gap, extras and payments
side by side without counting either twice, a running total laid over a
grouped query.

Changing rows, three single statements:

  * an upsert: one INSERT that adds a review or updates the one there
  * an UPDATE whose new value is a correlated subquery
  * a DELETE that keeps the latest of each group by ROW_NUMBER

Procedures, three scripts of several steps. SQLite has no CREATE
PROCEDURE; what it has is a transaction, whose steps stand or fall
together, and a trigger body, which is stored and runs when called:

  * two records of one guest merged, in the order foreign keys allow
  * an early departure: the stay shortened, then the balance paid
  * a log table and the AFTER UPDATE trigger that fills it

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

_JUNE = ("b.status = 'stayed' AND b.check_out >= '2026-06-01' AND b.check_out <= '2026-06-30'")
_STAYS_2026 = ("b.room_id = rooms.room_id AND b.status = 'stayed' AND b.check_in >= '2026-01-01'")

EXERCISES = [
    # ======================================== 1 Rooms and what they cost
    dict(
        id=1, ledger="Q1357", concept="DEAREST", tier="1 - Rooms and what they cost",
        title="The two dearest rooms in each hotel",
        prompt=(
            "For each hotel, by name, its dearest rooms by list price"
            " (rack_cents). A room is listed when fewer than two rooms"
            " of its own hotel cost more than it does, so rooms tied on"
            " price share a place and a hotel can show more than two."
            " Give each room its place. A ranking window function,"
            " started afresh for each hotel; what a window produces"
            " cannot be tested in the WHERE of the same SELECT.\n\n"
            "Return: hotel, room_no, rack_cents, place"
        ),
        solution=("SELECT h.name, x.room_no, x.rack_cents, x.place FROM"
                  " (SELECT r.hotel_id, r.room_no, r.rack_cents,"
                  " RANK() OVER (PARTITION BY r.hotel_id ORDER BY r.rack_cents DESC) AS place FROM rooms r) x"
                  " JOIN hotels h ON h.hotel_id = x.hotel_id WHERE x.place <= 2"),
        trap_sql=("SELECT h.name, x.room_no, x.rack_cents, x.place FROM"
                  " (SELECT r.hotel_id, r.room_no, r.rack_cents,"
                  " ROW_NUMBER() OVER (PARTITION BY r.hotel_id ORDER BY r.rack_cents DESC) AS place FROM rooms r) x"
                  " JOIN hotels h ON h.hotel_id = x.hotel_id WHERE x.place <= 2"),
        note="PARTITION BY restarts the count for each hotel and ORDER"
             " BY says what first means. RANK gives equal prices the"
             " same place and then skips, so 'place <= 2' is exactly"
             " 'fewer than two rooms cost more'. ROW_NUMBER, the trap,"
             " never ties: at The Old Mill three rooms share second"
             " place at 9,600 and it keeps one of them, whichever it"
             " met first, and at Abbey Steps it calls one of two equal"
             " rooms second. A window is worked out after WHERE, which"
             " is why the filter sits in an outer query.",
        claims=[("eighteen rooms, four of them at The Old Mill",
                 lambda rows, c: len(rows) == 18 and sum(r[0] == "The Old Mill" for r in rows) == 4),
                ("Abbey Steps has two rooms in first place at 6,700 and none in second",
                 lambda rows, c: sorted(r[1:] for r in rows if r[0] == "Abbey Steps")
                 == [("202", 6700, 1), ("206", 6700, 1)])],
    ),
    dict(
        id=2, ledger="Q1358", concept="FREE", tier="1 - Rooms and what they cost",
        title="Rooms free for four nights in July",
        prompt=(
            "A guest wants four nights, arriving 2026-07-10 and leaving"
            " 2026-07-14. For each hotel still trading (closed_on is"
            " NULL), by name: how many of its rooms are free for the"
            " whole stay, and the lowest list price among those. A room"
            " is free when no booking of it that is not cancelled"
            " overlaps those nights; someone leaving on the 10th or"
            " arriving on the 14th is not in the way. NOT EXISTS, with"
            " the overlap test inside it.\n\n"
            "Return: hotel, free_rooms, cheapest_cents"
        ),
        solution=("SELECT h.name, COUNT(*), MIN(r.rack_cents) FROM rooms r JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " WHERE h.closed_on IS NULL AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.room_id = r.room_id"
                  " AND b.status <> 'cancelled' AND b.check_in < '2026-07-14' AND '2026-07-10' < b.check_out)"
                  " GROUP BY h.hotel_id"),
        trap_sql=("SELECT h.name, COUNT(*), MIN(r.rack_cents) FROM rooms r JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " WHERE h.closed_on IS NULL AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.room_id = r.room_id"
                  " AND b.check_in < '2026-07-14' AND '2026-07-10' < b.check_out)"
                  " GROUP BY h.hotel_id"),
        note="The same overlap test as before, with the wanted stay as"
             " one of the two ranges: the booking starts before the"
             " guest would leave AND the guest would arrive before the"
             " booking ends. NOT EXISTS turns 'no such booking' into"
             " 'free'. The trap lets cancelled bookings block rooms"
             " they no longer hold and loses eight free rooms, three"
             " of them at Castle View, where the cheapest one on offer"
             " becomes 9,050 when it is really 7,400. Abbey Steps has"
             " twelve empty rooms and no door to open, hence the"
             " closed_on test.",
        claims=[("seven hotels, 35 free rooms between them",
                 lambda rows, c: len(rows) == 7 and sum(r[1] for r in rows) == 35),
                ("Castle View has six, from 7,400 cents",
                 lambda rows, c: ("Castle View", 6, 7400) in rows)],
    ),
    dict(
        id=3, ledger="Q1359", concept="WEEK", tier="1 - Rooms and what they cost",
        title="Every room at Fellfoot Inn, busy or not",
        prompt=(
            "Fellfoot Inn is hotel 8. For every one of its rooms: the"
            " room number, the kind, and how many stays (status"
            " 'stayed') BEGAN in the first week of June 2026, the 1st"
            " to the 7th. A room with none is listed with 0, not left"
            " out. An outer join -- and think about where the"
            " conditions on the booking have to be written for a room"
            " with no match to survive them.\n\n"
            "Return: room_no, kind, stays"
        ),
        solution=("SELECT r.room_no, r.kind, COUNT(b.booking_id) FROM rooms r"
                  " LEFT JOIN bookings b ON b.room_id = r.room_id AND b.status = 'stayed'"
                  " AND b.check_in >= '2026-06-01' AND b.check_in < '2026-06-08'"
                  " WHERE r.hotel_id = 8 GROUP BY r.room_id"),
        trap_sql=("SELECT r.room_no, r.kind, COUNT(b.booking_id) FROM rooms r"
                  " LEFT JOIN bookings b ON b.room_id = r.room_id"
                  " WHERE r.hotel_id = 8 AND b.status = 'stayed'"
                  " AND b.check_in >= '2026-06-01' AND b.check_in < '2026-06-08' GROUP BY r.room_id"),
        note="ON decides which bookings may match a room; WHERE"
             " decides which joined rows are kept afterwards. A room"
             " with no stay that week comes out of the LEFT JOIN with"
             " NULL in every booking column, and a WHERE that tests"
             " b.status or b.check_in throws that row away again --"
             " the outer join has been turned back into an inner one."
             " The trap lists ten rooms and no zeros. The condition on"
             " the room itself, hotel_id = 8, is about the kept side"
             " and belongs in WHERE.",
        claims=[("fourteen rooms, four of them with no stay that week",
                 lambda rows, c: len(rows) == 14 and sum(r[2] == 0 for r in rows) == 4),
                ("room 202, a twin, had two",
                 lambda rows, c: ("202", "twin", 2) in rows)],
    ),
    # ================================================ 2 Guests over time
    dict(
        id=4, ledger="Q1360", concept="GAP", tier="2 - Guests over time",
        title="How long between one stay and the next",
        prompt=(
            "Guest 306 has stayed seven times. For each of those stays"
            " (status 'stayed'): its check-in, its check-out, and the"
            " whole number of days from the PREVIOUS stay's check-out"
            " to this check-in -- NULL for the first, which has"
            " nothing before it. LAG reads a column from the row"
            " before, in an order you give it.\n\n"
            "Return: check_in, check_out, days_since_last"
        ),
        solution=("SELECT check_in, check_out,"
                  " CAST(julianday(check_in) - julianday(LAG(check_out) OVER (ORDER BY check_in)) AS INTEGER)"
                  " FROM bookings WHERE guest_id = 306 AND status = 'stayed'"),
        trap_sql=("SELECT check_in, check_out,"
                  " CAST(julianday(check_in) - julianday(LAG(check_out) OVER (ORDER BY check_in)) AS INTEGER)"
                  " FROM bookings WHERE guest_id = 306"),
        note="LAG(check_out) OVER (ORDER BY check_in) is 'the check_out"
             " of the row before this one when the rows are put in"
             " order of arrival'. The first row has no row before it,"
             " so LAG gives NULL and the subtraction stays NULL. The"
             " window sees only the rows WHERE lets through: the trap"
             " leaves in two bookings from April 2026 that were"
             " cancelled, and measures May's stay from a departure"
             " that never happened -- 27 days where the true gap is"
             " 151.",
        claims=[("seven stays, the first with no gap",
                 lambda rows, c: len(rows) == 7 and ("2025-01-04", "2025-01-08", None) in rows),
                ("151 days before the stay of May 2026",
                 lambda rows, c: ("2026-05-21", "2026-05-28", 151) in rows)],
    ),
    dict(
        id=5, ledger="Q1361", concept="BANDS", tier="2 - Guests over time",
        title="Once, a few times, or a regular",
        prompt=(
            "Count each guest's stays (status 'stayed'), then count the"
            " guests. Put each guest in a band by their number of"
            " stays -- 'once' for 1, '2 to 5', '6 to 15', 'over 15' --"
            " and for each band give how many guests are in it and how"
            " many stays they made between them. A guest with no stay"
            " is in no band. Two levels of grouping: a CTE for the"
            " first, and a query over it for the second.\n\n"
            "Return: band, guests, stays"
        ),
        solution=("WITH per_guest AS (SELECT guest_id, COUNT(*) AS stays FROM bookings"
                  " WHERE status = 'stayed' GROUP BY guest_id)"
                  " SELECT CASE WHEN stays = 1 THEN 'once' WHEN stays <= 5 THEN '2 to 5'"
                  " WHEN stays <= 15 THEN '6 to 15' ELSE 'over 15' END AS band, COUNT(*), SUM(stays)"
                  " FROM per_guest GROUP BY band"),
        trap_sql=("WITH per_guest AS (SELECT guest_id, COUNT(*) AS stays FROM bookings"
                  " GROUP BY guest_id)"
                  " SELECT CASE WHEN stays = 1 THEN 'once' WHEN stays <= 5 THEN '2 to 5'"
                  " WHEN stays <= 15 THEN '6 to 15' ELSE 'over 15' END AS band, COUNT(*), SUM(stays)"
                  " FROM per_guest GROUP BY band"),
        note="One query cannot count the stays of a guest and then"
             " count the guests with that count: the second grouping"
             " needs the first one's result as its rows. The CTE gives"
             " that result a name, one row per guest, and the outer"
             " query treats it as a table. CASE takes the first branch"
             " that is true, so each band needs only its upper end."
             " The trap counts every booking, cancelled and future"
             " ones too, and moves nearly half the '2 to 5' guests into"
             " the band above.",
        claims=[("four bands; 24 guests have stayed exactly once",
                 lambda rows, c: len(rows) == 4 and ("once", 24, 24) in rows),
                ("1,501 guests and 13,625 stays in all",
                 lambda rows, c: sum(r[1] for r in rows) == 1501 and sum(r[2] for r in rows) == 13625)],
    ),
    dict(
        id=6, ledger="Q1362", concept="LAPSED", tier="2 - Guests over time",
        title="Came in 2025 and have not been back",
        prompt=(
            "A guest has LAPSED when they stayed in 2025 -- a booking"
            " with status 'stayed' that began in that year -- and have"
            " nothing from 2026 on: no booking beginning on or after"
            " 2026-01-01 whose status is 'stayed' or 'booked'. A"
            " cancelled booking or a no-show is not a return. How many"
            " lapsed guests are there in each loyalty tier, with the"
            " guests in no tier (NULL) as a group of their own? One"
            " EXISTS and one NOT EXISTS.\n\n"
            "Return: tier, lapsed"
        ),
        solution=("SELECT g.tier, COUNT(*) FROM guests g WHERE EXISTS (SELECT 1 FROM bookings b"
                  " WHERE b.guest_id = g.guest_id AND b.status = 'stayed'"
                  " AND b.check_in >= '2025-01-01' AND b.check_in < '2026-01-01')"
                  " AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.guest_id = g.guest_id"
                  " AND b.status IN ('stayed', 'booked') AND b.check_in >= '2026-01-01') GROUP BY g.tier"),
        trap_sql=("SELECT g.tier, COUNT(*) FROM guests g WHERE EXISTS (SELECT 1 FROM bookings b"
                  " WHERE b.guest_id = g.guest_id AND b.status = 'stayed'"
                  " AND b.check_in >= '2025-01-01' AND b.check_in < '2026-01-01')"
                  " AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.guest_id = g.guest_id"
                  " AND b.check_in >= '2026-01-01') GROUP BY g.tier"),
        note="Each EXISTS is its own question about the guest, with"
             " its own copy of bookings, and the two are joined by AND:"
             " there is a 2025 stay, and there is no live booking"
             " after it. Written this way a guest is counted once"
             " however many bookings they have, which a join would"
             " not promise. The trap forgets the status in the second"
             " test, so a guest who booked for 2026 and cancelled"
             " counts as having come back: 52 lapsed where there are"
             " 68. GROUP BY puts the NULL tiers together as one"
             " group.",
        claims=[("three groups, 68 lapsed guests in all",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 68),
                ("54 of them are in no tier and 3 are gold",
                 lambda rows, c: (None, 54) in rows and ("gold", 3) in rows)],
    ),
    # ================================================= 3 Money in and out
    dict(
        id=7, ledger="Q1363", concept="DISCOUNT", tier="3 - Money in and out",
        title="What each channel gives away",
        prompt=(
            "A stay is discounted when the rate agreed for it is below"
            " the room's list price. For each channel, among stays"
            " (status 'stayed'): how many were discounted, and the"
            " total given away, as a whole number of cents -- for one"
            " stay, the gap between list price and rate on every night"
            " it lasted. The amount is worked out for each row, and"
            " the sum is taken over that.\n\n"
            "Return: channel, discounted_stays, discount_cents"
        ),
        solution=("SELECT b.channel, COUNT(*), CAST(SUM((r.rack_cents - b.rate_cents)"
                  " * (julianday(b.check_out) - julianday(b.check_in))) AS INTEGER)"
                  " FROM bookings b JOIN rooms r ON r.room_id = b.room_id"
                  " WHERE b.status = 'stayed' AND b.rate_cents < r.rack_cents GROUP BY b.channel"),
        trap_sql=("SELECT b.channel, COUNT(*), SUM(r.rack_cents - b.rate_cents)"
                  " FROM bookings b JOIN rooms r ON r.room_id = b.room_id"
                  " WHERE b.status = 'stayed' AND b.rate_cents < r.rack_cents GROUP BY b.channel"),
        note="The expression inside SUM is evaluated once per row, with"
             " that row's own prices and nights, and the results are"
             " added: a sum of products. It is not the product of two"
             " sums, and nothing has to be added up before the"
             " multiplying. The trap adds the nightly gap once per"
             " stay as if every stay were one night, and understates"
             " the web channel's 17.65 million cents as 5.6 million."
             " Whether a"
             " stay is discounted at all is a comparison of two"
             " columns from two tables, in WHERE.",
        claims=[("four channels, 9,408 discounted stays",
                 lambda rows, c: len(rows) == 4 and sum(r[1] for r in rows) == 9408),
                ("the web gave away 17,650,000 cents over 5,109 stays",
                 lambda rows, c: ("web", 5109, 17650000) in rows)],
    ),
    dict(
        id=8, ledger="Q1364", concept="TWOSUMS", tier="3 - Money in and out",
        title="Extras and payments, side by side",
        prompt=(
            "For each hotel, by name, taking the stays (status"
            " 'stayed') that checked out in June 2026: how many stays,"
            " the total of their extras (charges), and the total paid"
            " against them (payments, a refund counting as negative)."
            " A booking has several charges AND several payments;"
            " joined to both at once, every charge is repeated for"
            " every payment. Add each one up on its own before it"
            " meets the booking, and count a booking with no charges"
            " as 0.\n\n"
            "Return: hotel, stays, extras_cents, paid_cents"
        ),
        solution=("WITH c AS (SELECT booking_id, SUM(amount_cents) AS cents FROM charges GROUP BY booking_id),"
                  " p AS (SELECT booking_id, SUM(amount_cents) AS cents FROM payments GROUP BY booking_id)"
                  " SELECT h.name, COUNT(*), SUM(COALESCE(c.cents, 0)), SUM(COALESCE(p.cents, 0))"
                  " FROM bookings b JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " LEFT JOIN c ON c.booking_id = b.booking_id LEFT JOIN p ON p.booking_id = b.booking_id"
                  " WHERE " + _JUNE + " GROUP BY h.hotel_id"),
        trap_sql=("SELECT h.name, COUNT(DISTINCT b.booking_id), COALESCE(SUM(c.amount_cents), 0),"
                  " COALESCE(SUM(p.amount_cents), 0)"
                  " FROM bookings b JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " LEFT JOIN charges c ON c.booking_id = b.booking_id"
                  " LEFT JOIN payments p ON p.booking_id = b.booking_id"
                  " WHERE " + _JUNE + " GROUP BY h.hotel_id"),
        note="Charges and payments are both children of a booking and"
             " know nothing of each other. Join both and a booking"
             " with five charges and two payments becomes ten rows:"
             " each charge counted twice, each payment five times."
             " COUNT(DISTINCT) hides the damage in the first column,"
             " which is what makes the trap convincing -- 173 stays at"
             " Spa Gardens, and 66 million cents paid where 9.7"
             " million were. Folding each child to one row per booking"
             " first means every join after that is one to one.",
        claims=[("seven hotels, 785 stays",
                 lambda rows, c: len(rows) == 7 and sum(r[1] for r in rows) == 785),
                ("Spa Gardens: 173 stays, 2,548,990 in extras, 9,714,140 paid",
                 lambda rows, c: ("Spa Gardens", 173, 2548990, 9714140) in rows)],
    ),
    dict(
        id=9, ledger="Q1365", concept="RUNNING", tier="3 - Money in and out",
        title="The year's takings as they mounted up",
        prompt=(
            "Take the payments made in 2025 (paid_at in that year),"
            " refunds included as the negatives they are. For each"
            " month, written 'YYYY-MM': the net amount taken in the"
            " month, and the running total for the year up to and"
            " including it. strftime cuts the month out of a"
            " timestamp; a window with an ORDER BY adds up as it"
            " goes, and it can be laid over the result of a GROUP"
            " BY.\n\n"
            "Return: month, taken_cents, running_cents"
        ),
        solution=("SELECT strftime('%Y-%m', paid_at) AS month, SUM(amount_cents),"
                  " SUM(SUM(amount_cents)) OVER (ORDER BY strftime('%Y-%m', paid_at))"
                  " FROM payments WHERE paid_at >= '2025-01-01' AND paid_at < '2026-01-01' GROUP BY month"),
        trap_sql=("SELECT strftime('%Y-%m', paid_at) AS month, SUM(amount_cents),"
                  " SUM(SUM(amount_cents)) OVER ()"
                  " FROM payments WHERE paid_at >= '2025-01-01' AND paid_at < '2026-01-01' GROUP BY month"),
        note="GROUP BY runs first and leaves twelve rows; the window"
             " then runs over those rows. That is why the inner SUM is"
             " the month's total and the outer SUM ... OVER adds the"
             " monthly totals together. With ORDER BY in the OVER the"
             " window for each row is 'everything up to here'; with"
             " empty brackets, the trap, it is everything, and all"
             " twelve rows show December's figure. A CTE of monthly"
             " totals with the window over it says the same thing in"
             " two steps.",
        claims=[("twelve months; January took 18,857,710 and that is its running total too",
                 lambda rows, c: len(rows) == 12 and ("2025-01", 18857710, 18857710) in rows),
                ("the year ends on 352,148,650",
                 lambda rows, c: ("2025-12", 31520610, 352148650) in rows)],
    ),
    # ==================================================== 4 Changing rows
    dict(
        id=10, ledger="Q1366", concept="REPOST", tier="4 - Changing rows",
        kind="script",
        title="A review posted, or posted again",
        prompt=(
            "Two guests post reviews on 2026-07-01. Booking 16876"
            " already has one -- 3, 'Fine for one night' -- and its"
            " guest now gives 5 with the headline 'Better on"
            " reflection'. Booking 15266 has none; its guest gives 4,"
            " 'Lovely view of the lake'. reviews allows one review per"
            " booking: booking_id is UNIQUE. In ONE INSERT of both"
            " rows, a review that is new is added and one that exists"
            " is changed in place -- score, posted_on and headline --"
            " keeping its review_id. The upsert clause of INSERT; in"
            " it the row that could not go in is called excluded.\n\n"
            "Checked: the two bookings' reviews with their ids, and"
            " how many reviews there are"
        ),
        solution=("INSERT INTO reviews (booking_id, score, posted_on, headline)\n"
                  "VALUES (16876, 5, '2026-07-01', 'Better on reflection'),\n"
                  "       (15266, 4, '2026-07-01', 'Lovely view of the lake')\n"
                  "ON CONFLICT (booking_id) DO UPDATE\n"
                  "SET score = excluded.score, posted_on = excluded.posted_on, headline = excluded.headline;"),
        trap_sql=("INSERT OR REPLACE INTO reviews (booking_id, score, posted_on, headline)\n"
                  "VALUES (16876, 5, '2026-07-01', 'Better on reflection'),\n"
                  "       (15266, 4, '2026-07-01', 'Lovely view of the lake');"),
        probe_sql=("SELECT review_id, booking_id, score, posted_on, headline,"
                   " (SELECT COUNT(*) FROM reviews) FROM reviews WHERE booking_id IN (16876, 15266)"),
        note="ON CONFLICT names the UNIQUE or PRIMARY KEY columns whose"
             " clash it is prepared for -- it must match a real"
             " constraint, which is why it was an error on charges in"
             " the last set and works here. DO UPDATE then changes the"
             " row already there, and excluded.score is the value the"
             " INSERT was trying to store. INSERT OR REPLACE, the"
             " trap, looks the same from a distance but DELETES the"
             " old row and inserts a new one: review 3530 comes back"
             " as 3555, and anything that pointed at the old id would"
             " be left pointing at nothing.",
        claims=[("review 3530 now says 5, the new one is 3555, and there are 3,555 reviews",
                 lambda rows, c: sorted(rows) == [
                     (3530, 16876, 5, "2026-07-01", "Better on reflection", 3555),
                     (3555, 15266, 4, "2026-07-01", "Lovely view of the lake", 3555)])],
    ),
    dict(
        id=11, ledger="Q1367", concept="REPRICE", tier="4 - Changing rows",
        kind="script",
        title="List prices reset to what guests paid",
        prompt=(
            "Spa Gardens (hotel 5) resets its list prices. Each of its"
            " rooms gets as rack_cents the average rate_cents of that"
            " room's OWN stays (status 'stayed') that began in 2026,"
            " rounded to a whole number of cents. A room with no such"
            " stay keeps the price it has -- there is one. One UPDATE,"
            " whose new value is a subquery that looks back at the row"
            " being updated.\n\n"
            "Checked: for Spa Gardens and for the other hotels taken"
            " together: rooms, the total, lowest and highest list"
            " price, and how many different prices"
        ),
        solution=("UPDATE rooms\n"
                  "SET rack_cents = (SELECT ROUND(AVG(b.rate_cents)) FROM bookings b\n"
                  "                  WHERE " + _STAYS_2026 + ")\n"
                  "WHERE hotel_id = 5\n"
                  "  AND EXISTS (SELECT 1 FROM bookings b\n"
                  "              WHERE " + _STAYS_2026 + ");"),
        trap_sql=("UPDATE rooms\n"
                  "SET rack_cents = (SELECT ROUND(AVG(b.rate_cents)) FROM bookings b\n"
                  "                  JOIN rooms r ON r.room_id = b.room_id\n"
                  "                  WHERE r.hotel_id = 5 AND b.status = 'stayed' AND b.check_in >= '2026-01-01')\n"
                  "WHERE hotel_id = 5;"),
        probe_sql=("SELECT hotel_id = 5, COUNT(*), SUM(rack_cents), MIN(rack_cents), MAX(rack_cents),"
                   " COUNT(DISTINCT rack_cents) FROM rooms GROUP BY hotel_id = 5"),
        note="Inside the SET subquery, rooms.room_id is the room the"
             " UPDATE is standing on, so the average is worked out"
             " afresh for each of them: a correlated subquery. Without"
             " that link, the trap, the subquery is one number for the"
             " whole hotel and every room from a single to the suite"
             " is priced at 12,724. The WHERE needs the same test"
             " again as an EXISTS: for room 312, which has never been"
             " let, the average of no rows is NULL, and rack_cents is"
             " NOT NULL.",
        claims=[("Spa Gardens: 36 rooms, the dearest still room 312 at 24,500",
                 lambda rows, c: any(r[0] == 1 and r[1] == 36 and r[4] == 24500 for r in rows)),
                ("the other 140 rooms are untouched",
                 lambda rows, c: any(r[0] == 0 and r[1] == 140 for r in rows))],
    ),
    dict(
        id=12, ledger="Q1368", concept="LATEST", tier="4 - Changing rows",
        kind="script",
        title="One review per guest per hotel",
        prompt=(
            "The site will show only a guest's most recent review of"
            " each hotel. Delete every review that is not the latest"
            " one its guest has posted for that hotel; where two were"
            " posted on the same day, the one with the higher"
            " review_id is the later. A review reaches its guest"
            " through the booking and its hotel through the room. One"
            " DELETE; ROW_NUMBER, started afresh for each guest and"
            " hotel, numbers the reviews so that the ones to go can be"
            " picked out.\n\n"
            "Checked: the reviews left: how many, their scores added"
            " up, their ids added up, and the earliest posted"
        ),
        solution=("DELETE FROM reviews WHERE review_id IN (\n"
                  "  SELECT review_id FROM (\n"
                  "    SELECT v.review_id, ROW_NUMBER() OVER (\n"
                  "             PARTITION BY b.guest_id, r.hotel_id\n"
                  "             ORDER BY v.posted_on DESC, v.review_id DESC) AS n\n"
                  "    FROM reviews v\n"
                  "    JOIN bookings b ON b.booking_id = v.booking_id\n"
                  "    JOIN rooms r ON r.room_id = b.room_id)\n"
                  "  WHERE n > 1);"),
        trap_sql=("DELETE FROM reviews WHERE review_id IN (\n"
                  "  SELECT review_id FROM (\n"
                  "    SELECT v.review_id, ROW_NUMBER() OVER (\n"
                  "             PARTITION BY b.guest_id\n"
                  "             ORDER BY v.posted_on DESC, v.review_id DESC) AS n\n"
                  "    FROM reviews v\n"
                  "    JOIN bookings b ON b.booking_id = v.booking_id)\n"
                  "  WHERE n > 1);"),
        probe_sql="SELECT COUNT(*), SUM(score), SUM(review_id), MIN(posted_on) FROM reviews",
        note="Numbered newest first within each guest and hotel, the"
             " review to keep is always number 1 and everything else"
             " is a duplicate, however many there are. Here ROW_NUMBER"
             " is the right function and RANK would be the wrong one:"
             " exactly one row must survive, and the second ORDER BY"
             " column settles the two pairs posted on the same day."
             " The trap partitions by guest alone and keeps one review"
             " per person across the whole group -- 2,322 deleted"
             " where 794 should be.",
        claims=[("2,760 reviews are left of 3,554",
                 lambda rows, c: len(rows) == 1 and rows[0][0] == 2760)],
    ),
    # ======================================================= 5 Procedures
    dict(
        id=13, ledger="Q1369", concept="MERGE", tier="5 - Procedures",
        kind="script",
        title="One guest, entered twice",
        prompt=(
            "Benedict Bianchi is on the books twice. Guest 1425 is the"
            " older record, with the gold tier and no email; guest"
            " 1218 has an email and twelve bookings. Make them one,"
            " keeping 1425. In ONE transaction: 1425 takes 1218's"
            " email -- read it, do not type it -- every booking of"
            " 1218 becomes 1425's, and 1218 is deleted. Foreign keys"
            " are enforced, so a guest who still has bookings cannot"
            " be deleted; and a deleted guest has no email left to"
            " read. The order of the three steps matters. The"
            " question then issues a ROLLBACK: committed work"
            " survives it.\n\n"
            "Checked: guest 1425's email and tier, how many bookings"
            " 1425 and 1218 hold, and how many guests are called"
            " Benedict Bianchi"
        ),
        solution=("BEGIN;\n"
                  "UPDATE guests SET email = (SELECT email FROM guests WHERE guest_id = 1218)\n"
                  "WHERE guest_id = 1425;\n"
                  "UPDATE bookings SET guest_id = 1425 WHERE guest_id = 1218;\n"
                  "DELETE FROM guests WHERE guest_id = 1218;\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE bookings SET guest_id = 1425 WHERE guest_id = 1218;\n"
                  "DELETE FROM guests WHERE guest_id = 1218;\n"
                  "UPDATE guests SET email = (SELECT email FROM guests WHERE guest_id = 1218)\n"
                  "WHERE guest_id = 1425;\n"
                  "COMMIT;"),
        driver_sql="ROLLBACK;",
        probe_sql=("SELECT g.email, g.tier,"
                   " (SELECT COUNT(*) FROM bookings WHERE guest_id = 1425),"
                   " (SELECT COUNT(*) FROM bookings WHERE guest_id = 1218),"
                   " (SELECT COUNT(*) FROM guests WHERE name = 'Benedict Bianchi')"
                   " FROM guests g WHERE g.guest_id = 1425"),
        note="Two of the three steps depend on row 1218 still being"
             " there: the email has to be read from it, and its"
             " bookings have to be pointed elsewhere before the"
             " foreign key will let it go. So the DELETE comes last."
             " Deleting before moving the bookings fails loudly;"
             " deleting before copying the email, the trap, fails"
             " silently -- a subquery that finds no row is NULL, the"
             " UPDATE stores that without complaint, and the only"
             " email the group had for this guest is gone. The"
             " transaction means nobody ever sees the half-merged"
             " state.",
        claims=[("1425 has the email, the gold tier and all eighteen bookings; one Benedict Bianchi is left",
                 lambda rows, c: rows == [("benedict.bianchi91@example.net", "gold", 18, 0, 1)])],
    ),
    dict(
        id=14, ledger="Q1370", concept="EARLY", tier="5 - Procedures",
        kind="script",
        title="Leaving early, and settling up",
        prompt=(
            "Booking 15170 is in the house at Castle View and due to"
            " leave on 2026-07-06. The guest leaves on 2026-07-01"
            " instead, and pays what is owed by card at 2026-07-01"
            " 10:30. In one transaction: bring check_out forward, and"
            " insert ONE payment for the balance -- the nights"
            " actually stayed at the booking's rate, plus its charges,"
            " less what has already been paid. Work the balance out"
            " in the INSERT from the tables; do not type it. One of"
            " the two steps reads what the other writes, so their"
            " order decides the amount.\n\n"
            "Checked: the booking's check-out, how many payments it"
            " has and what they add up to"
        ),
        solution=("BEGIN;\n"
                  "UPDATE bookings SET check_out = '2026-07-01' WHERE booking_id = 15170;\n"
                  "INSERT INTO payments (booking_id, paid_at, amount_cents, method)\n"
                  "SELECT b.booking_id, '2026-07-01 10:30',\n"
                  "       (julianday(b.check_out) - julianday(b.check_in)) * b.rate_cents\n"
                  "       + COALESCE((SELECT SUM(c.amount_cents) FROM charges c WHERE c.booking_id = b.booking_id), 0)\n"
                  "       - COALESCE((SELECT SUM(p.amount_cents) FROM payments p WHERE p.booking_id = b.booking_id), 0),\n"
                  "       'card'\n"
                  "FROM bookings b WHERE b.booking_id = 15170;\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "INSERT INTO payments (booking_id, paid_at, amount_cents, method)\n"
                  "SELECT b.booking_id, '2026-07-01 10:30',\n"
                  "       (julianday(b.check_out) - julianday(b.check_in)) * b.rate_cents\n"
                  "       + COALESCE((SELECT SUM(c.amount_cents) FROM charges c WHERE c.booking_id = b.booking_id), 0)\n"
                  "       - COALESCE((SELECT SUM(p.amount_cents) FROM payments p WHERE p.booking_id = b.booking_id), 0),\n"
                  "       'card'\n"
                  "FROM bookings b WHERE b.booking_id = 15170;\n"
                  "UPDATE bookings SET check_out = '2026-07-01' WHERE booking_id = 15170;\n"
                  "COMMIT;"),
        probe_sql=("SELECT b.check_out,"
                   " (SELECT COUNT(*) FROM payments p WHERE p.booking_id = b.booking_id),"
                   " (SELECT SUM(p.amount_cents) FROM payments p WHERE p.booking_id = b.booking_id)"
                   " FROM bookings b WHERE b.booking_id = 15170"),
        note="Last set a row had to be copied BEFORE it was changed;"
             " here the change has to come first, because the balance"
             " is worked out from the nights and the nights are"
             " check_out minus check_in. Shorten the stay, and the"
             " INSERT ... SELECT reads nine nights: 90,450 for the"
             " room, 40,900 in charges, less the 10,050 deposit,"
             " 121,300 to pay. The trap bills first and charges the"
             " guest for all fourteen nights, 50,250 too much. The"
             " two totals are scalar subqueries, each added up on its"
             " own, so neither multiplies the other.",
        claims=[("out on the 1st, two payments adding up to 131,350",
                 lambda rows, c: rows == [("2026-07-01", 2, 131350)])],
    ),
    dict(
        id=15, ledger="Q1371", concept="RATELOG", tier="5 - Procedures",
        kind="script",
        title="Who changed that price?",
        prompt=(
            "Keep a record of every change to a room's list price. Two"
            " statements. Create a table rate_log with three integer"
            " columns: room_id, old_cents and new_cents. Then store a"
            " trigger that, AFTER an UPDATE of rack_cents on rooms,"
            " writes one row to it -- but only when the price really"
            " changed: an UPDATE that sets a price to the value it"
            " already had is not a change. The question then runs"
            " three updates at Fellfoot Inn: its twins go up by 300"
            " cents; its three ground-floor singles are all set to"
            " 4,550, which two of them already are; and one room's"
            " sleeps is altered.\n\n"
            "Checked: the rows of rate_log"
        ),
        solution=("CREATE TABLE rate_log (\n"
                  "  room_id   INTEGER NOT NULL,\n"
                  "  old_cents INTEGER NOT NULL,\n"
                  "  new_cents INTEGER NOT NULL);\n"
                  "CREATE TRIGGER log_rate AFTER UPDATE OF rack_cents ON rooms\n"
                  "WHEN OLD.rack_cents <> NEW.rack_cents\n"
                  "BEGIN\n"
                  "  INSERT INTO rate_log (room_id, old_cents, new_cents)\n"
                  "  VALUES (OLD.room_id, OLD.rack_cents, NEW.rack_cents);\n"
                  "END;"),
        trap_sql=("CREATE TABLE rate_log (\n"
                  "  room_id   INTEGER NOT NULL,\n"
                  "  old_cents INTEGER NOT NULL,\n"
                  "  new_cents INTEGER NOT NULL);\n"
                  "CREATE TRIGGER log_rate AFTER UPDATE OF rack_cents ON rooms\n"
                  "BEGIN\n"
                  "  INSERT INTO rate_log (room_id, old_cents, new_cents)\n"
                  "  VALUES (OLD.room_id, OLD.rack_cents, NEW.rack_cents);\n"
                  "END;"),
        driver_sql=("UPDATE rooms SET rack_cents = rack_cents + 300 WHERE hotel_id = 8 AND kind = 'twin';\n"
                    "UPDATE rooms SET rack_cents = 4550 WHERE hotel_id = 8 AND kind = 'single' AND floor = 1;\n"
                    "UPDATE rooms SET sleeps = 3 WHERE room_id = 164;"),
        probe_sql="SELECT room_id, old_cents, new_cents FROM rate_log",
        note="In an UPDATE trigger OLD is the row as it was and NEW the"
             " row as it will be, and the body runs once for each row"
             " the statement touches -- four times for the twins."
             " UPDATE OF rack_cents fires when that column is in the"
             " SET list, whether or not its value moved, so the WHEN"
             " clause is what tells a change from a rewrite. The trap"
             " has no WHEN and logs rooms 166 and 167 going from 4,550"
             " to 4,550. The third update never names rack_cents and"
             " fires nothing. The log is an ordinary table, made"
             " first because the trigger's INSERT needs it.",
        claims=[("five changes: four twins up 300 and one single down to 4,550",
                 lambda rows, c: sorted(rows) == [(163, 5050, 4550), (170, 6100, 6400), (171, 5850, 6150),
                                                  (172, 6350, 6650), (176, 6350, 6650)])],
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
