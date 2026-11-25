# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the hotel schema, the fourth
set on it. Ten questions go back to what the third set found hard, each in a new
task: a table joined to itself, a test on a whole group in HAVING, a DELETE
aimed at the table the rows are really in, a view that later statements read,
and carrying every condition a task states into the statement, down to the exact
value. Five use a tool these tables have not met: a row value, INTERSECT and
EXCEPT, a window frame, ALTER TABLE ... ADD COLUMN, and a unique index. Two
tools per question, with the tiers named by task. Nine read the data and **six
change it**: three single statements and three procedures of several steps. The
prompts name the tool but do not write the statement. **Fifteen Python** at the
easy level of the last fourteen sets: everyday tasks over plain lists and
strings in the hotel's terms, with no maths, no dicts and nothing to import.

**The database is the one the last three sets used.** If the app offers to
re-seed when it starts, accept; from a terminal it is `python seed.py`.

**The four statuses of a booking are 'booked', 'stayed', 'cancelled' and
'no_show'**, and there are no others: a booking not yet arrived is 'booked', and
one that was slept in is 'stayed', whether the guest has left or is still in the
house.

| Stage | SQL questions |
|---|---|
| 1 - Hotels and their rooms | 1-3 |
| 2 - Guests | 4-6 |
| 3 - Money and time | 7-9 |
| 4 - Changing rows | 10-12 |
| 5 - Procedures | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Times and numbers | 1-5 |
| 2 - Text as it is typed | 6-10 |
| 3 - Lists and registers | 11-15 |

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

Questions 10 to 15 change the data. 10 to 12 are one statement each: a DELETE
and two UPDATEs. 13 to 15 are **procedures**. SQLite has no CREATE PROCEDURE,
variables, loops or TRY/CATCH; what it has instead is a script whose steps
depend on each other, the view, which is a query stored under a name, and the
index, which is a rule stored in the database and enforced from then on.

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
complete statement. A statement may run over several lines.

**Run it twice and it fails.** After a script that adds a column, creates a view
or creates an index, a second Run stops because the first one's is still there:
press Reset. A statement that breaks a CHECK or a foreign key stops the script
at that statement, and whatever ran before it has already happened.

**Before a DELETE or an UPDATE, run its WHERE as a SELECT COUNT(*).** The
figures to expect are in the list below: 34 charges in question 10, 176 guests
in question 11, 46 bookings in question 12.

**Driver statements.** Question 15 runs six statements *after* your script.
Three guests are inserted: one with an email another guest has, one with no
email, one with a new email. Then, for room 170 on 2026-07-19, which has a live
booking already: a second live booking, a cancelled booking, and an UPDATE that
tries to turn the cancelled one back into a live one. The first, fourth and
sixth must be refused. Questions 10 to 14 are graded on what your script leaves
behind.

| # | Construct |
|---|---|
| 10 | `DELETE FROM charges WHERE kind = '...' AND charged_on >= '...' AND booking_id IN (SELECT b.booking_id FROM bookings b JOIN guests g ON ... JOIN rooms r ON ... WHERE g.tier = '...' AND r.hotel_id = 5)` |
| 11 | `UPDATE guests SET tier = 'silver' WHERE tier IS NULL AND guest_id IN (SELECT b.guest_id FROM bookings b JOIN rooms r ON ... WHERE b.status = '...' GROUP BY b.guest_id HAVING COUNT(DISTINCT r.hotel_id) >= 7)` |
| 12 | `UPDATE bookings SET status = 'cancelled', cancelled_at = '...' WHERE status = '...' AND check_in < '...' AND check_out > '...' AND room_id IN (SELECT room_id FROM rooms WHERE hotel_id = 7)` |
| 13 | `ALTER TABLE guests ADD COLUMN last_stay TEXT; UPDATE guests SET last_stay = (SELECT MAX(b.check_out) FROM bookings b WHERE b.guest_id = guests.guest_id AND ...); UPDATE guests SET email = NULL WHERE last_stay < '...' OR last_stay IS NULL` |
| 14 | `CREATE VIEW hotel_scores AS SELECT r.hotel_id, COUNT(*) AS reviews, AVG(v.score) AS avg_score FROM reviews v JOIN bookings b ON ... JOIN rooms r ON ... GROUP BY r.hotel_id; UPDATE hotels SET stars = stars + 1 WHERE stars < 5 AND hotel_id IN (SELECT hotel_id FROM hotel_scores WHERE ...); UPDATE hotels SET stars = stars - 1 WHERE stars > 2 AND hotel_id IN (SELECT hotel_id FROM hotel_scores WHERE ...)` |
| 15 | `UPDATE guests SET email = NULL WHERE EXISTS (SELECT 1 FROM guests o WHERE o.email = guests.email AND o.guest_id < guests.guest_id); CREATE UNIQUE INDEX ... ON guests (email); CREATE UNIQUE INDEX ... ON bookings (room_id, check_in) WHERE status IN ('...', '...')` |

## Things the data does on purpose

- **8 hotels in four towns, with 176 rooms between them.** Many rooms are alike:
  84 pairs share a hotel, a kind, a floor and a list price, 27 of them at
  Lakeside Lodge, and a self-join that does not order the pair finds 168,
  question 1.
- **February is quiet.** Eleven rooms had fewer than two stays arriving in
  February 2026, and one of them, 312 at Spa Gardens, had none, the zero
  question 2 has to show as 0.
- **A room's top rate is often an ordinary rate somewhere else.** Fellfoot Inn's
  fourteen rooms reached their best price on 25 stays; 129 stays there were at a
  rate that is the record for one room or another, question 3.
- **39 times a guest held two bookings for the same arrival day, cancelled one
  and stayed in the other.** In 24 of them the stay was the cheaper of the two.
  Five more cancelled bookings share a guest and a day with a booking that was
  itself cancelled or has not arrived, question 4.
- **Only 37 guests have kept to one hotel, and only five of those have stayed
  three times or more.** 1,635 pairs of guest and hotel have three stays or
  more, which is what question 5 counts if it is grouped by both.
- **286 guests have stayed at both Keswick hotels, 37 of them never at Spa
  Gardens.** 223 have stayed at one or the other and never at Spa Gardens,
  question 6.
- **Charges exist only on stays.** Sixteen stays ran up extras of more than
  twice the cost of the room; only three did it with a single charge, question
  7.
- **Eighteen months of stays, January 2025 to June 2026**, with room revenue
  from 14,211,150 cents in February 2025 to 33,071,850 in July 2025, question 8.
  2026 is ahead of 2025 in every month from January to May and 15 stays behind
  in June, question 9.
- **Gold members at Spa Gardens have 129 parking charges, 34 of them dated
  2026**, 61,200 cents, question 10.
- **225 guests have stayed at seven or more different hotels.** 176 are in no
  tier, 37 are silver already and 12 are gold, question 11.
- **Lakeside Lodge has 280 bookings not yet arrived. 46 of them include a night
  between 3 and 16 August 2026**: 38 arrive in that fortnight and eight arrive
  before it and are still there. Five more check out on the 3rd and two check in
  on the 17th, and are not affected, question 12.
- **99 of the 1,600 guests have never stayed, 82 of them with an email.**
  Another 145 guests with an email last left before 2026, question 13.
- **Average review scores run from 3.202 at Fellfoot Inn to 4.6 at Spa
  Gardens.** Castle View has 4.115 from 723 reviews and Lakeside Lodge 4.193
  from 513; The Old Mill's 3.777 and Station House's 3.753 are below 3.78 and
  Harbour Lights' 3.794 is not, question 14.
- **One email address is on two guests**, 870 and 1502, both called Ottilie
  Bianchi. 279 guests have no email. No room has two live bookings arriving on
  the same day, but 655 times a room and a day are shared by two bookings of
  which at least one is cancelled or a no-show, question 15.
- **The data ends at 2026-06-30 23:59**, so a booking with status 'booked' is
  always in the future, the latest of them arriving in February 2027.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function with
the name the question gives, Run calls it once for each test input and shows
every call and its result in the output pane, and Check compares each result
with the reference function's. Values are compared, not their printed form --
but the type counts: a tuple is not a list, 8500.0 is not 8500, and the string
'yes' is not True. A function that prints its answer instead of returning it
returns None, and None matches nothing. The inputs are everyday values in the
hotel's terms: clock times, cents and meter readings for questions 1 to 5, text
as guests and staff type it for 6 to 10, lists of names, scores and rooms for 11
to 15. Each prompt shows one or two example calls with their answers, and Run
adds a few more, including the empty list or the edge the question warns about.

**Nothing needs importing in this set.** Question 4 returns None when nothing
passes, question 14 is given a list of lists, and questions 8 and 13 return True
or False, not 1 or 0.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the database,
the app, or any file. Tab inserts four spaces and Return keeps the indentation
of the line above.

# SQL

## 1 - Hotels and their rooms (3)

A table joined to itself with each pair listed once, an outer join whose count
is tested in HAVING, and a row value: two columns compared at once with a
subquery that returns two.

1. **Rooms that can stand in for each other** (Q1387)

   When a room is out of order the desk moves its guest to one exactly like it.
   List every pair of interchangeable rooms: two different rooms in the same
   hotel, of the same kind, on the same floor, with the same list price
   (rack_cents). A self-join again: rooms joined to itself under two aliases.
   Last time the dates said which copy played which part. Here nothing does, and
   a plain 'not the same room' lists every pair twice, once each way round. Each
   pair must appear once, the room with the lower room_id first.

   *Return: hotel, first_room, second_room, rack_cents -- the hotel's name and the two room_no values*

2. **Rooms February nearly forgot** (Q1388)

   February is the quiet month. Which rooms, in any hotel, had fewer than two
   stays (status 'stayed') ARRIVING in February 2026 -- check_in from 2026-02-01
   up to but not including 2026-03-01? A room with no such stay at all belongs
   in the answer, with 0. Two things met before, now together: an outer join
   from the rooms, with the conditions on the booking written where an empty
   room survives them, and a test on the group's count, which belongs in HAVING.
   Mind what you count: one of the two ways of counting gives an empty room 1.

   *Return: hotel, room_no, stays -- hotel is its name*

3. **The best price each room ever fetched** (Q1389)

   For each room at Fellfoot Inn (hotel 8), find the stay or stays (status
   'stayed') that paid the highest rate_cents that room has ever been let for. A
   room whose top rate was paid more than once has a row for each of those
   stays. A grouped query gives each room its top rate. The bookings wanted are
   those that match it on BOTH things at once, the room and the rate. A row
   value -- two columns in brackets -- can be compared with a subquery that
   returns two columns.

   *Return: room_no, booking_id, check_in, rate_cents*

## 2 - Guests (3)

The self-join again with a status for each alias, two tests on one group in a
single HAVING, and INTERSECT and EXCEPT to compare whole lists.

4. **Two bookings held, one let go** (Q1390)

   Some guests hold two bookings for the same arrival day and let one of them
   go. Find every pair of bookings by the same guest with the same check_in in
   which one was cancelled (status 'cancelled') and the other became a stay
   (status 'stayed'). The self-join once more: bookings under two aliases, and
   this time it is the status that gives each copy its part, so every pair comes
   out once. Put the nightly rate of the booking that was dropped beside the
   rate of the one that was kept.

   *Return: guest_id, check_in, cancelled_booking, stay_booking, cancelled_rate, stay_rate*

5. **Guests who never try anywhere else** (Q1391)

   Most guests move round the group. Which guests have stayed (status 'stayed')
   at least three times and always at the SAME hotel? Two tests on one group,
   both in the same HAVING: one on how many stays the guest has, one on how many
   DIFFERENT hotels they were at. The group is the guest, not the guest and the
   hotel. Give the hotel's name as well; in a group with only one hotel in it,
   MIN or MAX of the name is that hotel.

   *Return: guest_id, name, hotel, stays -- name is the guest's, hotel is the hotel's name*

6. **Both Keswick hotels, never Spa Gardens** (Q1392)

   Keswick has two hotels, Lakeside Lodge (hotel 7) and Fellfoot Inn (hotel 8).
   Which guests have stayed (status 'stayed') at BOTH of them and have never
   stayed at Spa Gardens (hotel 5)? UNION ALL stacked one list on another; its
   relatives compare lists. INTERSECT keeps what is in both of two lists, and
   EXCEPT takes one list away from another. Three lists of guest_ids, one for
   each hotel, with those two words between them.

   *Return: guest_id*

## 3 - Money and time (3)

A sum that has to be tested in HAVING because no single row can answer, a window
frame for a moving average, and a CTE joined to itself to set one year beside
another.

7. **Stays where the extras outran the room** (Q1393)

   Now and then a guest takes a cheap room and lives well. Find the bookings
   whose extras -- ALL their charges added together -- come to more than twice
   the cost of the room, which is nights times rate_cents. Charges exist only on
   stays, so no status test is needed. The test is on a booking's charges taken
   together, a whole group of rows, so it cannot be a WHERE on one charge:
   group, and test the sum in HAVING.

   *Return: booking_id, room_cents, extras_cents*

8. **A three-month moving average of room revenue** (Q1394)

   Room revenue is nights times rate_cents, for stays (status 'stayed'). Give it
   for each month of check_in, written 'YYYY-MM', for all eighteen months of
   data. Beside it put the average of that month and the two months before it, a
   three-month moving average, which smooths the seasons out. The first month
   has nothing before it and averages itself alone; the second averages two. A
   window frame: after the window's ORDER BY, a ROWS BETWEEN clause says how far
   back from the current row the window reaches. It is laid over a grouped
   query, as the running total was. The average is compared to two decimal
   places.

   *Return: month, room_cents, avg3*

9. **This year against last, month by month** (Q1395)

   Is 2026 ahead of 2025? Count the stays (status 'stayed') by the year and the
   month of check_in, once, in a CTE. Then join that CTE to ITSELF: one alias
   plays 2025 and the other 2026, matched month to month, for January to June,
   the six months 2026 has. A named query can be joined to itself exactly as a
   table can. Give the month as strftime writes it, two characters of text, and
   the change as 2026 minus 2025.

   *Return: month, stays_2025, stays_2026, change*

## 4 - Changing rows (3)

Writable, one statement each: a DELETE from a child table chosen by facts three
tables away, an UPDATE fed by GROUP BY and HAVING that must leave some rows
alone, and an UPDATE of two columns with four conditions to carry.

10. **Gold members park free at Spa Gardens** (Q1396)

    Spa Gardens (hotel 5) has decided that gold members park free, back-dated to
    the start of 2026. Delete every charge of kind 'parking' with a charged_on
    of 2026-01-01 or later that sits on a booking at Spa Gardens made by a guest
    whose tier is 'gold'. The rows to go are charges and nothing else: the
    bookings, the guests and all their other charges stay. But the facts that
    pick them out are three tables away -- the tier is on the guest and the
    hotel is on the room -- so they are reached through a subquery on
    booking_id. One statement.

    *Checked: charges, split by Spa Gardens or not, gold or not, and kind: how many, their total, and how many are dated 2026*

11. **Seven hotels makes you silver** (Q1397)

    The loyalty scheme gets a new way in: a guest who has stayed (status
    'stayed') at seven or more DIFFERENT hotels becomes 'silver'. It applies
    only to guests who are in no tier yet (tier is NULL). Nobody who is already
    silver or gold is touched, least of all moved down. Find the guests with
    GROUP BY and HAVING, as a list of guest_ids, and let one UPDATE of the
    guests table use the list.

    *Checked: for each tier, the number of guests and the sum of their guest_ids*

12. **Lakeside Lodge shuts for a fortnight** (Q1398)

    Lakeside Lodge (hotel 7) closes for repairs. Nobody can sleep there on the
    nights of 2026-08-03 to 2026-08-16, and it reopens on the 17th. Cancel every
    booking not yet arrived (status 'booked') at that hotel that includes any of
    those nights: set its status to 'cancelled' and its cancelled_at to exactly
    '2026-06-30 12:00'. A stay is a half-open range, so a guest who checks OUT
    on 3 August, or checks IN on 17 August, is not affected -- and one who
    arrives on 1 August and leaves on the 5th is. The table has a CHECK that a
    booking is cancelled exactly when cancelled_at is filled in, so both columns
    change in the one UPDATE. Count the conditions in this paragraph before you
    run it.

    *Checked: for Lakeside Lodge and for the other hotels together, by status: bookings, how many have a cancelled_at, and how many were cancelled at '2026-06-30 12:00'*

## 5 - Procedures (3)

Writable questions of several steps, each step needing the one before. SQLite
has no CREATE PROCEDURE: a column is added and then filled, a view stores a
query for later statements to read, and a unique index is a rule the database
enforces by itself.

13. **A column for the last stay, and a shorter mailing list** (Q1399)

    Three steps, each needing the one before. The guests table is to remember
    when each guest last stayed. Add a column called last_stay to guests with
    ALTER TABLE ... ADD COLUMN; it will hold a date as text, and it starts out
    NULL in every row. Fill it: for each guest, the latest check_out among their
    stays (status 'stayed'), left NULL for a guest who has never stayed. Then
    use it. The mailing list is to drop everyone who has not stayed since the
    start of 2026: set email to NULL for every guest whose last_stay is before
    '2026-01-01', AND for every guest who has never stayed at all. Remember what
    a comparison with NULL gives.

    *Checked: guests; how many have a last_stay, the earliest and the latest; how many still have an email; and how many of those have no stay in 2026*

14. **Stars that follow the reviews** (Q1400)

    The group will let its guests decide the stars. First create a VIEW called
    hotel_scores with one row for each hotel and exactly these columns:
    hotel_id, reviews (how many reviews its stays have had) and avg_score (their
    average score). A review knows its booking, a booking its room, and a room
    its hotel. Then two UPDATEs of the hotels table, each reading the view. A
    hotel GAINS a star if its avg_score is 4.1 or more, AND it has at least 600
    reviews, AND it has fewer than 5 stars. A hotel LOSES a star if its
    avg_score is below 3.78 AND it has more than 2 stars. A CHECK keeps stars
    between 2 and 5, and one row that breaks it stops the whole statement. Five
    conditions; each is in the statement or it is not.

    *Checked: each hotel's stars, with its reviews and avg_score (to three decimal places) from the view*

15. **Two rules the database keeps by itself** (Q1401)

    Three steps. Rule one: no two guests share an email. One address is on two
    guests today, so first set email to NULL on every guest for whom ANOTHER
    guest exists with the same email and a lower guest_id -- a row compared with
    the rest of its own table, the self-join's idea inside an UPDATE. Then
    CREATE UNIQUE INDEX on the email column of guests; NULLs never count as
    equal, so guests with no email do not collide. Rule two: a room cannot have
    two LIVE bookings (status 'booked' or 'stayed') arriving on the same day.
    Cancelled bookings and no-shows often share a room and a day with a live
    one, so this unique index, on room_id and check_in together, needs a WHERE
    of its own: a partial index. The question then runs six statements, three of
    which the rules must refuse.

    *Checked: guests, emails and different emails; the test guests who got in; room 170's bookings for 2026-07-19 by status*

# Python

## 1 - Times and numbers (5)

split and int on a clock time, a percentage kept in whole numbers, range
counting down, a loop that returns at the first hit, and a loop over positions
that must start at 1.

1. **Half past two, in minutes** (P656)

   Times are easier to compare as one number. Write a function
   `to_minutes(clock)` that takes a time written as hours, a colon and minutes,
   and returns the number of minutes since midnight. split cuts the text at the
   colon; the two pieces are still text, and int turns each into a number,
   leading zero or not.

   ```
   to_minutes('14:30') -> 870
   to_minutes('00:05') -> 5
   ```

   *Return: an int.*

2. **Fifteen per cent off** (P657)

   A rate in cents is reduced by a whole-number percentage. Write a function
   `discounted(cents, percent)` that returns the reduced price in whole cents,
   any fraction of a cent dropped. percent runs from 0 to 100. What is left
   after 15 per cent off is 85 per cent: multiply by that first, then divide by
   100 with the operator that keeps the answer a whole number.

   ```
   discounted(10000, 15) -> 8500
   discounted(333, 50) -> 166
   ```

   *Return: an int.*

3. **Three nights left, two, one** (P658)

   The lobby screen counts a guest's stay down. Write a function
   `nights_left(n)` that returns a list of the whole numbers from n down to 1.
   With n of 0 the list is empty. range can count backwards if its third
   argument is negative; it still stops BEFORE its second argument, so think
   about what that has to be.

   ```
   nights_left(3) -> [3, 2, 1]
   nights_left(0) -> []
   ```

   *Return: a list of ints.*

4. **The first charge over the limit** (P659)

   The night auditor reads down a bill looking for the first charge that needs a
   manager's signature. Write a function `first_over(amounts, limit)` that
   returns the FIRST amount in the list that is greater than limit, or None if
   no amount is. An amount equal to the limit is not over it. A return inside a
   loop ends the function there and then.

   ```
   first_over([1200, 4500, 800, 9000], 4000) -> 4500
   first_over([1200, 800], 4000) -> None
   ```

   *Return: an int, or None.*

5. **What the meter says each morning** (P660)

   The laundry's water meter is read every morning and only ever goes up. Write
   a function `daily_use(readings)` that returns a list of how much was used
   between each reading and the next: each reading less the one before it. Four
   readings give three differences; one reading, or none, gives an empty list.
   Walk the positions with range -- and choose where to start.

   ```
   daily_use([100, 130, 135, 180]) -> [30, 5, 45]
   daily_use([50]) -> []
   ```

   *Return: a list of ints.*

## 2 - Text as it is typed (5)

split and join as a pair, a slice that leaves room for its dots, any against
all, range's missing far end, and a rule about the last two that needs its small
cases.

6. **One space between words, none at the ends** (P661)

   Notes typed in a hurry have spaces everywhere. Write a function
   `tidy_spaces(text)` that returns the text with exactly one space between
   words and none at either end. A text of nothing but spaces becomes ''. split
   with no argument cuts at any run of spaces, however long, and join puts the
   pieces back with whatever you choose between them.

   ```
   tidy_spaces('  late   check-out  please ') -> 'late check-out please'
   tidy_spaces('   ') -> ''
   ```

   *Return: a string.*

7. **A name that fits on the label** (P662)

   A label printer has room for `width` characters. Write a function
   `fit_label(text, width)`: a text that fits is returned as it is; a longer one
   is cut short and ends in three full stops, and the result -- dots included --
   is exactly width characters long. width is never less than 3. len measures a
   string and a slice takes the front of it.

   ```
   fit_label('Lakeside Lodge', 10) -> 'Lakesid...'
   fit_label('Spa', 10) -> 'Spa'
   ```

   *Return: a string.*

8. **Is there a number in it?** (P663)

   A form rejects an address line with no number anywhere in it. Write a
   function `has_digit(text)` that returns True if at least one character of the
   text is a digit, and False otherwise, the empty text included. A for loop
   over a string hands over one character at a time, and a string has a method
   that says whether it is made of digits.

   ```
   has_digit('Room 12 please') -> True
   has_digit('no number here') -> False
   ```

   *Return: a bool.*

9. **Rooms 101 to 105** (P664)

   Housekeeping's job sheet says '101-105', meaning every room from 101 to 105,
   BOTH ends included. Write a function `room_range(text)` that returns those
   room numbers as a list of ints. The first number is never larger than the
   second; there may be spaces round the hyphen, which int ignores. split, int,
   and range -- remembering where range stops.

   ```
   room_range('101-105') -> [101, 102, 103, 104, 105]
   room_range('204-204') -> [204]
   ```

   *Return: a list of ints.*

10. **Ada, Hugo and Mei** (P665)

    A welcome card lists the party the way a person would write it. Write a
    function `name_list(names)` that joins the names with a comma and a space,
    except that the last two are joined by the word 'and' with a space each
    side. One name is returned by itself, and an empty list gives ''. names[:-1]
    is every name but the last and names[-1] is the last.

    ```
    name_list(['Ada', 'Hugo', 'Mei']) -> 'Ada, Hugo and Mei'
    name_list(['Ada', 'Hugo']) -> 'Ada and Hugo'
    name_list(['Ada']) -> 'Ada'
    ```

    *Return: a string.*

## 3 - Lists and registers (5)

index with a guard, sorted with a direction, neighbours compared, one column
taken from a list of rows, and a loop that carries two counts.

11. **Where am I in the queue?** (P666)

    Guests wait for a taxi in the order of a list. Write a function
    `queue_place(queue, name)` that returns the guest's place counted the way
    people count -- 1 for the front -- and 0 if the name is not in the queue. If
    the name is there twice, the first one counts. A list's index method finds a
    value's position, counted from 0, and raises an error when the value is
    missing, so ask with `in` first.

    ```
    queue_place(['Ada', 'Hugo', 'Mei'], 'Hugo') -> 2
    queue_place(['Ada', 'Hugo', 'Mei'], 'Zeno') -> 0
    ```

    *Return: an int.*

12. **The three best scores** (P667)

    A hotel wants its three best review scores for the poster. Write a function
    `top_three(scores)` that returns a NEW list of the three highest scores, the
    highest first. With fewer than three scores it returns them all, still
    highest first. Equal scores each count. sorted returns a new sorted list and
    can be told to sort downwards; a slice takes the front.

    ```
    top_three([3, 5, 1, 4, 2]) -> [5, 4, 3]
    top_three([2]) -> [2]
    ```

    *Return: a list of ints.*

13. **Is the list in order?** (P668)

    The cleaning round should run through the rooms in rising order. Write a
    function `in_order(rooms)` that returns True when no room number is lower
    than the one before it, and False as soon as one is. Two equal numbers in a
    row are in order. An empty list and a list of one are in order too. Compare
    each item with its neighbour.

    ```
    in_order([101, 102, 205]) -> True
    in_order([101, 205, 102]) -> False
    ```

    *Return: a bool.*

14. **Just the names from the register** (P669)

    The register is a list of rows, and each row is a small list: a name, a room
    and a number of nights. Write a function `names_only(register)` that returns
    a list of just the names, one for each row, in order, repeats and all. The
    loop hands over one ROW at a time; the name is the first thing in it.

    ```
    names_only([['Ada', 101, 2], ['Hugo', 204, 1]]) -> ['Ada', 'Hugo']
    names_only([]) -> []
    ```

    *Return: a list of strings.*

15. **The longest run of nights let** (P670)

    A room's month is a list with a 1 for each night it was let and a 0 for each
    night it stood empty. Write a function `longest_run(nights)` that returns
    the length of the longest unbroken run of 1s, and 0 if there is none. Carry
    two numbers through the loop: the length of the run you are in, and the best
    seen so far. A 0 ends a run -- and so does the end of the list.

    ```
    longest_run([1, 1, 0, 1, 1, 1, 0]) -> 3
    longest_run([0, 1, 1]) -> 2
    ```

    *Return: an int.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
2,041 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
