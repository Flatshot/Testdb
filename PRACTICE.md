# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on a NEW schema, a small
group of hotels: the first set on it, so the tools are the central ones,
asked where rooms, nights and bills make them matter, at two tools per
question with the tiers named by task. Nine read the data and **six
change it**: three single statements and three procedures of several
steps. The prompts name the tool but do not write the statement.
**Fifteen Python** at the easy level of the last eleven sets: everyday
tasks over plain lists and strings, now in the hotel's terms, with no
maths and no dicts -- and, for the first time, dates handled with the
datetime module.

**The database has to be re-seeded for this set.** The app offers to do
it when it starts; from a terminal it is `python seed.py`.

| Stage | SQL questions |
|---|---|
| 1 - Finding your way around | 1-3 |
| 2 - Nights and dates | 4-6 |
| 3 - Money and scores | 7-9 |
| 4 - Changing rows | 10-12 |
| 5 - Procedures | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Dates, with datetime | 1-5 |
| 2 - Guests and bills | 6-10 |
| 3 - Rooms and floors | 11-15 |

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

Questions 10 to 15 change the data. 10 to 12 are one statement each, an
INSERT, an UPDATE and a DELETE. 13 to 15 are **procedures**. SQLite has no
CREATE PROCEDURE, variables, loops or TRY/CATCH; what it has instead is
the transaction, whose steps all happen or none do, and the trigger body,
which is stored in the database and runs when something calls it.

**How they run.** Press Run and your script executes, statement by statement,
in a private in-memory copy of the database. Nothing you write can reach the
real file. The copy **persists across Runs of the same question** -- so you can
run an `UPDATE`, then a `SELECT`, and see what it did -- and **Reset** throws it
away and starts again from the seeded data. Moving to another question also
starts fresh, so no question depends on what another one wrote. If your
script ends in a statement that returns rows, the results pane shows that;
otherwise it shows the question's *probe* query, which is what **Check answer**
compares. Check always grades a fresh copy, so nothing you ran earlier can
affect the grade.

**Start each statement on a new line.** The script is split where a line
ends a complete statement, so `BEGIN;` and `COMMIT;` get lines of their
own. A CREATE TRIGGER, with the semicolons inside its body, is kept whole.

**Transactions.** `BEGIN;` opens one and `COMMIT;` makes everything since
permanent. The sandbox does not commit for you. After a script that
creates a trigger, a second Run fails because the first one's is still
there: press Reset. The same goes for a script that stopped half-way with
its transaction open.

**Driver statements.** Question 13 issues a `ROLLBACK` *after* your
script: committed work stands, and a transaction left open is undone.
Question 15 tries three bookings: one that collides with a live booking
and must be refused, one that fits exactly between two others, and one
over nights that only a cancelled booking held, both of which must get
in. Questions 10, 11, 12 and 14 are graded on what your script leaves
behind.

| # | Construct |
|---|---|
| 10 | `INSERT INTO charges (...) SELECT b.booking_id, 'restaurant', 2500 * (b.adults + b.children), '...' FROM bookings b JOIN rooms ... JOIN hotels ... WHERE ...` |
| 11 | `UPDATE guests SET tier = 'gold' WHERE guest_id IN (SELECT guest_id FROM bookings WHERE status = 'stayed' GROUP BY guest_id HAVING SUM(...) >= 100)` |
| 12 | `DELETE FROM guests WHERE joined_on < '...' AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.guest_id = guests.guest_id)` |
| 13 | `BEGIN; UPDATE bookings SET status = 'cancelled', cancelled_at = '...' WHERE ...; INSERT INTO payments (...) SELECT booking_id, '...', -amount_cents, method FROM payments WHERE ...; COMMIT;` |
| 14 | `BEGIN; INSERT INTO bookings (...) SELECT guest_id, 159, booked_at, '...', check_out, ... FROM bookings WHERE booking_id = ...; UPDATE bookings SET check_out = '...' WHERE ...; COMMIT;` |
| 15 | `CREATE TRIGGER ... BEFORE INSERT ON bookings WHEN NEW.status <> 'cancelled' AND EXISTS (SELECT 1 FROM bookings b WHERE ... overlap ...) BEGIN SELECT RAISE(ABORT, '...'); END` |

## Things the data does on purpose

- **8 hotels in four towns, two to a town, with 176 rooms between them**, so
  grouping by town is not grouping by hotel, question 1's trap. Abbey Steps
  closed on 2026-03-01 and Fellfoot Inn opened on 2025-09-01, which is why
  their totals are small.
- **96 of the 1,600 guests have never booked**, the rows a LEFT JOIN keeps in
  question 2; 34 of them joined before 2023, the ones question 12 deletes. 279
  guests have no email and 1,239 are in no loyalty tier.
- **Of 17,479 bookings, 13,625 stayed, 1,630 were cancelled, 357 never turned
  up and 1,867 have not begun**, so a question that forgets the status is
  counting nights nobody slept.
- **81 rooms were occupied on the night of 31 December 2025; BETWEEN finds
  102**, the extra ones being guests who left that morning, question 4.
- **1,563 bookings were made at the desk on the day**, a lead time of exactly
  zero in question 5, and less than zero if the time of day is left in.
- **888 cancelled bookings had some of their nights sold again, but only 655
  to a guest arriving on the same day**, the difference between an overlap and
  an equality in question 6. No two live bookings for one room overlap at all:
  the count is 0.
- **978 payments are refunds, none of them in cash**, question 7's third
  column; 1,471 stays have no charges, the ones an inner join loses in
  question 8; 1,238 of the 3,554 reviews are a score with no words.
- **82 bookings are in the house on the last night, 14 of them at Spa
  Gardens**, the ones question 10 charges for dinner.
- **32 guests have stayed a hundred nights; counting cancelled and future
  nights as well it would be 126**, question 11.
- **One room has never been booked**: 312 at Spa Gardens, a suite out of
  service, there for any question that looks for rooms with nothing.
- **The data ends at 2026-06-30 23:59**, so a date in July 2026 is always
  after everything already there.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form -- but the type counts: a tuple is not a list, and 0 is not False. A
function that prints its answer instead of returning it returns None, and
None matches nothing. The inputs are everyday values in the hotel's terms:
dates as 'YYYY-MM-DD' text for questions 1 to 5, amounts, ages, names and
email addresses for 6 to 10, room numbers and lists of rooms for 11 to
15. Each prompt shows one example call with its answer, and Run adds a
few more, including the empty list or the edge the question warns about.

**Importing is allowed.** Questions 1 to 4 use the standard library's
`datetime` module: put `from datetime import date, timedelta` at the top
of the editor, above the function.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Finding your way around (3)

One join and a GROUP BY on the key, a LEFT JOIN whose NULL rows are the guests
with no booking, and julianday on both ends of a stay to turn two dates into a
number of nights.

1. **What each hotel has to sell** (Q1342)

   For each hotel, by name: how many rooms it has, and the lowest and highest
   list price (rack_cents) among them. Two hotels can share a town, so group
   by the hotel. One join and three aggregates.

   *Return: hotel, rooms, cheapest_cents, dearest_cents*

2. **Guests on the books who have never booked** (Q1343)

   For each country: how many guests are on the books, and how many of them
   have never made a booking of any kind. Start from guests and keep every
   one, booked or not: the outer join, whose unmatched rows carry NULLs you
   can count.

   *Return: country, guests, never_booked*

3. **Room-nights sold in 2025** (Q1344)

   A stay of three nights sells three room-nights. For each hotel, by name:
   the stays that BEGAN in 2025 and the room-nights they sold, as a whole
   number. Count only bookings whose status is 'stayed' -- the guest arrived.
   check_out is the morning of departure, so the nights are the difference of
   the two dates; julianday turns a date into a number of days.

   *Return: hotel, stays, room_nights*

## 2 - Nights and dates (3)

check_in <= d AND check_out > d for a night, date() on a timestamp before it
meets a plain date, and the overlap test -- each range starts before the other
ends -- inside EXISTS.

4. **Who was in the house on New Year's Eve** (Q1345)

   For the NIGHT of 2025-12-31, each hotel by name: the rooms occupied and the
   people sleeping in them, adults and children together. Status 'stayed'
   only. A guest who checks out on the 31st left that morning and is not there
   that night; a guest who checks in on the 31st is. The range is closed at
   one end and open at the other.

   *Return: hotel, rooms_occupied, people*

5. **How far ahead each channel books** (Q1346)

   For each booking channel: its bookings, and the average number of days
   between the DAY the booking was made and the day of check-in, to one
   decimal place. Leave out cancelled bookings. booked_at is a timestamp with
   a time of day and check_in is a plain date: cut the timestamp down to its
   date before subtracting.

   *Return: channel, bookings, avg_lead_days*

6. **Cancelled nights that were sold again** (Q1347)

   When a booking is cancelled the room may be let to someone else for some or
   all of the same nights. For each hotel, by name: how many CANCELLED
   bookings had at least one of their nights taken by another booking of the
   same room that was not cancelled. Two date ranges overlap when each starts
   before the other ends; EXISTS asks whether such a booking is there.

   *Return: hotel, relet*

## 3 - Money and scores (3)

CASE inside SUM to keep takings and refunds apart, COALESCE on a LEFT JOIN to an
aggregate so that nothing means 0, and COUNT(column) beside COUNT(*) where NULL
means 'no review'.

7. **Money taken and money given back** (Q1348)

   A payment with a negative amount is a refund. For each payment method: the
   money TAKEN (the positive amounts added up) and the money REFUNDED, as a
   positive number of cents -- 0, not NULL, where there were no refunds. Two
   conditional sums in one pass.

   *Return: method, taken_cents, refunded_cents*

8. **What a stay spends on extras** (Q1349)

   For each hotel, by name: its stays (status 'stayed') and the average a stay
   spent on extras -- the charges table -- in whole cents, rounded. Many stays
   have no charges at all, and they count as stays that spent 0. Add the
   charges up per booking first, then attach that to every stay with the join
   that keeps the ones with nothing.

   *Return: hotel, stays, avg_extras_cents*

9. **How many stays are reviewed, and how well** (Q1350)

   A stay can be reviewed once it is over. For each hotel, by name, taking the
   stays (status 'stayed') that had checked out by 2026-06-30: how many stays,
   how many of them have a review, and the average score to two decimal
   places. Keep the unreviewed stays in the count: COUNT(*) and COUNT(a
   column) differ exactly where that column is NULL.

   *Return: hotel, stays, reviews, avg_score*

## 4 - Changing rows (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. One statement each: INSERT ... SELECT
with the amount worked out in the SELECT, an UPDATE fed by GROUP BY ... HAVING,
and a DELETE with a date and NOT EXISTS.

10. **The gala dinner goes on every bill** (Q1351)

    On 2026-06-30 Spa Gardens held a gala dinner, and every booking in the
    house that NIGHT is charged for it: one 'restaurant' charge dated
    2026-06-30 of 2,500 cents for each person in the booking, adults and
    children alike. Status 'stayed'; guests who left that morning were not at
    dinner. One INSERT ... SELECT, with the amount worked out in the SELECT.

    *Checked: the restaurant charges dated 2026-06-30, how many and their cents*

11. **A hundred nights makes you gold** (Q1352)

    Every guest who has STAYED a hundred nights or more in total becomes a
    gold member, whatever their tier was. Only nights of bookings with status
    'stayed' count. One UPDATE; the guests are named by a subquery that groups
    the bookings and keeps the groups that reach the total.

    *Checked: how many guests there are in each tier, NULL included*

12. **Old names that never became guests** (Q1353)

    The books are being tidied. Delete every guest who joined BEFORE
    2023-01-01 and has never made a booking of any kind. Guests with bookings,
    and anyone who joined later, stay. A DELETE whose WHERE has a date test
    and a NOT EXISTS that looks at the guest being considered.

    *Checked: guests left, the earliest joined_on among them, and how many have no email*

## 5 - Procedures (3)

Writable questions of several steps. SQLite has no CREATE PROCEDURE: a
transaction makes steps stand or fall together, the order of the steps is the
procedure, and a trigger body is a procedure the database runs for you.

13. **A cancellation, and the deposit back** (Q1354)

    Booking 13638 is for a week in August 2026 and one payment has been made
    against it, the deposit. The guest cancels at 2026-07-01 09:00. In ONE
    transaction: mark the booking cancelled with that time -- the table's
    CHECK wants the status and cancelled_at to change together -- and record
    the refund: a payment for the same booking by the same method, at
    2026-07-01 09:05, for the deposit's amount made NEGATIVE. Read the amount
    and method from the deposit; do not type them. The question then issues a
    ROLLBACK: committed work survives it.

    *Checked: the booking's status and cancelled_at, its payments and what they add up to, and the refunds in the whole table*

14. **A guest who changed rooms mid-stay** (Q1355)

    Booking 11988 records guest 441 in room 155 at Lakeside Lodge from
    2026-03-06 to 2026-03-13. In fact the guest moved to room 159 on
    2026-03-10 and spent the last three nights there. Put the records right in
    one transaction, as two bookings: 11988 ends on the 10th, and a NEW
    booking for room 159 runs from the 10th to the ORIGINAL check-out, with
    every other column copied from 11988. Think about which of the two steps
    must read the row before the other changes it.

    *Checked: guest 441's bookings that begin from 6 to 12 March 2026: room, check-in, check-out, rate and status*

15. **No room is sold twice** (Q1356)

    Nothing in the schema stops two bookings for the same room on the same
    night. Store the check as a trigger: BEFORE INSERT on bookings, when the
    new booking is not itself cancelled and another booking for that room,
    also not cancelled, overlaps its dates, the insert is refused with
    RAISE(ABORT, ...). A guest may arrive on the day another leaves; cancelled
    bookings block nothing. The question then tries three bookings for July
    and August 2026: one that collides, one that fits exactly between two
    others, and one over nights that only a cancelled booking held.

    *Checked: room and dates of the bookings made after the data ends*

# Python

## 1 - Dates, with datetime (5)

date.fromisoformat to get in and .isoformat() to get out, subtraction for .days
and timedelta for adding, weekday() as an index into a list that starts on
Monday, range for the nights, and < both ways for a collision.

1. **How many nights is the stay?** (P611)

   Dates arrive as 'YYYY-MM-DD' text. Write a function `nights(check_in,
   check_out)` that returns the number of nights between them. `from datetime
   import date` gives you date.fromisoformat(text); one date minus another is
   a length of time with a .days.

   ```
   nights("2026-03-06", "2026-03-13") -> 7
   nights("2026-01-30", "2026-02-02") -> 3
   ```

   *Return: an int.*

2. **The morning they leave** (P612)

   Write a function `check_out_date(check_in, nights)` that returns the date
   so many nights after check_in, as 'YYYY-MM-DD' text. From datetime, a
   timedelta(days=n) can be added to a date, and a date has .isoformat() to
   turn it back into text.

   ```
   check_out_date("2026-01-30", 3) -> "2026-02-02"
   ```

   *Return: a str.*

3. **What day of the week is that?** (P613)

   Write a function `day_name(day)` that returns the English name of the
   weekday for a 'YYYY-MM-DD' date. A date has a .weekday() method that gives
   a number: 0 for Monday up to 6 for Sunday. Use it to pick from a list of
   names.

   ```
   day_name("2026-06-01") -> "Monday"
   day_name("2026-03-08") -> "Sunday"
   ```

   *Return: a str.*

4. **Every night of the stay** (P614)

   Write a function `stay_nights(check_in, check_out)` that returns the date
   of every night of the stay as 'YYYY-MM-DD' text, in order. The first night
   is check_in; check_out is the morning of departure and is NOT a night.
   range, and a timedelta for each step.

   ```
   stay_nights("2026-03-06", "2026-03-09") -> ["2026-03-06", "2026-03-07", "2026-03-08"]
   ```

   *Return: a list of str.*

5. **Do the two stays collide?** (P615)

   Two stays in the same room, each a check-in and a check-out as 'YYYY-MM-DD'
   text. Write a function `collide(in_a, out_a, in_b, out_b)` that returns
   True if they share at least one night. One guest leaving on the morning the
   other arrives is NOT a collision. Dates in this form compare correctly as
   plain text, so no conversion is needed.

   ```
   collide("2026-08-05", "2026-08-09", "2026-08-08", "2026-08-10") -> True
   collide("2026-08-04", "2026-08-05", "2026-08-05", "2026-08-09") -> False
   ```

   *Return: a bool.*

## 2 - Guests and bills (5)

// for the share and % for the cents left over, >= at the boundary age, a case
each for none, one and several, one @ before the split, and a length test before
the footnote.

6. **A bill split so that it adds up** (P616)

   Write a function `split_bill(total_cents, people)` that returns a list of
   what each person pays, in whole cents. The shares must add up to the total
   exactly: everyone pays the same, except that the first few pay one cent
   more when the total does not divide evenly. // and % give the share and
   what is left over.

   ```
   split_bill(10000, 3) -> [3334, 3333, 3333]
   ```

   *Return: a list of int.*

7. **Adults and children in the party** (P617)

   Write a function `party(ages)` that takes the ages of the guests in a
   booking and returns two numbers: how many are adults and how many are
   children. Anyone aged 18 or over is an adult.

   ```
   party([34, 36, 8, 5]) -> (2, 2)
   party([18]) -> (1, 0)
   ```

   *Return: a tuple of two ints, adults first.*

8. **A booking's guests on one line** (P618)

   The arrivals list has room for one line per booking. Write a function
   `guest_line(names)` that returns the first guest's name, followed by ' + '
   and the number of OTHER guests when there are any. A single guest is just
   their name; no guests is the empty string.

   ```
   guest_line(["Agnes Devlin", "Hugo Devlin", "Mei Devlin"]) -> "Agnes Devlin + 2"
   guest_line(["Agnes Devlin"]) -> "Agnes Devlin"
   ```

   *Return: a str.*

9. **Does that look like an email address?** (P619)

   Write a function `looks_like_email(text)` for a first check on a form. It
   returns True only if the text has exactly ONE '@', something before it, and
   after it a part that contains a dot which is neither its first nor its last
   character.

   ```
   looks_like_email("agnes.devlin7@example.org") -> True
   looks_like_email("@example.org") -> False
   looks_like_email("agnes@example") -> False
   ```

   *Return: a bool.*

10. **A long guest list, cut short** (P620)

    Write a function `short_list(names, limit)` that returns the names
    unchanged if there are no more than `limit` of them. If there are more, it
    returns the first `limit` names followed by one extra item saying how many
    were left off: 'and 2 more'.

    ```
    short_list(["Agnes", "Hugo", "Mei", "Niall", "Pavel"], 3) -> ["Agnes", "Hugo", "Mei", "and 2 more"]
    short_list(["Agnes", "Hugo"], 3) -> ["Agnes", "Hugo"]
    ```

    *Return: a list of str.*

## 3 - Rooms and floors (5)

A slice that stops two from the end, min to stop at the top of a ladder, int()
in the test and the string in the result, extend where append would nest, and a
paired assignment for a swap.

11. **Which floor is the room on?** (P621)

    A room number is the floor followed by a two-digit room: '204' is floor 2,
    room 4, and in a tall hotel '1204' is floor 12. Write a function
    `floor_of(room_no)` that returns the floor as an int. Count from the END
    of the string, where the layout is fixed.

    ```
    floor_of("204") -> 2
    floor_of("1204") -> 12
    ```

    *Return: an int.*

12. **An upgrade, if there is one** (P622)

    Room types run from the plainest to the best in a list. Write a function
    `upgrade(kind, ladder)` that returns the type one step up from `kind`. A
    guest already in the best type stays where they are. kind is always in the
    list.

    ```
    upgrade("twin", ["single", "twin", "double", "family", "suite"]) -> "double"
    upgrade("suite", ["single", "twin", "double", "family", "suite"]) -> "suite"
    ```

    *Return: a str.*

13. **The rooms that face the sea** (P623)

    At Harbour Lights the odd-numbered rooms face the sea. Write a function
    `sea_view(rooms)` that takes room numbers as strings and returns the odd-
    numbered ones, in order, still as strings. A whole number is odd when the
    remainder on dividing by 2 is 1.

    ```
    sea_view(["201", "202", "203", "210", "215"]) -> ["201", "203", "215"]
    ```

    *Return: a list of str.*

14. **Every room on every floor** (P624)

    The housekeeping sheet lists rooms floor by floor: a list of lists. Write
    a function `all_rooms(floors)` that returns every room number in ONE flat
    list, in the same order. A list has two ways of adding to itself, and they
    differ on exactly this.

    ```
    all_rooms([["101", "102"], ["201"], ["301", "302", "303"]]) -> ["101", "102", "201", "301", "302", "303"]
    ```

    *Return: a list of str.*

15. **Two guests swap rooms** (P625)

    A list holds the guest in each room, room by room. Write a function
    `swap_guests(guests, i, j)` that returns a NEW list in which the guests at
    positions i and j have changed places. The list passed in is not altered.
    Python can assign to two things at once.

    ```
    swap_guests(["Agnes", "Hugo", "Mei", "Niall"], 0, 2) -> ["Mei", "Hugo", "Agnes", "Niall"]
    ```

    *Return: a list.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,951 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
