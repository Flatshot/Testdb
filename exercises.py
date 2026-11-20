"""Practice exercises: fifteen questions on the hotel-group schema.

The first set on a NEW schema (SEED 1356): a small group of eight hotels,
their rooms, guests, bookings, the extras charged to a stay, the payments
made against it and the reviews left afterwards. Nine questions read and
six change the data, the last three of them procedures. Because the
tables are new the tools are the central ones, asked where a hotel makes
them matter, and the prompts name the tool but do not write the
statement. Finding your way around -- rooms and prices per hotel by a
join and GROUP BY, guests who never booked by LEFT JOIN, room-nights sold
by subtracting dates. Nights and dates -- who was in the house on a given
night by a half-open range, how far ahead each channel books by date()
on a timestamp, cancelled nights sold again by an overlap test. Money and
scores -- takings and refunds apart by conditional sums, extras per stay
with the stays that had none by a LEFT JOIN to an aggregate, the share of
stays reviewed by COUNT(column).

Changing rows, three single statements:

  * an INSERT ... SELECT that charges everyone in the house on one night
  * an UPDATE whose rows come from a grouped subquery with HAVING
  * a DELETE with NOT EXISTS and a date

Procedures, three scripts of several steps. SQLite has no CREATE
PROCEDURE; what it has is a transaction, whose steps stand or fall
together, and a trigger body, which is stored and runs when called:

  * a booking cancelled and its deposit refunded, two tables in one
    transaction
  * a stay split in two when the guest moved room, in the only order
    that works
  * a BEFORE INSERT trigger that refuses a double booking

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
    # ============================================ 1 Finding your way around
    dict(
        id=1, ledger="Q1342", concept="ROOMS", tier="1 - Finding your way around",
        title="What each hotel has to sell",
        prompt=(
            "For each hotel, by name: how many rooms it has, and the"
            " lowest and highest list price (rack_cents) among them."
            " Two hotels can share a town, so group by the hotel. One"
            " join and three aggregates.\n\n"
            "Return: hotel, rooms, cheapest_cents, dearest_cents"
        ),
        solution=("SELECT h.name, COUNT(*), MIN(r.rack_cents), MAX(r.rack_cents) FROM hotels h"
                  " JOIN rooms r ON r.hotel_id = h.hotel_id GROUP BY h.hotel_id"),
        trap_sql=("SELECT h.name, COUNT(*), MIN(r.rack_cents), MAX(r.rack_cents) FROM hotels h"
                  " JOIN rooms r ON r.hotel_id = h.hotel_id GROUP BY h.town"),
        note="The join gives one row per room with its hotel beside it,"
             " and GROUP BY folds those back to one row per hotel, with"
             " COUNT, MIN and MAX each looking at that hotel's rooms"
             " only. Group by town, the trap, and the four towns each"
             " merge two hotels: York becomes one 48-room hotel under"
             " whichever name SQLite happens to show. Grouping by the"
             " key, hotel_id, is safer than by name, though here the"
             " names are unique too.",
        claims=[("eight hotels, Spa Gardens the biggest with 36 rooms",
                 lambda rows, c: len(rows) == 8 and ("Spa Gardens", 36, 10000, 24500) in rows),
                ("Abbey Steps has twelve rooms from 4,550 to 6,700 cents",
                 lambda rows, c: ("Abbey Steps", 12, 4550, 6700) in rows)],
    ),
    dict(
        id=2, ledger="Q1343", concept="NEVER", tier="1 - Finding your way around",
        title="Guests on the books who have never booked",
        prompt=(
            "For each country: how many guests are on the books, and"
            " how many of them have never made a booking of any kind."
            " Start from guests and keep every one, booked or not: the"
            " outer join, whose unmatched rows carry NULLs you can"
            " count.\n\n"
            "Return: country, guests, never_booked"
        ),
        solution=("SELECT g.country, COUNT(DISTINCT g.guest_id), SUM(b.booking_id IS NULL) FROM guests g"
                  " LEFT JOIN bookings b ON b.guest_id = g.guest_id GROUP BY g.country"),
        trap_sql=("SELECT g.country, COUNT(DISTINCT g.guest_id), SUM(b.booking_id IS NULL) FROM guests g"
                  " JOIN bookings b ON b.guest_id = g.guest_id GROUP BY g.country"),
        note="A LEFT JOIN keeps every guest: one row per booking for"
             " those who have any, and a single row with NULLs in the"
             " booking columns for those who have none. Counting those"
             " NULL rows counts the guests who never booked, and"
             " COUNT(DISTINCT guest_id) counts people where COUNT(*)"
             " would count bookings. The inner join of the trap drops"
             " the never-booked before anything is counted: 96 guests"
             " vanish from the first column and the second is zero"
             " everywhere.",
        claims=[("eight countries, 1,089 guests from GB and 62 of them never booked",
                 lambda rows, c: len(rows) == 8 and ("GB", 1089, 62) in rows),
                ("96 guests in all have never booked, of 1,600",
                 lambda rows, c: sum(r[2] for r in rows) == 96 and sum(r[1] for r in rows) == 1600)],
    ),
    dict(
        id=3, ledger="Q1344", concept="NIGHTS", tier="1 - Finding your way around",
        title="Room-nights sold in 2025",
        prompt=(
            "A stay of three nights sells three room-nights. For each"
            " hotel, by name: the stays that BEGAN in 2025 and the"
            " room-nights they sold, as a whole number. Count only"
            " bookings whose status is 'stayed' -- the guest arrived."
            " check_out is the morning of departure, so the nights are"
            " the difference of the two dates; julianday turns a date"
            " into a number of days.\n\n"
            "Return: hotel, stays, room_nights"
        ),
        solution=("SELECT h.name, COUNT(*), CAST(SUM(julianday(b.check_out) - julianday(b.check_in)) AS INTEGER)"
                  " FROM bookings b JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " WHERE b.status = 'stayed' AND b.check_in >= '2025-01-01' AND b.check_in < '2026-01-01'"
                  " GROUP BY h.hotel_id"),
        trap_sql=("SELECT h.name, COUNT(*), CAST(SUM(julianday(b.check_out) - julianday(b.check_in)) AS INTEGER)"
                  " FROM bookings b JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " WHERE b.check_in >= '2025-01-01' AND b.check_in < '2026-01-01'"
                  " GROUP BY h.hotel_id"),
        note="Dates are text and cannot be subtracted; julianday() of"
             " each can. A booking has no hotel of its own -- it is"
             " reached through the room -- so the join runs bookings to"
             " rooms to hotels. The trap forgets the status and counts"
             " nights that were cancelled or never turned up for,"
             " about one booking in eight. Fellfoot Inn opened in"
             " September 2025, which is why its year is so short.",
        claims=[("eight hotels, Spa Gardens 1,969 stays and 6,187 room-nights",
                 lambda rows, c: len(rows) == 8 and ("Spa Gardens", 1969, 6187) in rows),
                ("Fellfoot Inn, open four months, 225 stays and 672 nights",
                 lambda rows, c: ("Fellfoot Inn", 225, 672) in rows)],
    ),
    # ====================================================== 2 Nights and dates
    dict(
        id=4, ledger="Q1345", concept="INHOUSE", tier="2 - Nights and dates",
        title="Who was in the house on New Year's Eve",
        prompt=(
            "For the NIGHT of 2025-12-31, each hotel by name: the rooms"
            " occupied and the people sleeping in them, adults and"
            " children together. Status 'stayed' only. A guest who"
            " checks out on the 31st left that morning and is not"
            " there that night; a guest who checks in on the 31st is."
            " The range is closed at one end and open at the other.\n\n"
            "Return: hotel, rooms_occupied, people"
        ),
        solution=("SELECT h.name, COUNT(*), SUM(b.adults + b.children)"
                  " FROM bookings b JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " WHERE b.status = 'stayed' AND b.check_in <= '2025-12-31' AND b.check_out > '2025-12-31'"
                  " GROUP BY h.hotel_id"),
        trap_sql=("SELECT h.name, COUNT(*), SUM(b.adults + b.children)"
                  " FROM bookings b JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " WHERE b.status = 'stayed' AND '2025-12-31' BETWEEN b.check_in AND b.check_out"
                  " GROUP BY h.hotel_id"),
        note="A stay covers the nights from check_in up to but not"
             " including check_out, so 'in the house on night d' is"
             " check_in <= d AND check_out > d. BETWEEN, the trap,"
             " includes both ends and counts everyone who left that"
             " morning as well: 102 rooms where 81 were occupied, and"
             " at some hotels more guests than beds. The same"
             " half-open test, with two ranges, is how you ask whether"
             " two bookings collide.",
        claims=[("eight hotels, 81 rooms occupied in all",
                 lambda rows, c: len(rows) == 8 and sum(r[1] for r in rows) == 81),
                ("Castle View had 14 rooms and 28 people",
                 lambda rows, c: ("Castle View", 14, 28) in rows)],
    ),
    dict(
        id=5, ledger="Q1346", concept="LEAD", tier="2 - Nights and dates",
        title="How far ahead each channel books",
        prompt=(
            "For each booking channel: its bookings, and the average"
            " number of days between the DAY the booking was made and"
            " the day of check-in, to one decimal place. Leave out"
            " cancelled bookings. booked_at is a timestamp with a time"
            " of day and check_in is a plain date: cut the timestamp"
            " down to its date before subtracting.\n\n"
            "Return: channel, bookings, avg_lead_days"
        ),
        solution=("SELECT channel, COUNT(*), ROUND(AVG(julianday(check_in) - julianday(date(booked_at))), 1)"
                  " FROM bookings WHERE status <> 'cancelled' GROUP BY channel"),
        trap_sql=("SELECT channel, COUNT(*), ROUND(AVG(julianday(check_in) - julianday(booked_at)), 1)"
                  " FROM bookings WHERE status <> 'cancelled' GROUP BY channel"),
        note="julianday of a timestamp includes the time as a fraction"
             " of a day, and a plain date counts as midnight. Subtract"
             " without date(), the trap, and a room taken at the desk"
             " at four in the afternoon was booked 'minus 0.7 days'"
             " ahead of its own check-in; every channel's average is"
             " short by the same half-day or so. date() cuts both to"
             " whole days. Agents book three months ahead, the web"
             " under two, and a walk-in by definition not at all.",
        claims=[("four channels, walk-ins exactly 0.0 days ahead",
                 lambda rows, c: len(rows) == 4 and ("walk_in", 1563, 0.0) in rows),
                ("agents book 96.3 days ahead on average",
                 lambda rows, c: ("agent", 3134, 96.3) in rows)],
    ),
    dict(
        id=6, ledger="Q1347", concept="OVERLAP", tier="2 - Nights and dates",
        title="Cancelled nights that were sold again",
        prompt=(
            "When a booking is cancelled the room may be let to someone"
            " else for some or all of the same nights. For each hotel,"
            " by name: how many CANCELLED bookings had at least one of"
            " their nights taken by another booking of the same room"
            " that was not cancelled. Two date ranges overlap when each"
            " starts before the other ends; EXISTS asks whether such a"
            " booking is there.\n\n"
            "Return: hotel, relet"
        ),
        solution=("SELECT h.name, COUNT(*) FROM bookings a JOIN rooms r ON r.room_id = a.room_id"
                  " JOIN hotels h ON h.hotel_id = r.hotel_id WHERE a.status = 'cancelled' AND EXISTS"
                  " (SELECT 1 FROM bookings b WHERE b.room_id = a.room_id AND b.status <> 'cancelled'"
                  " AND b.check_in < a.check_out AND a.check_in < b.check_out) GROUP BY h.hotel_id"),
        trap_sql=("SELECT h.name, COUNT(*) FROM bookings a JOIN rooms r ON r.room_id = a.room_id"
                  " JOIN hotels h ON h.hotel_id = r.hotel_id WHERE a.status = 'cancelled' AND EXISTS"
                  " (SELECT 1 FROM bookings b WHERE b.room_id = a.room_id AND b.status <> 'cancelled'"
                  " AND b.check_in = a.check_in) GROUP BY h.hotel_id"),
        note="Two ranges overlap when a starts before b ends AND b"
             " starts before a ends -- two comparisons that cover every"
             " case: one inside the other, either end sticking out, or"
             " identical. Strict < is right because check_out is the"
             " morning of departure: one guest leaving on the day the"
             " next arrives is not a collision. The trap looks only"
             " for a new booking starting on the same day and misses"
             " every replacement that began later in the freed"
             " nights, about a quarter of them.",
        claims=[("eight hotels, 888 cancelled bookings re-let",
                 lambda rows, c: len(rows) == 8 and sum(r[1] for r in rows) == 888),
                ("197 of them at Castle View",
                 lambda rows, c: ("Castle View", 197) in rows)],
    ),
    # ====================================================== 3 Money and scores
    dict(
        id=7, ledger="Q1348", concept="SIGNS", tier="3 - Money and scores",
        title="Money taken and money given back",
        prompt=(
            "A payment with a negative amount is a refund. For each"
            " payment method: the money TAKEN (the positive amounts"
            " added up) and the money REFUNDED, as a positive number of"
            " cents -- 0, not NULL, where there were no refunds. Two"
            " conditional sums in one pass.\n\n"
            "Return: method, taken_cents, refunded_cents"
        ),
        solution=("SELECT method, SUM(CASE WHEN amount_cents > 0 THEN amount_cents ELSE 0 END),"
                  " SUM(CASE WHEN amount_cents < 0 THEN -amount_cents ELSE 0 END) FROM payments GROUP BY method"),
        trap_sql=("SELECT method, SUM(amount_cents),"
                  " SUM(CASE WHEN amount_cents < 0 THEN -amount_cents ELSE 0 END) FROM payments GROUP BY method"),
        note="A CASE inside SUM decides, row by row, what each payment"
             " contributes: its amount to one column, its amount with"
             " the sign turned round to the other, and 0 otherwise."
             " The ELSE 0 is what makes cash's refund column 0 and not"
             " NULL. A plain SUM(amount_cents), the trap, is the NET:"
             " refunds already taken off, so the card total is 7.3"
             " million cents short of what was actually taken. Both"
             " numbers are true; they answer different questions.",
        claims=[("three methods, card took 416,072,170 and refunded 7,349,450",
                 lambda rows, c: len(rows) == 3 and ("card", 416072170, 7349450) in rows),
                ("cash was never refunded",
                 lambda rows, c: ("cash", 72842210, 0) in rows)],
    ),
    dict(
        id=8, ledger="Q1349", concept="EXTRAS", tier="3 - Money and scores",
        title="What a stay spends on extras",
        prompt=(
            "For each hotel, by name: its stays (status 'stayed') and"
            " the average a stay spent on extras -- the charges table --"
            " in whole cents, rounded. Many stays have no charges at"
            " all, and they count as stays that spent 0. Add the"
            " charges up per booking first, then attach that to every"
            " stay with the join that keeps the ones with nothing.\n\n"
            "Return: hotel, stays, avg_extras_cents"
        ),
        solution=("SELECT h.name, COUNT(*), CAST(ROUND(AVG(COALESCE(x.cents, 0))) AS INTEGER) FROM bookings b"
                  " JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " LEFT JOIN (SELECT booking_id, SUM(amount_cents) AS cents FROM charges GROUP BY booking_id) x"
                  " ON x.booking_id = b.booking_id WHERE b.status = 'stayed' GROUP BY h.hotel_id"),
        trap_sql=("SELECT h.name, COUNT(*), CAST(ROUND(AVG(x.cents)) AS INTEGER) FROM bookings b"
                  " JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " LEFT JOIN (SELECT booking_id, SUM(amount_cents) AS cents FROM charges GROUP BY booking_id) x"
                  " ON x.booking_id = b.booking_id WHERE b.status = 'stayed' GROUP BY h.hotel_id"),
        note="The subquery is one row per booking that HAS charges; the"
             " LEFT JOIN gives every other stay a NULL. AVG skips"
             " NULLs, so without COALESCE, the trap, the average is"
             " over the stays that spent something and comes out a"
             " tenth too high -- 'what a spending guest spends' passed"
             " off as 'what a guest spends'. COALESCE(x, 0) turns the"
             " missing into the zero it means here. Summing in a"
             " subquery first also keeps the stay count from being"
             " multiplied by the number of charges.",
        claims=[("eight hotels, Spa Gardens 2,946 stays averaging 13,968 cents",
                 lambda rows, c: len(rows) == 8 and ("Spa Gardens", 2946, 13968) in rows),
                ("Fellfoot Inn the least, 7,065",
                 lambda rows, c: min(rows, key=lambda r: r[2]) == ("Fellfoot Inn", 533, 7065))],
    ),
    dict(
        id=9, ledger="Q1350", concept="REVIEWED", tier="3 - Money and scores",
        title="How many stays are reviewed, and how well",
        prompt=(
            "A stay can be reviewed once it is over. For each hotel, by"
            " name, taking the stays (status 'stayed') that had checked"
            " out by 2026-06-30: how many stays, how many of them have"
            " a review, and the average score to two decimal places."
            " Keep the unreviewed stays in the count: COUNT(*) and"
            " COUNT(a column) differ exactly where that column is"
            " NULL.\n\n"
            "Return: hotel, stays, reviews, avg_score"
        ),
        solution=("SELECT h.name, COUNT(*), COUNT(v.review_id), ROUND(AVG(v.score), 2) FROM bookings b"
                  " JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " LEFT JOIN reviews v ON v.booking_id = b.booking_id"
                  " WHERE b.status = 'stayed' AND b.check_out <= '2026-06-30' GROUP BY h.hotel_id"),
        trap_sql=("SELECT h.name, COUNT(*), COUNT(v.review_id), ROUND(AVG(v.score), 2) FROM bookings b"
                  " JOIN rooms r ON r.room_id = b.room_id JOIN hotels h ON h.hotel_id = r.hotel_id"
                  " JOIN reviews v ON v.booking_id = b.booking_id"
                  " WHERE b.status = 'stayed' AND b.check_out <= '2026-06-30' GROUP BY h.hotel_id"),
        note="After the LEFT JOIN an unreviewed stay has NULL in every"
             " review column. COUNT(*) counts it, COUNT(v.review_id)"
             " does not, and AVG(v.score) leaves it out -- which is"
             " right this time: a stay with no review has no score,"
             " not a score of 0. The inner join of the trap keeps only"
             " reviewed stays, so its first two columns are equal and"
             " every hotel appears to be reviewed by all its guests."
             " About one stay in four is.",
        claims=[("eight hotels, Spa Gardens 752 reviews of 2,932 stays at 4.6",
                 lambda rows, c: len(rows) == 8 and ("Spa Gardens", 2932, 752, 4.6) in rows),
                ("Fellfoot Inn scores lowest, 3.2",
                 lambda rows, c: min(rows, key=lambda r: r[3])[0] == "Fellfoot Inn")],
    ),
    # ======================================================== 4 Changing rows
    dict(
        id=10, ledger="Q1351", concept="GALA", tier="4 - Changing rows",
        kind="script",
        title="The gala dinner goes on every bill",
        prompt=(
            "On 2026-06-30 Spa Gardens held a gala dinner, and every"
            " booking in the house that NIGHT is charged for it: one"
            " 'restaurant' charge dated 2026-06-30 of 2,500 cents for"
            " each person in the booking, adults and children alike."
            " Status 'stayed'; guests who left that morning were not at"
            " dinner. One INSERT ... SELECT, with the amount worked out"
            " in the SELECT.\n\n"
            "Checked: the restaurant charges dated 2026-06-30, how many"
            " and their cents"
        ),
        solution=("INSERT INTO charges (booking_id, kind, amount_cents, charged_on)\n"
                  "SELECT b.booking_id, 'restaurant', 2500 * (b.adults + b.children), '2026-06-30'\n"
                  "FROM bookings b\n"
                  "JOIN rooms r ON r.room_id = b.room_id\n"
                  "JOIN hotels h ON h.hotel_id = r.hotel_id\n"
                  "WHERE h.name = 'Spa Gardens' AND b.status = 'stayed'\n"
                  "  AND b.check_in <= '2026-06-30' AND b.check_out > '2026-06-30';"),
        trap_sql=("INSERT INTO charges (booking_id, kind, amount_cents, charged_on)\n"
                  "SELECT b.booking_id, 'restaurant', 2500 * (b.adults + b.children), '2026-06-30'\n"
                  "FROM bookings b\n"
                  "WHERE b.status = 'stayed'\n"
                  "  AND b.check_in <= '2026-06-30' AND b.check_out > '2026-06-30';"),
        probe_sql=("SELECT COUNT(*), SUM(amount_cents) FROM charges"
                   " WHERE kind = 'restaurant' AND charged_on = '2026-06-30'"),
        note="INSERT ... SELECT writes one row for each row its SELECT"
             " returns, so the WHERE of the SELECT is the whole"
             " decision about who is charged, and any expression can"
             " sit in its list: here a price times a head count, beside"
             " two literals. The trap has the right night and no hotel,"
             " and bills the dinner to all 82 bookings in the house"
             " across the group. Run the SELECT on its own first; it"
             " shows exactly the rows the INSERT will add.",
        claims=[("14 bookings and 29 people charged: 29 restaurant charges that day now",
                 lambda rows, c: rows == [(15 + 14, 87900 + 29 * 2500)])],
    ),
    dict(
        id=11, ledger="Q1352", concept="PROMOTE", tier="4 - Changing rows",
        kind="script",
        title="A hundred nights makes you gold",
        prompt=(
            "Every guest who has STAYED a hundred nights or more in"
            " total becomes a gold member, whatever their tier was."
            " Only nights of bookings with status 'stayed' count. One"
            " UPDATE; the guests are named by a subquery that groups"
            " the bookings and keeps the groups that reach the"
            " total.\n\n"
            "Checked: how many guests there are in each tier, NULL"
            " included"
        ),
        solution=("UPDATE guests SET tier = 'gold'\n"
                  "WHERE guest_id IN (\n"
                  "  SELECT guest_id FROM bookings WHERE status = 'stayed'\n"
                  "  GROUP BY guest_id\n"
                  "  HAVING SUM(julianday(check_out) - julianday(check_in)) >= 100);"),
        trap_sql=("UPDATE guests SET tier = 'gold'\n"
                  "WHERE guest_id IN (\n"
                  "  SELECT guest_id FROM bookings\n"
                  "  GROUP BY guest_id\n"
                  "  HAVING SUM(julianday(check_out) - julianday(check_in)) >= 100);"),
        probe_sql="SELECT tier, COUNT(*) FROM guests GROUP BY tier",
        note="The subquery is a query in its own right: group the stays"
             " by guest, add up each one's nights, and let HAVING keep"
             " the guests whose total reaches 100. WHERE filters rows"
             " before grouping -- the status -- and HAVING filters"
             " groups after it. The trap drops the WHERE and counts"
             " nights that were cancelled, never turned up for, or"
             " have not happened yet, promoting 124 guests instead of"
             " 31. One of the 32 who qualify was gold already.",
        claims=[("31 promoted: 128 gold, 261 silver, 1,211 with no tier",
                 lambda rows, c: sorted(rows, key=str) == sorted([("gold", 128), ("silver", 261), (None, 1211)], key=str))],
    ),
    dict(
        id=12, ledger="Q1353", concept="PURGE", tier="4 - Changing rows",
        kind="script",
        title="Old names that never became guests",
        prompt=(
            "The books are being tidied. Delete every guest who joined"
            " BEFORE 2023-01-01 and has never made a booking of any"
            " kind. Guests with bookings, and anyone who joined later,"
            " stay. A DELETE whose WHERE has a date test and a NOT"
            " EXISTS that looks at the guest being considered.\n\n"
            "Checked: guests left, the earliest joined_on among them,"
            " and how many have no email"
        ),
        solution=("DELETE FROM guests\n"
                  "WHERE joined_on < '2023-01-01'\n"
                  "  AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.guest_id = guests.guest_id);"),
        trap_sql=("DELETE FROM guests\n"
                  "WHERE NOT EXISTS (SELECT 1 FROM bookings b WHERE b.guest_id = guests.guest_id);"),
        probe_sql="SELECT COUNT(*), MIN(joined_on), SUM(email IS NULL) FROM guests",
        note="NOT EXISTS is true for a guest when the subquery finds no"
             " booking with their id; the reference to guests.guest_id"
             " inside it is what ties the subquery to the row being"
             " tested. The trap leaves out the date and deletes all 96"
             " who never booked, 62 of them recent sign-ups who may"
             " yet. Had the DELETE reached a guest WITH bookings, the"
             " foreign key would have refused the whole statement --"
             " the constraint is a safety net, not a substitute for"
             " the WHERE.",
        claims=[("34 deleted: 1,566 guests left",
                 lambda rows, c: rows[0][0] == 1566)],
    ),
    # =========================================================== 5 Procedures
    dict(
        id=13, ledger="Q1354", concept="CANCEL", tier="5 - Procedures",
        kind="script",
        title="A cancellation, and the deposit back",
        prompt=(
            "Booking 13638 is for a week in August 2026 and one payment"
            " has been made against it, the deposit. The guest cancels"
            " at 2026-07-01 09:00. In ONE transaction: mark the booking"
            " cancelled with that time -- the table's CHECK wants the"
            " status and cancelled_at to change together -- and record"
            " the refund: a payment for the same booking by the same"
            " method, at 2026-07-01 09:05, for the deposit's amount"
            " made NEGATIVE. Read the amount and method from the"
            " deposit; do not type them. The question then issues a"
            " ROLLBACK: committed work survives it.\n\n"
            "Checked: the booking's status and cancelled_at, its"
            " payments and what they add up to, and the refunds in the"
            " whole table"
        ),
        solution=("BEGIN;\n"
                  "UPDATE bookings SET status = 'cancelled', cancelled_at = '2026-07-01 09:00'\n"
                  "WHERE booking_id = 13638;\n"
                  "INSERT INTO payments (booking_id, paid_at, amount_cents, method)\n"
                  "SELECT booking_id, '2026-07-01 09:05', -amount_cents, method\n"
                  "FROM payments WHERE booking_id = 13638;\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE bookings SET status = 'cancelled', cancelled_at = '2026-07-01 09:00'\n"
                  "WHERE booking_id = 13638;\n"
                  "INSERT INTO payments (booking_id, paid_at, amount_cents, method)\n"
                  "SELECT booking_id, '2026-07-01 09:05', amount_cents, method\n"
                  "FROM payments WHERE booking_id = 13638;\n"
                  "COMMIT;"),
        driver_sql="ROLLBACK;",
        probe_sql=("SELECT b.status, b.cancelled_at,"
                   " (SELECT COUNT(*) FROM payments p WHERE p.booking_id = b.booking_id),"
                   " (SELECT SUM(p.amount_cents) FROM payments p WHERE p.booking_id = b.booking_id),"
                   " (SELECT COUNT(*) FROM payments WHERE amount_cents < 0)"
                   " FROM bookings b WHERE b.booking_id = 13638"),
        note="A cancellation is two facts in two tables, and the"
             " transaction is what stops the world seeing one without"
             " the other: a cancelled booking still holding a deposit,"
             " or a refund for a booking that is still live. The"
             " refund is not an edit to the deposit; money that moved"
             " is recorded as a new row with the opposite sign, so the"
             " two add up to nothing and the history stays. The trap"
             " copies the deposit without the minus and charges the"
             " guest twice for a stay they cancelled.",
        claims=[("cancelled, two payments adding up to nothing, 979 refunds now",
                 lambda rows, c: rows == [("cancelled", "2026-07-01 09:00", 2, 0, 979)])],
    ),
    dict(
        id=14, ledger="Q1355", concept="MOVE", tier="5 - Procedures",
        kind="script",
        title="A guest who changed rooms mid-stay",
        prompt=(
            "Booking 11988 records guest 441 in room 155 at Lakeside"
            " Lodge from 2026-03-06 to 2026-03-13. In fact the guest"
            " moved to room 159 on 2026-03-10 and spent the last three"
            " nights there. Put the records right in one transaction,"
            " as two bookings: 11988 ends on the 10th, and a NEW"
            " booking for room 159 runs from the 10th to the ORIGINAL"
            " check-out, with every other column copied from 11988."
            " Think about which of the two steps must read the row"
            " before the other changes it.\n\n"
            "Checked: guest 441's bookings that begin from 6 to 12"
            " March 2026: room, check-in, check-out, rate and status"
        ),
        solution=("BEGIN;\n"
                  "INSERT INTO bookings (guest_id, room_id, booked_at, check_in, check_out,\n"
                  "                      adults, children, channel, rate_cents, status)\n"
                  "SELECT guest_id, 159, booked_at, '2026-03-10', check_out,\n"
                  "       adults, children, channel, rate_cents, status\n"
                  "FROM bookings WHERE booking_id = 11988;\n"
                  "UPDATE bookings SET check_out = '2026-03-10' WHERE booking_id = 11988;\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE bookings SET check_out = '2026-03-10' WHERE booking_id = 11988;\n"
                  "INSERT INTO bookings (guest_id, room_id, booked_at, check_in, check_out,\n"
                  "                      adults, children, channel, rate_cents, status)\n"
                  "SELECT guest_id, 159, booked_at, '2026-03-10', '2026-03-12',\n"
                  "       adults, children, channel, rate_cents, status\n"
                  "FROM bookings WHERE booking_id = 11988;\n"
                  "COMMIT;"),
        probe_sql=("SELECT room_id, check_in, check_out, rate_cents, status FROM bookings"
                   " WHERE guest_id = 441 AND check_in >= '2026-03-06' AND check_in <= '2026-03-12'"),
        note="The new booking's check-out is the old one's, and that"
             " value exists in only one place. Copy first, then"
             " shorten: once the UPDATE has run, 11988 says the 10th"
             " and the original date is gone -- an INSERT ... SELECT"
             " after it would copy the 10th as both ends, and the"
             " CHECK (check_out > check_in) would refuse it. The trap"
             " shortens first and then has to type the date from"
             " memory, a night short. Seven nights before, four and"
             " three after: a split should never change the total.",
        claims=[("room 155 to the 10th, room 159 from the 10th to the 13th",
                 lambda rows, c: sorted(rows) == [(155, "2026-03-06", "2026-03-10", 8650, "stayed"),
                                                  (159, "2026-03-10", "2026-03-13", 8650, "stayed")])],
    ),
    dict(
        id=15, ledger="Q1356", concept="GUARD", tier="5 - Procedures",
        kind="script",
        title="No room is sold twice",
        prompt=(
            "Nothing in the schema stops two bookings for the same room"
            " on the same night. Store the check as a trigger: BEFORE"
            " INSERT on bookings, when the new booking is not itself"
            " cancelled and another booking for that room, also not"
            " cancelled, overlaps its dates, the insert is refused with"
            " RAISE(ABORT, ...). A guest may arrive on the day another"
            " leaves; cancelled bookings block nothing. The question"
            " then tries three bookings for July and August 2026: one"
            " that collides, one that fits exactly between two others,"
            " and one over nights that only a cancelled booking"
            " held.\n\n"
            "Checked: room and dates of the bookings made after the"
            " data ends"
        ),
        solution=("CREATE TRIGGER no_double_booking BEFORE INSERT ON bookings\n"
                  "WHEN NEW.status <> 'cancelled' AND EXISTS (\n"
                  "  SELECT 1 FROM bookings b\n"
                  "  WHERE b.room_id = NEW.room_id AND b.status <> 'cancelled'\n"
                  "    AND b.check_in < NEW.check_out AND NEW.check_in < b.check_out)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'room already booked for those nights');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER no_double_booking BEFORE INSERT ON bookings\n"
                  "WHEN EXISTS (\n"
                  "  SELECT 1 FROM bookings b\n"
                  "  WHERE b.room_id = NEW.room_id\n"
                  "    AND b.check_in < NEW.check_out AND NEW.check_in < b.check_out)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'room already booked for those nights');\n"
                  "END;"),
        driver_sql=("INSERT INTO bookings (guest_id, room_id, booked_at, check_in, check_out, adults, children, channel, rate_cents, status)"
                    " VALUES (1, 15, '2026-07-01 10:00', '2026-08-09', '2026-08-11', 1, 0, 'phone', 7400, 'booked');\n"
                    "INSERT INTO bookings (guest_id, room_id, booked_at, check_in, check_out, adults, children, channel, rate_cents, status)"
                    " VALUES (2, 15, '2026-07-01 10:05', '2026-08-05', '2026-08-09', 1, 0, 'phone', 7400, 'booked');\n"
                    "INSERT INTO bookings (guest_id, room_id, booked_at, check_in, check_out, adults, children, channel, rate_cents, status)"
                    " VALUES (3, 26, '2026-07-01 10:10', '2026-07-10', '2026-07-11', 2, 0, 'phone', 9000, 'booked');"),
        probe_sql="SELECT room_id, check_in, check_out FROM bookings WHERE booked_at >= '2026-07-01'",
        note="A trigger's WHEN clause is a condition on the incoming"
             " row, NEW, and may hold a subquery; RAISE(ABORT) inside"
             " the body cancels the statement that fired it. The"
             " overlap test is the usual pair of strict comparisons,"
             " so the booking that starts the day another ends gets"
             " in. The trap forgets that a cancelled booking holds no"
             " room and turns away the third guest from an empty one."
             " A CHECK cannot do this job: it sees one row, and a"
             " double booking is a fact about two.",
        claims=[("two of the three got in: the exact fit and the room freed by a cancellation",
                 lambda rows, c: sorted(rows) == [(15, "2026-08-05", "2026-08-09"), (26, "2026-07-10", "2026-07-11")])],
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
