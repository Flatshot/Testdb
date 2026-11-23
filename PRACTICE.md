# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the hotel schema, the third set
on it: ten questions use a tool these tables have not met -- a window aggregate,
a recursive CTE, string functions, a self-join, COUNT(DISTINCT), strftime, UNION
ALL, CASE inside an UPDATE, UPDATE ... FROM, a view, CREATE TABLE ... AS SELECT
-- and five return to what the second set found hard: what a window is
partitioned by, where an outer join's conditions go, a total over a grouped
query, the fan-out of two child tables, and the upsert. Two tools per question,
with the tiers named by task. Nine read the data and **six change it**: three
single statements and three procedures of several steps. The prompts name the
tool but do not write the statement. **Fifteen Python** at the easy level of the
last thirteen sets: everyday tasks over plain lists and strings in the hotel's
terms, with no maths, no dicts and nothing to import.

**The database is the one the last two sets used.** If the app offers to re-seed
when it starts, accept; from a terminal it is `python seed.py`.

| Stage | SQL questions |
|---|---|
| 1 - Hotels and their rooms | 1-3 |
| 2 - Guests | 4-6 |
| 3 - Money and time | 7-9 |
| 4 - Changing rows | 10-12 |
| 5 - Procedures | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Numbers at the desk | 1-5 |
| 2 - Words and names | 6-10 |
| 3 - Lists on the board | 11-15 |

## The schema

Seven tables. `hotels` are the 8 sites, each in a `town` with a
star rating, opened on a date and perhaps closed. `rooms` belong to a
hotel: a `room_no` as written on the door, a `floor`, a `kind` (single,
twin, double, family or suite), how many it `sleeps`, and `rack_cents`,
the list price for one night. `guests` are people: a `country` code, an
`email` that may be NULL, a loyalty `tier` (silver, gold, or NULL for the
many who are not in the scheme) and the day they `joined_on`. `bookings`
is the centre: a guest, a room, when it was `booked_at`, a `check_in` and
a `check_out` date, the `adults` and `children`, the `channel` it came
through (web, phone, agent or walk_in), `rate_cents` -- the price agreed
per night, which is not always the list price -- a `status`, and a
`cancelled_at` that is NULL unless it was cancelled. `charges` are the
extras put on a room during a stay: breakfast, bar, restaurant, spa,
parking, laundry. `payments` are money against a booking, with a
NEGATIVE amount for a refund. `reviews` are at most one per booking: a
`score` from 1 to 5 and perhaps a `headline`. Double-click a table in the
left pane to see its columns.

**A stay is a half-open range.** `check_in` is the first night and
`check_out` is the morning the guest leaves, so the number of nights is
`check_out` minus `check_in`, a guest is in the house on night `d` when
`check_in <= d AND check_out > d`, and a room can be let again on the day
its last guest leaves.

**Status.** 'stayed' means the guest arrived, and includes the guests
still in the house when the data ends. 'booked' is a stay that had not
begun by then. 'cancelled' bookings keep their dates, so they can
overlap whoever took the room next. 'no_show' is a guest who never
came; the room was held for them.

**Dates and times are text**: 'YYYY-MM-DD' for dates, 'YYYY-MM-DD HH:MM'
for timestamps. They compare correctly as text; `julianday()` turns either
into a number of days you can subtract, and `date()` cuts a timestamp to
its day.

**The data ends at 2026-06-30 23:59.** Nothing later has happened:
1,867 bookings are for stays that have not begun, 82 guests
are in the house on the last night with their bills not yet settled, and
every question that touches the edge says which side of it to stand on.

**The definition of a table**, with its CHECKs and UNIQUE constraints,
is in `schema.sql`.

## The writable stage

Questions 10 to 15 change the data. 10 to 12 are one statement each: two UPDATEs
and a DELETE. 13 to 15 are **procedures**. SQLite has no CREATE PROCEDURE,
variables, loops or TRY/CATCH; what it has instead is the transaction, whose
steps all happen or none do, the view, which is a query stored under a name, and
the trigger body, which is stored in the database and runs when something calls
it.

**How they run.** Press Run and your script executes, statement by statement, in
a private in-memory copy of the database. Nothing you write can reach the real
file. The copy **persists across Runs of the same question** -- so you can run
an `UPDATE`, then a `SELECT`, and see what it did -- and **Reset** throws it
away and starts again from the seeded data. Moving to another question also
starts fresh, so no question depends on what another one wrote. If your script
ends in a statement that returns rows, the results pane shows that; otherwise it
shows the question's *probe* query, which is what **Check answer** compares.
Check always grades a fresh copy, so nothing you ran earlier can affect the
grade.

**Start each statement on a new line.** The script is split where a line ends a
complete statement, so `BEGIN;` and `COMMIT;` get lines of their own. A
statement may run over several lines, and a CREATE TRIGGER, with the semicolons
inside its body, is kept whole.

**Transactions.** `BEGIN;` opens one and `COMMIT;` makes everything since
permanent. The sandbox does not commit for you. After a script that creates a
view, a table or a trigger, a second Run fails because the first one's is still
there: press Reset. The same goes for a script that stopped half-way with its
transaction open.

**Driver statements.** Question 14 issues a `ROLLBACK` *after* your script:
committed work stands, and a transaction left open is undone, tables and all.
Question 15 inserts four charges: 1,850 and 6,000 cents for booking 15170, which
has extras already, and 1,400 and 900 for booking 14148, which has none, so the
trigger meets both of its cases. Questions 10 to 13 are graded on what your
script leaves behind.

| # | Construct |
|---|---|
| 10 | `UPDATE rooms SET rack_cents = rack_cents + CASE kind WHEN '...' THEN ... WHEN '...' THEN ... ELSE ... END WHERE hotel_id = 8` |
| 11 | `UPDATE bookings SET rate_cents = r.rack_cents FROM rooms r WHERE r.room_id = bookings.room_id AND r.hotel_id = 6 AND bookings.status = '...' AND bookings.rate_cents > r.rack_cents` |
| 12 | `DELETE FROM payments WHERE booking_id IN (SELECT booking_id FROM payments GROUP BY booking_id HAVING SUM(amount_cents) = 0)` |
| 13 | `CREATE VIEW bills AS SELECT b.booking_id, b.check_out, nights * b.rate_cents AS room_cents, COALESCE((SELECT SUM ... charges), 0) AS extras_cents, COALESCE((SELECT SUM ... payments), 0) AS paid_cents FROM bookings b WHERE ...; INSERT INTO payments (...) SELECT booking_id, '...', room_cents + extras_cents - paid_cents, 'card' FROM bills WHERE ...` |
| 14 | `BEGIN; CREATE TABLE old_bookings AS SELECT b.* FROM bookings b JOIN rooms r ... WHERE ...; CREATE TABLE old_payments AS SELECT * FROM payments WHERE booking_id IN (SELECT booking_id FROM old_bookings); DELETE FROM payments WHERE ...; DELETE FROM bookings WHERE ...; COMMIT;` |
| 15 | `CREATE TABLE extras_totals (booking_id INTEGER PRIMARY KEY, total_cents INTEGER NOT NULL); INSERT INTO extras_totals SELECT booking_id, SUM(amount_cents) FROM charges GROUP BY booking_id; CREATE TRIGGER ... AFTER INSERT ON charges BEGIN INSERT INTO extras_totals ... VALUES (NEW.booking_id, NEW.amount_cents) ON CONFLICT (booking_id) DO UPDATE SET total_cents = total_cents + excluded.total_cents; END` |

## Things the data does on purpose

- **8 hotels in four towns, with 176 rooms between them.** Abbey Steps, hotel 4,
  closed on 2026-03-01: it sold seven rooms on its last night, 28 February, and
  none after, the zeros question 3 has to keep. Fellfoot Inn, hotel 8, opened on
  2025-09-01 with 14 rooms.
- **Each hotel has its own level of prices.** The average list price runs from
  5,821 cents at Fellfoot Inn to 14,382 at Spa Gardens. Fourteen rooms cost more
  than one and a quarter times their own hotel's average; measured against the
  whole group's average it would be 43, 32 of them at Spa Gardens, question 1.
- **1,501 guests have stayed, at 6,728 pairs of guest and hotel.** 34 times a
  guest began two stays at one hotel on the same day, which is why question 2
  names booking_id as the tiebreak.
- **279 of the 1,600 guests gave no email.** The other 1,321 use four domains,
  question 4.
- **Booking ids do not run in date order.** 332 times a guest checked out of one
  stay and into another on the same day; three of those were the same room,
  question 5, and in all three the later stay has the lower booking_id.
- **71 guests have stayed at all eight hotels**, the keenest in eleven stays.
  560 guests have eight stays or more, the number question 6 gives if stays are
  counted in place of hotels.
- **9,191 stays began in 2025**, most on a Friday or a Saturday, question 7.
  Their room revenue was 275,230,200 cents, 48.9 per cent of it booked on the
  web, question 8.
- **No two charges are alike in every column, but many look alike without their
  date.** Booking 15410 has three breakfasts at 1,200 cents and three nights'
  parking at 1,000; its bill has twelve lines and plain UNION leaves eight,
  question 9.
- **A rate is not always the list price, in either direction.** 149 of Station
  House's 206 bookings not yet arrived were agreed above it, by 121,100 cents in
  all, and 51 below it, question 11.
- **Refunds are negative payments, and all 978 of them belong to cancelled
  bookings**, each cancelling one deposit exactly. Another 258 cancelled
  bookings kept their deposit, 2,315,000 cents between them, question 12.
- **82 stays are in the house when the data ends and 79 of them owe money**,
  4,009,680 cents in all. 886 stays that have already left also owe something,
  question 13.
- **Abbey Steps has 61 cancelled bookings and 14 no-shows**, with 101 payments
  worth 121,600 cents. A booking that never became a stay has no charges and no
  review, so payments are the only child rows in the way, question 14.
- **1,471 of the 13,625 stays have no charge at all.** Booking 14148 is one;
  booking 15170 has 40,900 cents of extras, question 15.
- **The data ends at 2026-06-30 23:59**, so a booking with status 'booked' is
  always in the future and a payment at 23:30 that night is the last of the day.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function with
the name the question gives, Run calls it once for each test input and shows
every call and its result in the output pane, and Check compares each result
with the reference function's. Values are compared, not their printed form --
but the type counts: a tuple is not a list, 2.0 is not 2, and the string 'yes'
is not True. A function that prints its answer instead of returning it returns
None, and None matches nothing. The inputs are everyday values in the hotel's
terms: whole numbers of nights, hours and cents for questions 1 to 5, text as
guests and agents type it for 6 to 10, lists of names, rooms and log entries for
11 to 15. Each prompt shows one or two example calls with their answers, and Run
adds a few more, including the empty list or the edge the question warns about.

**Nothing needs importing in this set.** Question 4 returns None for an empty
list, and question 15 returns a list of lists.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the database,
the app, or any file. Tab inserts four spaces and Return keeps the indentation
of the line above.

# SQL

## 1 - Hotels and their rooms (3)

An average written beside every row by a window with a partition and no order, a
numbering that restarts for every pair of guest and hotel, and a list of dates
made by a recursive CTE so that an outer join has something to start from.

1. **Rooms priced well above their own hotel** (Q1372)

   Each hotel has its own level of prices: a dear room at Fellfoot Inn costs
   less than a cheap one at Spa Gardens. List the rooms whose list price
   (rack_cents) is more than one and a quarter times the average list price of
   THEIR OWN hotel, with the hotel's name and that average beside them. A window
   aggregate: an average with OVER and a partition, but no ORDER BY, gives every
   row its group's figure without collapsing the rows. As with any window, the
   test on it goes in an outer query. The average is compared to two decimal
   places.

   *Return: hotel, room_no, rack_cents, hotel_avg*

2. **How each hotel's guests first found it** (Q1373)

   A guest's first stay at a hotel says how that hotel won them. Take stays only
   (status 'stayed'). For each guest and each hotel, find the first stay that
   guest made AT THAT HOTEL: the earliest check_in, and the lower booking_id if
   two begin on the same day. Then count those first stays by hotel name and
   channel. A numbering window function, whose numbering restarts for every pair
   of guest and hotel -- not for every guest, and not for every hotel.

   *Return: hotel, channel, first_stays*

3. **Abbey Steps, night by night, to the end** (Q1374)

   Abbey Steps is hotel 4 and closed on 2026-03-01. For each of the ten nights
   from 2026-02-23 to 2026-03-04: how many of its rooms were occupied by a stay
   (status 'stayed')? A guest is in the house on night d when check_in <= d <
   check_out. Every one of the ten nights must have a row, the empty ones with
   0. No table holds one row per date, so make one: a recursive CTE (WITH
   RECURSIVE) begins with a first row and keeps adding a day to the row before
   until a stop date. Then an outer join from the nights to the bookings -- and
   remember where the conditions on the booking have to be written for an empty
   night to survive them.

   *Return: night, rooms_sold*

## 2 - Guests (3)

instr and substr to take a text apart, the bookings table joined to itself under
two names, and COUNT(DISTINCT) in a HAVING for the guests who have been
everywhere.

4. **Where the guests' email lives** (Q1375)

   The part of an email address after the @ is its domain. For each domain: how
   many guests use it, and how many of those are in the loyalty scheme (tier is
   not NULL). Guests with no email are left out altogether, not shown as a group
   of their own. Two string functions: one finds the position of a character
   inside a text, the other takes the part of a text from a given position on.

   *Return: domain, guests, members*

5. **A stay extended by booking again** (Q1376)

   When a guest extends a stay the desk sometimes enters a second booking
   instead of changing the first: the same guest, in the same room, checking in
   on the very day the first booking checks out. Find those pairs, both bookings
   being stays (status 'stayed'). A self-join: the bookings table joined to
   itself under two aliases, one playing the earlier stay and one the later.
   Booking ids do not run in date order, so let the dates decide which is which.

   *Return: guest_id, room_id, first_booking, second_booking, check_in, check_out -- the check_in of the earlier booking and the check_out of the later*

6. **Guests who have tried every hotel** (Q1377)

   Which guests have stayed (status 'stayed') at every hotel the group has ever
   had, Abbey Steps included? Give each with their total number of stays. Do not
   type the number of hotels: compare the count of DIFFERENT hotels a guest has
   stayed at with a subquery that counts the hotels table. The test is on a
   group, so it belongs in HAVING.

   *Return: guest_id, name, stays*

## 3 - Money and time (3)

strftime to fold a year of dates into seven weekdays, a window with empty
brackets for each group's share of the whole, and UNION ALL to stack three
tables into one bill.

7. **Which day of the week guests arrive** (Q1378)

   For stays (status 'stayed') that began in 2025: group them by the day of the
   week of check_in, and give the number of arrivals and the average length of
   stay in nights. strftime turns a date into text in a format you choose, and
   one of its codes is the day of the week as a digit, '0' for Sunday to '6' for
   Saturday. Return the digit as strftime gives it, which is text. The average
   is compared to two decimal places.

   *Return: weekday, arrivals, avg_nights*

8. **Each channel's share of the room revenue** (Q1379)

   For stays (status 'stayed') that began in 2025, room revenue is nights times
   rate_cents. For each channel: its room revenue, and that revenue as a
   percentage of all four channels together, rounded to one decimal place. The
   total has to appear on every row beside the group's own figure. A window with
   empty brackets, OVER (), spans the whole result, and it can be laid over a
   grouped query as the running total was last time.

   *Return: channel, room_cents, pct*

9. **The bill for booking 15410, line by line** (Q1380)

   Print the bill for booking 15410, three nights at Station House. One line for
   the room: the item 'room' and nights times rate_cents as the amount. One line
   for EVERY charge, the item being its kind. One line for EVERY payment, the
   item 'paid' and the amount made NEGATIVE, so that a settled bill adds up to
   nothing. Three SELECTs stacked into one result. There are two words for
   stacking, and one of them quietly throws away lines that look alike: this
   guest had breakfast three times.

   *Return: item, cents*

## 4 - Changing rows (3)

Writable, one statement each: an UPDATE whose amount is chosen by CASE, an
UPDATE that joins a second table with FROM, and a DELETE that removes whole
groups picked by HAVING.

10. **Fellfoot Inn puts its prices up, by kind of room** (Q1381)

    Fellfoot Inn (hotel 8) raises its list prices: singles by 250 cents, twins
    by 400, and every other kind of room by 600. In ONE UPDATE statement. A CASE
    expression can stand wherever a value can, including on the right of SET,
    and its ELSE takes care of 'every other'. No other hotel's prices change.

    *Checked: rooms and total list price by kind, for Fellfoot Inn and for the other hotels together*

11. **Nobody pays over the list price at Station House** (Q1382)

    Station House (hotel 6) has promised that no future guest will pay more than
    the list price. For its bookings not yet arrived (status 'booked') whose
    rate_cents is above the rack_cents of the room booked, bring the rate down
    to that list price. Rates already at or below it stay as they are, and so
    does every other hotel. The new value lives in another table: UPDATE ...
    FROM joins that table into the UPDATE, so that SET can use its columns
    directly. It does with a join what the correlated subquery did last time.

    *Checked: for Station House and for the other hotels together, by status: bookings, the total of their rates, and how many are above the list price*

12. **Deposits paid and refunded in full** (Q1383)

    When a booking is cancelled in good time its deposit is refunded, and its
    two payments -- one positive, one negative -- add up to nothing. The
    accountant wants those rows gone: delete every payment that belongs to a
    booking whose payments sum to exactly zero. A booking whose payments do not
    cancel out keeps all of them, and that includes the cancelled bookings where
    the deposit was kept. The test is on a whole group of rows, so find the
    booking_ids with GROUP BY and HAVING and let the DELETE take every row that
    carries one of them. One statement.

    *Checked: by booking status: payment rows left, bookings with a payment left, the total left, and refunds left*

## 5 - Procedures (3)

Writable questions of several steps. SQLite has no CREATE PROCEDURE: a view
stores a query for later statements to read, a transaction makes steps stand or
fall together, and a trigger body is a procedure the database runs for you.

13. **A view of every bill, and a night audit that reads it** (Q1384)

    Two steps. First create a VIEW called bills, with one row for each stay
    (status 'stayed') and exactly these columns: booking_id, check_out,
    room_cents (nights times rate_cents), extras_cents (the sum of its charges,
    0 if it has none) and paid_cents (the sum of its payments, 0 if none). A
    view is a SELECT stored under a name and read like a table. A stay has many
    charges and many payments: beware the fan-out that counts each once for
    every row of the other. Then use the view. For every stay still in the house
    when the data ends (check_out after '2026-06-30') that owes money, INSERT
    one payment of exactly what it owes, by 'card', paid_at '2026-06-30 23:30'.
    What a stay owes is room plus extras less paid.

    *Checked: the view's rows and its three totals; payments made at 23:30; stays in the house still owing; stays owing anywhere*

14. **Abbey Steps' dead bookings leave the live tables** (Q1385)

    Abbey Steps (hotel 4) has closed, and its bookings that never became stays
    -- status 'cancelled' or 'no_show' -- are to move out of the live tables,
    and their payments with them. In ONE transaction: create a table
    old_bookings holding those booking rows, all columns; create a table
    old_payments holding every payment of those bookings, all columns; then
    delete the same rows from payments and from bookings. CREATE TABLE ... AS
    SELECT makes a table out of a query's result. Two orders matter. A row has
    to be copied before it is deleted. And foreign keys are enforced, so a
    booking that still has payments cannot be deleted. The question then issues
    a ROLLBACK: committed work survives it.

    *Checked: rows in old_bookings; rows and total in old_payments; rows left in bookings; rows and total left in payments*

15. **A total of extras that keeps itself up to date** (Q1386)

    The bar wants each booking's extras total without adding up its charges
    every time. Three steps. Create a table extras_totals with booking_id as its
    PRIMARY KEY and total_cents. Fill it from the charges already there, one row
    for each booking that has any. Then create a trigger that fires AFTER INSERT
    ON charges and keeps the table right: a booking already in it has the new
    amount added to its total, and a booking not yet in it gets a row. That is
    the upsert of the last set, written inside a trigger body, where NEW is the
    row just inserted. The question then inserts four charges: two for booking
    15170, which has 40,900 cents of extras already, and two for booking 14148,
    which has none.

    *Checked: the number of rows in extras_totals and their grand total; the rows for bookings 15170 and 14148*

# Python

## 1 - Numbers at the desk (5)

An f-string with a decision in it, a format spec for commas and padding, if /
elif / else with the boundaries on the right side, index with max, and a loop
that answers False early and True only at the end.

1. **One night or two nights** (P641)

   A confirmation says how long the stay is. Write a function `nights_label(n)`
   that returns the number followed by the word 'night' when n is exactly 1 and
   'nights' for any other number, 0 included. An f-string puts the number into
   the text.

   ```
   nights_label(1) -> '1 night'
   nights_label(3) -> '3 nights'
   ```

   *Return: a string.*

2. **Cents as a number, money as text** (P642)

   Last time money text became cents; now the other way. Write a function
   `format_cents(cents)` that takes a whole number of cents, never negative, and
   returns it as text: the dollars with a comma between each group of three
   digits, a point, and always two digits of cents. // and % split the number in
   two. Inside an f-string's braces a format spec after a colon does the rest: a
   comma asks for thousands separators, and 02d pads a number to two digits with
   a zero. No floats.

   ```
   format_cents(123450) -> '1,234.50'
   format_cents(5) -> '0.05'
   ```

   *Return: a string.*

3. **What a late check-out costs** (P643)

   Guests should be out by eleven. Up to and including 1 hour late costs
   nothing. More than 1 hour and up to and including 4 hours costs half the
   nightly rate. More than 4 hours costs the whole rate. Write a function
   `late_charge(hours, rate)` that returns the charge in cents; hours is a whole
   number and rate is in cents, and half of it is rate // 2. An if, an elif and
   an else -- and mind which side of each line 1 and 4 fall.

   ```
   late_charge(1, 9000) -> 0
   late_charge(4, 9000) -> 4500
   late_charge(5, 9000) -> 9000
   ```

   *Return: an int.*

4. **Which stay was the longest?** (P644)

   A guest's stays are listed in order, as numbers of nights. Write a function
   `longest_stay(nights)` that returns the POSITION of the longest one, counting
   from 0; the first of them if several are equally long; and None when the list
   is empty. max finds the largest value and a list's index method finds where a
   value first appears.

   ```
   longest_stay([2, 5, 3]) -> 1
   longest_stay([4, 7, 7, 1]) -> 1
   ```

   *Return: an int, or None.*

5. **Has everyone settled up?** (P645)

   Before a coach party leaves, the desk checks the balance on every room, in
   cents. Write a function `all_settled(balances)` that returns True when every
   balance is 0 and False when any is not. With no rooms at all there is nothing
   outstanding: True. One unsettled room is enough to answer False, but True can
   only be said after the last one has been looked at.

   ```
   all_settled([0, 0, 0]) -> True
   all_settled([0, 250, 0]) -> False
   ```

   *Return: a bool.*

## 2 - Words and names (5)

split and strip round a comma, a string built up letter by letter, a slice with
upper and zfill, in after strip and lower, and whole words compared one at a
time.

6. **Surname first, turned round** (P646)

   The agent's list gives names surname first, with a comma: 'Lovelace, Ada'.
   Write a function `swap_name(listed)` that returns the first name, one space,
   and the surname. There is always exactly one comma, but the spaces round it
   and at the ends are as the agent happened to type them. split cuts a string
   at a separator, and strip removes spaces from both ends.

   ```
   swap_name('Lovelace, Ada') -> 'Ada Lovelace'
   swap_name('Hopper,Grace') -> 'Grace Hopper'
   ```

   *Return: a string.*

7. **Initials for the luggage tag** (P647)

   A luggage tag carries initials. Write a function `initials(name)` that
   returns the first letter of each word of the name, as a capital, each
   followed by a full stop. The name may have any number of words, extra spaces,
   or be empty, which gives ''. split with no argument cuts at any run of
   spaces, and word[0] is a word's first letter.

   ```
   initials('ada mary lovelace') -> 'A.M.L.'
   initials('cher') -> 'C.'
   ```

   *Return: a string.*

8. **The code on a key card** (P648)

   Each key card is printed with a code: the first three letters of the hotel's
   name in capitals, a hyphen, and the room number written with three digits,
   zeros in front if it needs them. Write a function `key_code(hotel, room)`,
   where hotel is the name and room is a whole number from 1 to 999. A slice
   takes the first three letters; the number has to become text before it can be
   padded, and strings have a method that fills with zeros on the left.

   ```
   key_code('Fellfoot Inn', 7) -> 'FEL-007'
   key_code('Spa Gardens', 312) -> 'SPA-312'
   ```

   *Return: a string.*

9. **Did the guest say yes?** (P649)

   The kiosk asks 'Breakfast? (y/n)' and guests type what they like. Write a
   function `said_yes(answer)` that returns True when the answer is 'y' or 'yes'
   -- in any mixture of capitals, with or without spaces at the ends -- and
   False for anything else at all, 'yes please' included. Tidy the text first;
   then `in` tests whether a value is one of several.

   ```
   said_yes(' Y ') -> True
   said_yes('no') -> False
   ```

   *Return: a bool.*

10. **How often does the note say it?** (P650)

    Housekeeping scans booking notes for a word. Write a function
    `count_word(note, word)` that returns how many times the word appears in the
    note as a WHOLE word. Capitals do not matter, and a full stop, comma,
    exclamation mark or question mark stuck to the end of a word is not part of
    it. 'bedroom' is not 'bed'. Split the note into words and compare each one;
    strip can be told which characters to remove.

    ```
    count_word('Extra bed please. Bed by the window, not the bedroom door!', 'bed') -> 2
    count_word('quiet room', 'bed') -> 0
    ```

    *Return: an int.*

## 3 - Lists on the board (5)

A slice from the end and its one bad value, not in to filter, a list that
remembers what it has seen, zip to walk two lists together, and range with a
step.

11. **The last few lines of the log** (P651)

    The night porter wants the end of the door log. Write a function
    `last_entries(log, n)` that returns a new list of the last n entries, in
    their original order. If the log has fewer than n, return them all; if n is
    0, return an empty list. n is never negative. A slice with a negative start
    counts from the end -- but try it with 0 before you trust it.

    ```
    last_entries(['in 101', 'out 204', 'in 305', 'out 101'], 2) -> ['in 305', 'out 101']
    last_entries(['in 101'], 5) -> ['in 101']
    ```

    *Return: a list of strings.*

12. **The rooms nobody has taken** (P652)

    One list holds a floor's rooms and another the rooms already taken. Write a
    function `still_free(rooms, taken)` that returns a NEW list of the rooms
    that are not in taken, in the order they had in rooms. `not in` tests
    whether a value is missing from a list. Build the answer up; do not take
    things out of a list you are walking through.

    ```
    still_free([101, 102, 103, 104], [102, 103]) -> [101, 104]
    ```

    *Return: a list of ints.*

13. **A guest list with nobody on it twice** (P653)

    The dinner list was written as guests rang down, and some rang twice. Write
    a function `no_repeats(names)` that returns a new list with each name once,
    in the order of its FIRST appearance. Keep a list of the names already seen
    and add a name only when it is not there yet.

    ```
    no_repeats(['Mei', 'Ada', 'Mei', 'Hugo', 'Ada']) -> ['Mei', 'Ada', 'Hugo']
    ```

    *Return: a list of strings.*

14. **Who is in which room?** (P654)

    Two lists run side by side: guests' names, and the rooms given out in the
    same order. Write a function `pair_up(names, rooms)` that returns a list of
    lines, each a name, a colon and a space, and the room. If one list is longer
    than the other, stop when the shorter runs out. zip walks two lists together
    and hands over one item from each on every turn.

    ```
    pair_up(['Ada', 'Hugo'], [101, 204]) -> ['Ada: 101', 'Hugo: 204']
    pair_up(['Ada', 'Hugo', 'Mei'], [101, 204]) -> ['Ada: 101', 'Hugo: 204']
    ```

    *Return: a list of strings.*

15. **A party seated at tables** (P655)

    The restaurant seats a party in the order of the list, filling one table
    before starting the next. Write a function `tables_of(guests, size)` that
    returns a list of lists: each inner list one table of `size` guests, except
    that the last table takes whoever is left and may be smaller. Nobody is left
    standing, and an empty party needs no tables. range can count in steps, and
    a slice that runs past the end simply stops there.

    ```
    tables_of(['Ada', 'Hugo', 'Mei', 'Zeno', 'Li'], 2) -> [['Ada', 'Hugo'], ['Mei', 'Zeno'], ['Li']]
    ```

    *Return: a list of lists of strings.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
2,011 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
