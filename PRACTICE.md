# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the parcel-courier scheme,
the fourth set on it, at two tools per question with the tiers named by
task, on tools the first three courier sets left out, and three writable
questions; the prompts name the tool but do not write the statement.
**Fifteen Python** at the easy level of the last six sets: everyday tasks
over plain lists and strings in the courier's terms, with no maths and no
dicts.

| Stage | SQL questions |
|---|---|
| 1 - Trails and runs | 1-3 |
| 2 - Depots and regions | 4-6 |
| 3 - Customers and money | 7-9 |
| 4 - Weights and days | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Counting and finding | 1-5 |
| 2 - Labels | 6-10 |
| 3 - Checks and filters | 11-15 |

## The schema

Six tables. `depots` are the buildings, each in a `region` with so many
loading bays, opened on a date and perhaps closed. `couriers` work from a
depot with a `vehicle` -- bike, van or lorry -- hired on a date, perhaps
left. `customers` are businesses or people with a home depot; a
`postcode_area` that may be NULL. `parcels` is the centre: a customer OR
NULL for a walk-in at the counter, an origin depot and a destination depot,
a `service` (economy, standard or express), a weight in grams,
`collected_at`, a `delivered_at` and `courier_id` that are NULL while the
parcel is still moving, and the `postage_cents` decided when it was
collected. `scans` is the trail: one row per event in time order --
collected, departed, arrived, out_for_delivery, failed, delivered -- at a
depot, with the courier for the last three. `invoices` bill a business
customer's month of postage, issued on the first of the next month and
paid on a date or not yet. Double-click a table in the left pane to see
its columns.

**Dates and times are text**: 'YYYY-MM-DD' for dates, 'YYYY-MM-DD HH:MM'
for timestamps. They compare correctly as text; `julianday()` turns either
into a number of days you can subtract -- multiply by 24 for hours -- and
`date()` cuts a timestamp to its day.

**The data ends at 2026-06-30 23:59.** Anything that would have happened
after that has not happened -- 271 parcels have no delivery,
113 of them after a failed attempt and nothing since; June's invoices
are not out -- and every question that measures an open interval says
which end to supply.

## The writable stage

SQLite has no stored procedures, variables, loops or TRY/CATCH. What it has
instead is triggers and plain DML -- and each of questions 13 to 15 is one
of those.

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

**Driver statements.** Question 14 runs two UPDATEs *after* your script:
parcel 40 is marked delivered, which the trigger must turn into a scan,
and parcel 41's postage changes, which it must ignore. Questions 13 and
15 are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `UPDATE customers SET depot_id = 1 FROM depots d WHERE customers.depot_id = d.depot_id AND d.closed_on IS NOT NULL` |
| 14 | `CREATE TRIGGER scan_on_delivery AFTER UPDATE OF delivered_at ON parcels WHEN NEW.delivered_at IS NOT NULL AND OLD.delivered_at IS NULL BEGIN INSERT INTO scans (...) VALUES (NEW.parcel_id, ...); END` |
| 15 | `INSERT INTO invoices (customer_id, period, amount_cents, issued_on) SELECT c.customer_id, '2026-06', SUM(p.postage_cents), '2026-07-01' FROM parcels p JOIN customers c ... WHERE c.kind = 'business' AND ... GROUP BY c.customer_id` |

## Things the data does on purpose

- **The best bike courier delivered on 20 consecutive days**, question 1's
  longest island, found only once each day is counted once.
- **Every one of the 546 days has a collection**, so question 2's seven-row
  frame is seven days; 1 June's week reaches back into May.
- **509 of the 620 senders have sent to all five regions and only 9 have stuck
  to three**, question 4's division; the busiest same-region pair, Southfield
  and Millbank, exchange 547 parcels, question 5's largest.
- **Old Foundry collected nothing after January 2026**, the five zero months
  question 6's recursive spine supplies and a GROUP BY cannot.
- **24 businesses have never been invoiced, 2 of whom have sent parcels** --
  they joined in June, whose bill is not out -- question 7's anti-join.
- **A business needs 187,570 cents of postage to be in its top tenth**,
  question 8's threshold; Central Hub's customers have been invoiced
  $8,574.70, question 9's text.
- **Economy's median weight is 1,532 grams against a mean of 2,243**, question
  10's gap; 28.7 per cent of deliveries fall at the weekend, question 11's
  share, within a point of two sevenths.
- **The best courier fails only 8.7 per cent of attempts**, question 12's top
  of the list.
- **Old Foundry had 53 customers**, whom question 13 moves to the hub; 163
  businesses sent in June out of 424 senders, the invoices question 15 issues.
- **The data ends at 2026-06-30 23:59**, with 271 parcels still moving and 332
  invoices unpaid.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form -- but the type counts: a tuple is not a list, and 0 is not False. A
function that prints its answer instead of returning it returns None, and
None matches nothing. The inputs are everyday values in the courier's terms:
weights, code lists and trails for questions 1 to 5, hours, stamps and
counts for 6 to 10, trails and codes for 11 to 15. Each prompt shows one
example call with its answer, and Run adds a few more, including the empty
list or the edge the question warns about. Where a tool needs an import,
the question says the line to write.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Trails and runs (3)

A row number subtracted from a date as the island key, which needs DISTINCT days
first; a ROWS frame of seven that must see May before June is filtered; and
GROUP_CONCAT with its own ORDER BY and separator, no DISTINCT.

1. **Each bike courier's longest unbroken run of days** (Q1267)

   For each courier on a bike: the most CONSECUTIVE days on which they
   delivered at least one parcel. The gaps-and-islands trick: a CTE of
   DISTINCT courier-and-day pairs, a group key made by subtracting each day's
   row number (within the courier) from the day, so a run of consecutive days
   shares one key; count per key, MAX per courier.

   *Return: name, longest_run*

2. **A week's collections, rolling** (Q1268)

   For each day of June 2026: the parcels collected that day, and the average
   over that day and the six before it, to one decimal. Count per day in a
   CTE, a window AVG with a ROWS frame reaching six rows back, and the June
   filter applied AFTER the window -- 1 June's week reaches into May.

   *Return: day, parcels, rolling_avg*

3. **A troubled trail in one line** (Q1269)

   For parcels 40, 44, 67, 71 and 72 -- the first five that failed an attempt:
   the whole trail as ONE text cell, the statuses in time order joined by ' >
   '. GROUP_CONCAT with its own separator and its own ORDER BY; a status that
   appears twice must appear twice.

   *Return: parcel_id, trail*

## 2 - Depots and regions (3)

A count of distinct regions compared with the count of regions, < rather than <>
in a self-join, and a recursive CTE that manufactures the months a GROUP BY
cannot.

4. **Customers who have sent to every region** (Q1270)

   For each kind of customer: how many have sent parcels to EVERY one of the
   five regions. Relational division: per customer, the number of DIFFERENT
   destination regions, compared with the number of regions there are; then a
   count per kind.

   *Return: kind, everywhere*

5. **Neighbours in the same region** (Q1271)

   Every pair of depots that share a region, each pair once with the lower
   depot_id first, and the parcels that travelled between them in EITHER
   direction. A self-join of depots on region with a strict inequality on the
   ids, and a count of the parcels whose two depots are the pair, either way
   round.

   *Return: depot_a, depot_b, between*

6. **Old Foundry, month by month, to the end** (Q1272)

   Old Foundry's collections for every month from January 2025 to June 2026 --
   eighteen rows, with 0 for the months after it closed. Generate the months
   with a recursive CTE that adds a month each step, then LEFT JOIN the
   depot's parcels onto them.

   *Return: month, parcels*

## 3 - Customers and money (3)

IS NULL in WHERE after a LEFT JOIN rather than in ON, CUME_DIST ascending so 0.9
names the big spenders, and printf's comma flag over a real division.

7. **Businesses that have never been billed** (Q1273)

   Every business customer with no invoice at all: name, date joined, and how
   many parcels they have sent. An anti-join with LEFT JOIN: join invoices and
   keep the customers whose side of the join came back empty. The parcel count
   is a separate scalar subquery.

   *Return: name, joined_on, parcels*

8. **What it takes to be a top-ten-per-cent sender** (Q1274)

   For each kind of customer: the senders, the postage total that puts a
   customer in the top ten per cent of that kind's senders, and the kind's
   maximum. A CTE of postage per customer, CUME_DIST over it partitioned by
   kind in ascending order, then the smallest total whose CUME_DIST is at
   least 0.9 -- MIN with a FILTER -- and MAX.

   *Return: kind, senders, top_decile_cents, max_cents*

9. **Invoiced money, printed as money** (Q1275)

   For every depot, of the customer's home: the invoice money issued, as TEXT
   the way an accountant writes it -- a dollar sign, thousands separated by
   commas, two decimals: '$8,574.70'. printf has a flag for the separator.

   *Return: name, invoiced*

## 4 - Weights and days (3)

(n + 1) / 2 and (n + 2) / 2 landing on the middle rows, %w on the DELIVERY
timestamp with quoted digits, and failures over attempts rather than over
deliveries.

10. **The middle parcel of each service** (Q1276)

    For each service: the MEDIAN weight in grams. No MEDIAN function: number
    each service's parcels by weight with ROW_NUMBER and count them with
    COUNT(*) OVER, both partitioned by service, in a CTE; keep the rows
    numbered (n + 1) / 2 and (n + 2) / 2 -- one row when n is odd, the two
    middle rows when it is even -- and AVG them.

    *Return: service, median_g*

11. **Weekend deliveries, by vehicle** (Q1277)

    For each vehicle type: its deliveries, how many were made on a Saturday or
    Sunday, and that as a percentage to one decimal. The day of the week comes
    from strftime on the DELIVERY timestamp, '0' for Sunday to '6' for
    Saturday; the average of a true-or-false test is a share.

    *Return: vehicle, deliveries, weekend, weekend_pct*

12. **The couriers whose attempts most often succeed** (Q1278)

    The five couriers with the LOWEST failure rate: name, vehicle, attempts
    ('out_for_delivery' scans), failures ('failed' scans), and the failures as
    a percentage of the attempts to one decimal. Two conditional sums per
    courier, a ratio of them, ORDER BY the rate then courier_id, LIMIT 5.

    *Return: name, vehicle, attempts, failures, fail_pct*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. UPDATE ... FROM with the closed test on
the depot row, AFTER UPDATE OF with OLD and NEW in the WHEN, and a GROUP BY
feeding an INSERT.

13. **A closed depot's customers move to the hub** (Q1279)

    Every customer whose home depot has closed should now belong to Central
    Hub, depot 1. ONE UPDATE of customers that joins depots into it -- UPDATE
    ... FROM -- so that the test on closed_on can be written against the depot
    row rather than a subquery.

    *Checked: how many customers belong to depot 1, how many to depot 2, and how many there are*

14. **Marking a parcel delivered writes its last scan** (Q1280)

    When a parcel's delivered_at is set -- changed from NULL to a time -- a
    'delivered' scan should appear in its trail: at the destination depot, by
    the parcel's courier, at that time. Write an AFTER UPDATE trigger on
    parcels that fires only for that column and only for that change (a WHEN
    clause with OLD and NEW). The question then marks parcel 40 delivered and
    changes parcel 41's postage.

    *Checked: parcel 40's delivered scans, any scan for parcel 41 dated July, and the total number of scans*

15. **Billing June** (Q1281)

    Issue June 2026's invoices: one per BUSINESS customer who sent a parcel in
    June, for the period '2026-06', issued on 2026-07-01, for the sum of their
    June postage. ONE INSERT whose rows come from a SELECT with a GROUP BY.

    *Checked: how many June invoices there are, their amounts added up, and the earliest issue date*

# Python

## 1 - Counting and finding (5)

A sum of comparisons plus one, zip so neither list is indexed past its end, a
difference left negative on purpose, `in` rather than count() over nested lists,
and split('-') before the set.

1. **Where a parcel ranks by weight** (P536)

   Write a function `weight_rank(weights, w)` that returns the rank of weight
   w among the weights, 1 for the heaviest: one more than the number of
   weights strictly heavier than w. A sum of comparisons, plus one.

   ```
   weight_rank([2500, 7500, 1200, 3000], 3000) -> 2
   ```

   *Return: an int.*

2. **Where the manifest and the scans first disagree** (P537)

   The manifest lists the codes a van should carry; the scans list what was
   actually loaded, in order. Write a function `first_mismatch(expected,
   actual)` that returns the position of the first place the two lists differ,
   or -1 when they agree as far as the shorter one goes. enumerate over zip;
   return inside the loop, -1 after it.

   ```
   first_mismatch(["MB-1", "MB-2", "MB-3"], ["MB-1", "MB-9", "MB-3"]) -> 1
   ```

   *Return: an int.*

3. **Room left in the van** (P538)

   A van takes a fixed weight. Write a function `room_left(capacity, weights)`
   that returns how much weight can still be loaded after the listed parcels
   -- which may be negative if the van is already over. The capacity minus the
   sum.

   ```
   room_left(50000, [12000, 7500, 3000]) -> 27500
   ```

   *Return: an int.*

4. **How many trails had a failure anywhere** (P539)

   Write a function `trails_with(trails, status)` that returns how many of the
   trails contain the status at least once, wherever it appears. A sum over
   the trails of `status in trail`.

   ```
   trails_with([["collected", "failed", "delivered"], ["collected", "delivered"], ["failed"]], "failed") -> 2
   ```

   *Return: an int.*

5. **Is the whole batch from one depot?** (P540)

   A parcel code starts with its depot code and a hyphen. Write a function
   `one_depot(codes)` that returns True when every code in the batch has the
   same depot code, and True for an empty batch. Pull the depot codes out,
   then test how many DIFFERENT ones there are.

   ```
   one_depot(["MB-0012", "MB-0031", "MB-0007"]) -> True
   ```

   *Return: True or False.*

## 2 - Labels (5)

// 4 * 4 then :02d, a slice from 11 not 10, math.gcd before //, newlines between
the lines and none after, and abs() once the sign has picked the word.

6. **The delivery slot for an hour** (P541)

   Deliveries are promised in four-hour slots: 08:00-12:00, 12:00-16:00,
   16:00-20:00 and so on, round the clock. Write a function `slot(hour)` that
   returns the slot label for an hour from 0 to 23, both ends zero-padded.
   Integer division by 4 and back finds the slot's start; a format spec pads.

   ```
   slot(9) -> "08:00-12:00"
   ```

   *Return: a str.*

7. **Just the time of a scan** (P542)

   Scans are stamped 'YYYY-MM-DD HH:MM'. Write a function `time_of(stamp)`
   that returns just the 'HH:MM' part. The format is fixed, so a slice does
   it.

   ```
   time_of("2026-03-04 08:05") -> "08:05"
   ```

   *Return: a str.*

8. **Parcels per courier, as a ratio** (P543)

   Write a function `ratio(a, b)` that returns 'a:b' with both numbers divided
   by their greatest common divisor, so ratio(24000, 60) is '400:1'.
   math.gcd() finds the divisor; write `import math` at the top.

   ```
   ratio(24000, 60) -> "400:1"
   ```

   *Return: a str.*

9. **A three-line address label** (P544)

   Write a function `label(code, name, town)` that returns a three-line label:
   the code on the first line, the name on the second, the town in capitals on
   the third, the lines separated by newline characters and nothing after the
   last.

   ```
   label("MB-0012", "Hamid Uddin", "Millbank") -> "MB-0012\nHamid Uddin\nMILLBANK"
   ```

   *Return: a str.*

10. **Early, late, or on time** (P545)

    A parcel was promised in one number of days and arrived in another. Write
    a function `timing(promised, actual)` that returns 'on time' when they
    match, '2 days late' when it took longer, and '2 days early' when it took
    less -- with 'day' for exactly one. Compute the difference, then an
    if/elif/else.

    ```
    timing(3, 5) -> "2 days late"
    ```

    *Return: a str.*

## 3 - Checks and filters (5)

The last entry rather than anywhere in the trail, a tuple key with int() in its
second part, lower() before the set, a tuple built from the two parts, and ints
compared with their sorted selves.

11. **The trails that were not lost** (P546)

    A trail is lost when it ENDS on 'failed'. Write a function
    `not_lost(trails)` that returns the trails that are not lost, in order,
    keeping empty trails. A comprehension whose test is 'empty, or last entry
    not failed'.

    ```
    not_lost([["collected", "delivered"], ["collected", "failed"], ["collected"]]) -> [["collected", "delivered"], ["collected"]]
    ```

    *Return: a list of lists.*

12. **Codes in depot order, then by number** (P547)

    Write a function `by_depot_then_number(codes)` that returns the codes
    sorted by depot code alphabetically and, within a depot, by the NUMBER
    after the hyphen. sorted() with a key that returns a tuple of the two
    parts, the number converted to int.

    ```
    by_depot_then_number(["MB-100", "CH-7", "MB-23", "CH-100"]) -> ["CH-7", "CH-100", "MB-23", "MB-100"]
    ```

    *Return: a list of str.*

13. **The same code typed two ways** (P548)

    Scanners sometimes read a code in lower case. Write a function
    `case_clash(codes)` that returns True when two codes in the list are the
    same apart from case, and False otherwise. Compare how many codes there
    are with how many DIFFERENT codes there are once every one is lower-cased.

    ```
    case_clash(["MB-0012", "mb-0012"]) -> True
    ```

    *Return: True or False.*

14. **Codes taken apart** (P549)

    Write a function `split_codes(codes)` that turns each code into a pair:
    the depot code and the number as an int -- ('MB', 12). A comprehension
    that splits at the hyphen and builds a tuple; the result is a list of
    tuples.

    ```
    split_codes(["MB-0012", "CH-7"]) -> [("MB", 12), ("CH", 7)]
    ```

    *Return: a list of (str, int) tuples.*

15. **Are the codes in numeric order?** (P550)

    Write a function `in_number_order(codes)` that returns True when the
    numbers after the hyphens never decrease along the list, and False
    otherwise; a list of one or none is in order. Pull the numbers out as
    ints, then compare the list with its sorted self.

    ```
    in_number_order(["MB-7", "MB-23", "MB-100"]) -> True
    ```

    *Return: True or False.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,801 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
