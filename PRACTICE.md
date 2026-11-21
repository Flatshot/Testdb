# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the hotel schema, the second
set on it: ten questions use a tool these tables have not met, and five return
to what the first set found hard -- overlapping ranges, EXISTS, arithmetic done
row by row, a subquery feeding an UPDATE -- in a different task. Two tools per
question, with the tiers named by task. Nine read the data and **six change
it**: three single statements and three procedures of several steps. The prompts
name the tool but do not write the statement. **Fifteen Python** at the easy
level of the last twelve sets: everyday tasks over plain lists and strings in
the hotel's terms, with no maths, no dicts and, this time, no datetime.

**The database is the one the last set used.** If the app offers to re-seed when
it starts, accept; from a terminal it is `python seed.py`.

| Stage | SQL questions |
|---|---|
| 1 - Rooms and what they cost | 1-3 |
| 2 - Guests over time | 4-6 |
| 3 - Money in and out | 7-9 |
| 4 - Changing rows | 10-12 |
| 5 - Procedures | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Bills and counting | 1-5 |
| 2 - Names and notes | 6-10 |
| 3 - Rooms and rotas | 11-15 |

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

Questions 10 to 15 change the data. 10 to 12 are one statement each: an INSERT
that may turn into an UPDATE, an UPDATE and a DELETE. 13 to 15 are
**procedures**. SQLite has no CREATE PROCEDURE, variables, loops or TRY/CATCH;
what it has instead is the transaction, whose steps all happen or none do, and
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
table or a trigger, a second Run fails because the first one's is still there:
press Reset. The same goes for a script that stopped half-way with its
transaction open.

**Driver statements.** Question 13 issues a `ROLLBACK` *after* your script:
committed work stands, and a transaction left open is undone. Question 15 runs
three updates at Fellfoot Inn: its four twins go up by 300 cents, which must be
logged; its three ground-floor singles are set to 4,550, which only one of them
is not already; and one room's `sleeps` is altered, which is no change of price
at all. Questions 10, 11, 12 and 14 are graded on what your script leaves
behind.

| # | Construct |
|---|---|
| 10 | `INSERT INTO reviews (booking_id, score, posted_on, headline) VALUES (...), (...) ON CONFLICT (booking_id) DO UPDATE SET score = excluded.score, ...` |
| 11 | `UPDATE rooms SET rack_cents = (SELECT ROUND(AVG(b.rate_cents)) FROM bookings b WHERE b.room_id = rooms.room_id AND ...) WHERE hotel_id = 5 AND EXISTS (SELECT 1 FROM bookings b WHERE b.room_id = rooms.room_id AND ...)` |
| 12 | `DELETE FROM reviews WHERE review_id IN (SELECT review_id FROM (SELECT v.review_id, ROW_NUMBER() OVER (PARTITION BY b.guest_id, r.hotel_id ORDER BY v.posted_on DESC, v.review_id DESC) AS n FROM reviews v JOIN ...) WHERE n > 1)` |
| 13 | `BEGIN; UPDATE guests SET email = (SELECT email FROM guests WHERE guest_id = 1218) WHERE guest_id = 1425; UPDATE bookings SET guest_id = 1425 WHERE guest_id = 1218; DELETE FROM guests WHERE guest_id = 1218; COMMIT;` |
| 14 | `BEGIN; UPDATE bookings SET check_out = '...' WHERE ...; INSERT INTO payments (...) SELECT b.booking_id, '...', nights * b.rate_cents + COALESCE((SELECT SUM ... charges), 0) - COALESCE((SELECT SUM ... payments), 0), 'card' FROM bookings b WHERE ...; COMMIT;` |
| 15 | `CREATE TABLE rate_log (room_id INTEGER, old_cents INTEGER, new_cents INTEGER); CREATE TRIGGER ... AFTER UPDATE OF rack_cents ON rooms WHEN OLD.rack_cents <> NEW.rack_cents BEGIN INSERT INTO rate_log ... VALUES (OLD.room_id, OLD.rack_cents, NEW.rack_cents); END` |

## Things the data does on purpose

- **8 hotels in four towns, with 176 rooms between them.** Abbey Steps closed on
  2026-03-01 and its 12 rooms are still in the table, empty and unbookable,
  which is why question 2 looks at closed_on. Fellfoot Inn, hotel 8, opened on
  2025-09-01 with 14 rooms.
- **List prices tie.** Three rooms at The Old Mill share second place at 9,600
  cents and two at Abbey Steps share first at 6,700: the rows RANK keeps and
  ROW_NUMBER drops in question 1, 18 rooms against 16.
- **Cancelled bookings keep their dates.** 35 rooms are free from 10 to 14 July
  2026; eight of them look taken if a cancelled booking is allowed to count,
  question 2.
- **Four of Fellfoot Inn's 14 rooms had no stay beginning in the first week of
  June 2026**, the zeros question 3 has to keep.
- **Guest 306 has nine bookings: seven stayed and two cancelled**, both in April
  2026, which would put a false stay into the gaps of question 4.
- **1,501 of the 1,600 guests have stayed at least once: 24 once only, 254 more
  than fifteen times**, question 5. 68 stayed in 2025 and have no live booking
  since; 16 more booked for 2026 and cancelled or never came, the ones question
  6's trap calls returned.
- **A rate is not always the list price.** Of 13,625 stays, 9,408 were below it,
  1,575 at it and 2,642 above; question 7 counts the first group, and the
  discount is per night.
- **A stay has several charges and several payments.** 785 stays checked out in
  June 2026, none of them at Abbey Steps; joined to both child tables at once,
  their payments add up to about seven times the truth, question 8.
- **978 of the 25,855 payments are refunds**, negative amounts, so a month's
  takings in question 9 are a net figure. 2025 took 352,148,650 cents.
- **reviews.booking_id is UNIQUE**, one review per booking, which is the
  constraint the upsert of question 10 names. charges has no such constraint,
  and ON CONFLICT cannot be used on it.
- **Room 312 at Spa Gardens has never been booked**, the one room question 11
  must leave at its old price.
- **794 reviews are not their guest's latest for that hotel, and two pairs were
  posted on the same day**, question 12; 2,760 are left when they have gone.
- **446 names belong to more than one guest.** A name is not an identity; guests
  1218 and 1425 are said by the question to be the same Benedict Bianchi,
  question 13.
- **82 bookings are in the house when the data ends**, their bills not yet
  settled. Booking 15170 has run up 40,900 cents in charges and paid 10,050,
  question 14.
- **The data ends at 2026-06-30 23:59**, so a date in July 2026 is always after
  everything already there.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function with
the name the question gives, Run calls it once for each test input and shows
every call and its result in the output pane, and Check compares each result
with the reference function's. Values are compared, not their printed form --
but the type counts: a tuple is not a list, 2.0 is not 2, and 0 is not False. A
function that prints its answer instead of returning it returns None, and None
matches nothing. The inputs are everyday values in the hotel's terms: amounts in
cents and numbers of nights for questions 1 to 5, text as guests and staff type
it for 6 to 10, lists of rooms, names and pairs for 11 to 15. Each prompt shows
one or two example calls with their answers, and Run adds a few more, including
the empty list or the edge the question warns about.

**Nothing needs importing in this set.** In question 7 the name may arrive as
None, and in question 15 each pair arrives as a list of two items.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the database,
the app, or any file. Tab inserts four spaces and Return keeps the indentation
of the line above.

# SQL

## 1 - Rooms and what they cost (3)

RANK started afresh for each hotel and filtered from outside, NOT EXISTS round
the overlap test for a stay nobody has booked yet, and a LEFT JOIN that keeps
its unmatched rooms because the conditions on the booking are in the ON.

1. **The two dearest rooms in each hotel** (Q1357)

   For each hotel, by name, its dearest rooms by list price (rack_cents). A room
   is listed when fewer than two rooms of its own hotel cost more than it does,
   so rooms tied on price share a place and a hotel can show more than two. Give
   each room its place. A ranking window function, started afresh for each
   hotel; what a window produces cannot be tested in the WHERE of the same
   SELECT.

   *Return: hotel, room_no, rack_cents, place*

2. **Rooms free for four nights in July** (Q1358)

   A guest wants four nights, arriving 2026-07-10 and leaving 2026-07-14. For
   each hotel still trading (closed_on is NULL), by name: how many of its rooms
   are free for the whole stay, and the lowest list price among those. A room is
   free when no booking of it that is not cancelled overlaps those nights;
   someone leaving on the 10th or arriving on the 14th is not in the way. NOT
   EXISTS, with the overlap test inside it.

   *Return: hotel, free_rooms, cheapest_cents*

3. **Every room at Fellfoot Inn, busy or not** (Q1359)

   Fellfoot Inn is hotel 8. For every one of its rooms: the room number, the
   kind, and how many stays (status 'stayed') BEGAN in the first week of June
   2026, the 1st to the 7th. A room with none is listed with 0, not left out. An
   outer join -- and think about where the conditions on the booking have to be
   written for a room with no match to survive them.

   *Return: room_no, kind, stays*

## 2 - Guests over time (3)

LAG to read the row before in a guest's history, a CTE so that a count can
itself be counted, and EXISTS beside NOT EXISTS for came and did not come back.

4. **How long between one stay and the next** (Q1360)

   Guest 306 has stayed seven times. For each of those stays (status 'stayed'):
   its check-in, its check-out, and the whole number of days from the PREVIOUS
   stay's check-out to this check-in -- NULL for the first, which has nothing
   before it. LAG reads a column from the row before, in an order you give it.

   *Return: check_in, check_out, days_since_last*

5. **Once, a few times, or a regular** (Q1361)

   Count each guest's stays (status 'stayed'), then count the guests. Put each
   guest in a band by their number of stays -- 'once' for 1, '2 to 5', '6 to
   15', 'over 15' -- and for each band give how many guests are in it and how
   many stays they made between them. A guest with no stay is in no band. Two
   levels of grouping: a CTE for the first, and a query over it for the second.

   *Return: band, guests, stays*

6. **Came in 2025 and have not been back** (Q1362)

   A guest has LAPSED when they stayed in 2025 -- a booking with status 'stayed'
   that began in that year -- and have nothing from 2026 on: no booking
   beginning on or after 2026-01-01 whose status is 'stayed' or 'booked'. A
   cancelled booking or a no-show is not a return. How many lapsed guests are
   there in each loyalty tier, with the guests in no tier (NULL) as a group of
   their own? One EXISTS and one NOT EXISTS.

   *Return: tier, lapsed*

## 3 - Money in and out (3)

A sum over an amount worked out on each row, the two children of a booking added
up separately before they meet, and a window laid over a GROUP BY for a running
total.

7. **What each channel gives away** (Q1363)

   A stay is discounted when the rate agreed for it is below the room's list
   price. For each channel, among stays (status 'stayed'): how many were
   discounted, and the total given away, as a whole number of cents -- for one
   stay, the gap between list price and rate on every night it lasted. The
   amount is worked out for each row, and the sum is taken over that.

   *Return: channel, discounted_stays, discount_cents*

8. **Extras and payments, side by side** (Q1364)

   For each hotel, by name, taking the stays (status 'stayed') that checked out
   in June 2026: how many stays, the total of their extras (charges), and the
   total paid against them (payments, a refund counting as negative). A booking
   has several charges AND several payments; joined to both at once, every
   charge is repeated for every payment. Add each one up on its own before it
   meets the booking, and count a booking with no charges as 0.

   *Return: hotel, stays, extras_cents, paid_cents*

9. **The year's takings as they mounted up** (Q1365)

   Take the payments made in 2025 (paid_at in that year), refunds included as
   the negatives they are. For each month, written 'YYYY-MM': the net amount
   taken in the month, and the running total for the year up to and including
   it. strftime cuts the month out of a timestamp; a window with an ORDER BY
   adds up as it goes, and it can be laid over the result of a GROUP BY.

   *Return: month, taken_cents, running_cents*

## 4 - Changing rows (3)

Writable, one statement each: an INSERT that updates when the row is already
there, an UPDATE whose new value is looked up afresh for each row, and a DELETE
that numbers the rows to find the ones to go.

10. **A review posted, or posted again** (Q1366)

    Two guests post reviews on 2026-07-01. Booking 16876 already has one -- 3,
    'Fine for one night' -- and its guest now gives 5 with the headline 'Better
    on reflection'. Booking 15266 has none; its guest gives 4, 'Lovely view of
    the lake'. reviews allows one review per booking: booking_id is UNIQUE. In
    ONE INSERT of both rows, a review that is new is added and one that exists
    is changed in place -- score, posted_on and headline -- keeping its
    review_id. The upsert clause of INSERT; in it the row that could not go in
    is called excluded.

    *Checked: the two bookings' reviews with their ids, and how many reviews there are*

11. **List prices reset to what guests paid** (Q1367)

    Spa Gardens (hotel 5) resets its list prices. Each of its rooms gets as
    rack_cents the average rate_cents of that room's OWN stays (status 'stayed')
    that began in 2026, rounded to a whole number of cents. A room with no such
    stay keeps the price it has -- there is one. One UPDATE, whose new value is
    a subquery that looks back at the row being updated.

    *Checked: for Spa Gardens and for the other hotels taken together: rooms, the total, lowest and highest list price, and how many different prices*

12. **One review per guest per hotel** (Q1368)

    The site will show only a guest's most recent review of each hotel. Delete
    every review that is not the latest one its guest has posted for that hotel;
    where two were posted on the same day, the one with the higher review_id is
    the later. A review reaches its guest through the booking and its hotel
    through the room. One DELETE; ROW_NUMBER, started afresh for each guest and
    hotel, numbers the reviews so that the ones to go can be picked out.

    *Checked: the reviews left: how many, their scores added up, their ids added up, and the earliest posted*

## 5 - Procedures (3)

Writable questions of several steps. SQLite has no CREATE PROCEDURE: a
transaction makes steps stand or fall together, the order of the steps is the
procedure, and a trigger body is a procedure the database runs for you.

13. **One guest, entered twice** (Q1369)

    Benedict Bianchi is on the books twice. Guest 1425 is the older record, with
    the gold tier and no email; guest 1218 has an email and twelve bookings.
    Make them one, keeping 1425. In ONE transaction: 1425 takes 1218's email --
    read it, do not type it -- every booking of 1218 becomes 1425's, and 1218 is
    deleted. Foreign keys are enforced, so a guest who still has bookings cannot
    be deleted; and a deleted guest has no email left to read. The order of the
    three steps matters. The question then issues a ROLLBACK: committed work
    survives it.

    *Checked: guest 1425's email and tier, how many bookings 1425 and 1218 hold, and how many guests are called Benedict Bianchi*

14. **Leaving early, and settling up** (Q1370)

    Booking 15170 is in the house at Castle View and due to leave on 2026-07-06.
    The guest leaves on 2026-07-01 instead, and pays what is owed by card at
    2026-07-01 10:30. In one transaction: bring check_out forward, and insert
    ONE payment for the balance -- the nights actually stayed at the booking's
    rate, plus its charges, less what has already been paid. Work the balance
    out in the INSERT from the tables; do not type it. One of the two steps
    reads what the other writes, so their order decides the amount.

    *Checked: the booking's check-out, how many payments it has and what they add up to*

15. **Who changed that price?** (Q1371)

    Keep a record of every change to a room's list price. Two statements. Create
    a table rate_log with three integer columns: room_id, old_cents and
    new_cents. Then store a trigger that, AFTER an UPDATE of rack_cents on
    rooms, writes one row to it -- but only when the price really changed: an
    UPDATE that sets a price to the value it already had is not a change. The
    question then runs three updates at Fellfoot Inn: its twins go up by 300
    cents; its three ground-floor singles are all set to 4,550, which two of
    them already are; and one room's sleeps is altered.

    *Checked: the rows of rate_log*

# Python

## 1 - Bills and counting (5)

A total carried through a loop, // and % and divmod for questions about whole
numbers, adding before dividing to round up, and break for a rule that stops.

1. **The bill as it mounts up** (P626)

   A list holds the charges put on a room, in order, in cents. Write a function
   `running_bill(charges)` that returns a list of the same length: what the bill
   stood at after each charge. Keep one total going and add to it.

   ```
   running_bill([1200, 450, 800]) -> [1200, 1650, 2450]
   ```

   *Return: a list of ints.*

2. **Weeks and odd nights** (P627)

   The weekly rate applies to each full week of a stay. Write a function
   `weeks_and_nights(nights)` that returns a tuple: the number of full weeks,
   and the nights left over. Both are whole numbers. // divides and drops the
   remainder, % gives the remainder, and divmod does both at once.

   ```
   weeks_and_nights(10) -> (1, 3)
   weeks_and_nights(14) -> (2, 0)
   ```

   *Return: a tuple of two ints.*

3. **How many rooms does the party need?** (P628)

   A party of `guests` people is put in rooms that each sleep `sleeps`. Write a
   function `rooms_needed(guests, sleeps)` that returns the smallest number of
   rooms that holds everyone. A room that is only part full is still a room;
   nobody needs no rooms. Use whole-number arithmetic only.

   ```
   rooms_needed(7, 2) -> 4
   rooms_needed(8, 2) -> 4
   ```

   *Return: an int.*

4. **Every seventh night is free** (P629)

   The group's offer: every seventh night of a stay is free. Write a function
   `nights_charged(nights)` that returns how many nights the guest pays for. A
   fortnight has two free nights in it, not one.

   ```
   nights_charged(7) -> 6
   nights_charged(14) -> 12
   nights_charged(6) -> 6
   ```

   *Return: an int.*

5. **How many nights can they afford?** (P630)

   `prices` holds the price of each night of a stay, in order; they differ,
   weekends cost more. Write a function `nights_afforded(prices, budget)` that
   returns how many nights, starting from the first, can be paid for without
   going over budget. The stay has to be unbroken: the first night that does not
   fit ends it, however cheap the nights after it are. Spending the budget
   exactly is allowed.

   ```
   nights_afforded([100, 300, 50], 200) -> 1
   nights_afforded([80, 80, 80], 240) -> 3
   ```

   *Return: an int.*

## 2 - Names and notes (5)

partition for a single cut, or for a value that may be missing, split and join
round capitalize, int on each side of the point to stay out of floats, and str
on the way into join.

6. **A request and its detail** (P631)

   Requests on a booking are typed as 'kind: detail'. Write a function
   `split_request(text)` that returns a tuple of the two parts, each with the
   spaces round it removed. Only the FIRST colon divides them -- the detail may
   hold a time. With no colon at all the whole text is the kind and the detail
   is the empty string. A string has a method that cuts at the first occurrence
   of a separator and always gives three pieces.

   ```
   split_request("late checkout: after 2pm") -> ("late checkout", "after 2pm")
   split_request("cot") -> ("cot", "")
   ```

   *Return: a tuple of two strs.*

7. **Dear whoever you are** (P632)

   A letter opens 'Dear NAME,'. Write a function `greeting(name)` that returns
   that line with the name's surrounding spaces removed. The name may be missing
   in three ways -- None, an empty string, or nothing but spaces -- and then the
   letter opens 'Dear Guest,'. `a or b` gives b whenever a is empty or None.

   ```
   greeting("Ada") -> "Dear Ada,"
   greeting("") -> "Dear Guest,"
   ```

   *Return: a str.*

8. **A name typed in a hurry** (P633)

   Names arrive from the web form in any state. Write a function
   `tidy_name(name)` that returns the name with each word starting with a
   capital and the rest of it in small letters, exactly one space between words,
   and none at the ends. split with no argument, a method that capitalises one
   word, and join.

   ```
   tidy_name("  aDA   loveLACE ") -> "Ada Lovelace"
   ```

   *Return: a str.*

9. **Money as text, cents as a number** (P634)

   Amounts are typed as text such as '$1,250.50': a dollar sign, perhaps commas,
   and either no decimal point or a point followed by exactly two digits. Write
   a function `to_cents(text)` that returns the amount as a whole number of
   cents. Keep it in whole numbers all the way: take the two sides of the point
   apart as text and convert each with int.

   ```
   to_cents("$12.05") -> 1205
   to_cents("$1,250.50") -> 125050
   to_cents("$45") -> 4500
   ```

   *Return: an int.*

10. **The rooms on one line** (P635)

    A confirmation lists the rooms booked. Write a function `room_list(rooms)`
    that takes a list of room numbers, which are ints, and returns them as one
    string with a comma and a space BETWEEN them: nothing at the start, nothing
    at the end. An empty list gives the empty string. join does the between
    part, but it will only join strings.

    ```
    room_list([101, 102, 205]) -> "101, 102, 205"
    ```

    *Return: a str.*

## 3 - Rooms and rotas (5)

enumerate for positions, two slices and a remainder to rotate, a loop inside a
loop, a slice that steps backwards, and a for that unpacks pairs.

11. **Which rooms are free?** (P636)

    A list holds the state of each room along a corridor, 'free' or 'taken'.
    Write a function `free_rooms(states)` that returns the positions of ALL the
    free ones, counting from 0. enumerate hands you each item together with its
    position.

    ```
    free_rooms(["free", "taken", "free", "free"]) -> [0, 2, 3]
    ```

    *Return: a list of ints.*

12. **The rota moves on** (P637)

    The early-shift rota is a list of names; each day the person at the front
    goes to the back. Write a function `rota(staff, days)` that returns a NEW
    list showing the rota after that many days. days can be more than the number
    of staff -- the rota simply goes round again -- and an empty rota stays
    empty. Two slices joined, and a remainder.

    ```
    rota(["Ana", "Bo", "Cy"], 1) -> ["Bo", "Cy", "Ana"]
    rota(["Ana", "Bo", "Cy"], 5) -> ["Cy", "Ana", "Bo"]
    ```

    *Return: a list.*

13. **Every door in the building** (P638)

    A new hotel has `floors` floors, numbered from 1, and `per_floor` rooms on
    each, numbered from 1. A door number is the floor followed by the room as
    two digits: floor 2, room 4 is '204'. Write a function `room_numbers(floors,
    per_floor)` that returns every door number as text, floor by floor. A loop
    inside a loop; an f-string can pad a number to two digits.

    ```
    room_numbers(2, 3) -> ["101", "102", "103", "201", "202", "203"]
    ```

    *Return: a list of strs.*

14. **Starting from the far end** (P639)

    Housekeeping is given the rooms to clean in the order they lie along the
    corridor, and today starts from the far end. Write a function
    `cleaning_order(rooms)` that returns a NEW list with the same rooms in the
    opposite order -- the order they were given in, backwards, not sorted. A
    slice can step backwards.

    ```
    cleaning_order(["101", "102", "103"]) -> ["103", "102", "101"]
    ```

    *Return: a list.*

15. **One guest's nights, added up** (P640)

    `stays` is a list of pairs, each a guest's name and a number of nights:
    [["Ada", 3], ["Hugo", 2]]. A guest can appear more than once. Write a
    function `nights_for(stays, guest)` that returns the total nights of all the
    stays under that name, and 0 when there are none. A for loop can unpack each
    pair into two names as it goes.

    ```
    nights_for([["Ada", 3], ["Hugo", 2], ["Ada", 4]], "Ada") -> 7
    ```

    *Return: an int.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,981 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
