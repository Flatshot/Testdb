# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the parcel-courier scheme,
the second set on it, at two tools per question with the tiers named by
task, on tools the first courier set left out, and three writable
questions; the prompts name the tool but do not write the statement.
**Fifteen Python** at the easy level of the last four sets: everyday
tasks over plain lists and strings in the courier's terms, with no maths
and no dicts.

| Stage | SQL questions |
|---|---|
| 1 - Trails and gaps | 1-3 |
| 2 - Depots and regions | 4-6 |
| 3 - Customers and money | 7-9 |
| 4 - People and vehicles | 10-12 |
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
instead is views, conflict clauses and DDL -- and each of questions 13 to
15 is one of those.

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

**No driver statements this time.** All three are graded on what your
script leaves behind: question 13 on the view it creates, 14 on the
invoices table, and 15 on the new column.

| # | Construct |
|---|---|
| 13 | `CREATE VIEW lost_parcels AS SELECT p.* FROM parcels p WHERE p.delivered_at IS NULL AND (SELECT status FROM scans ... ORDER BY scanned_at DESC LIMIT 1) = 'failed'` |
| 14 | `INSERT INTO invoices (...) VALUES (...), (...) ON CONFLICT (customer_id, period) DO UPDATE SET amount_cents = excluded.amount_cents` |
| 15 | `ALTER TABLE parcels ADD COLUMN is_local INTEGER NOT NULL DEFAULT 0; UPDATE parcels SET is_local = 1 WHERE origin_depot_id = dest_depot_id` |

## Things the data does on purpose

- **113 parcels end their trail on a failed attempt**, out of the 3,345 that
  failed at least once: question 1's correlated MAX tells the two apart, and
  question 13's view holds the same 113.
- **15,592 parcels have exactly five scans**, the plain journey; three is a
  local parcel, seven is one failed attempt, nine is two, and the trails of
  one or two are parcels the data's end cut short -- question 2's histogram.
- **No depot goes quiet for more than 67 hours between collections**, question
  3's longest gap, once LAG looks back within the depot rather than across the
  network.
- **Old Foundry collected nothing after January 2026**, the five zero cells
  question 4's grid has and a plain GROUP BY lacks; Central Hub takes 69.3 per
  cent of the centre's collections, question 5's share.
- **Millbank's counter peaks at five in the afternoon with 364 parcels**, the
  biggest of question 6's ten busiest hours; no depot peaks at noon.
- **25 customers have sent more than 60 parcels AND average over 700 cents**,
  question 7's list; with OR instead of AND it would be 435.
- **1,966 invoices are paid and 652 of them took more than thirty days**,
  question 8's figures, which the 332 unpaid ones would turn into a third,
  NULL row.
- **No June 2026 invoice exists yet**, so every business that sent in June is
  outstanding in question 9; 6,900 parcels never left their depot, the flag
  question 15 sets.
- **9 couriers were hired since the data began**, question 11's rows; bike
  couriers average 5.4 years of service, question 10's longest; the busiest
  courier of all has 1,584 deliveries, question 12's largest bare-column row.
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
trails of status words, lists of trails, parcel codes and weights for
questions 1 to 5, a period, a number or a status for 6 to 10, codes,
weights and trails for 11 to 15. Each prompt shows one example call with
its answer, and Run adds a few more, including the empty list or the edge
the question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Trails and gaps (3)

A correlated MAX for the latest scan where EXISTS would find any failure, a
COUNT of COUNTs in two layers, and LAG with PARTITION BY so the previous row is
the previous row HERE.

1. **The parcels that were never heard of again** (Q1237)

   For each service: how many parcels have a FAILED attempt as the latest scan
   in their trail -- lost, as far as the data knows. The latest scan is the
   one whose time equals the parcel's maximum, found by a correlated subquery;
   a parcel that failed once and was delivered later does not count.

   *Return: service, lost*

2. **How long a trail is** (Q1238)

   How many parcels have a trail of 1 scan, of 2, of 3, and so on: one row per
   trail length. Count the scans per parcel first, then count the parcels per
   count -- an aggregate of an aggregate, in two layers.

   *Return: scans, parcels*

3. **The longest quiet spell at each depot** (Q1239)

   For every depot: the longest gap in hours between two consecutive
   collections there, to one decimal, and the average gap. The previous
   collection at the SAME depot comes from a window function that looks one
   row back, partitioned by depot and ordered by time, in a CTE.

   *Return: name, longest_gap_h, avg_gap_h*

## 2 - Depots and regions (3)

CROSS JOIN to build the cells before LEFT JOIN fills them, a window SUM
partitioned by region as the denominator, and ROW_NUMBER partitioned with a
tiebreak to keep number 1.

4. **Every depot, every month of 2026, zeros included** (Q1240)

   For every depot and every month of 2026 in the data: how many parcels were
   collected there, with 0 where there were none. A CROSS JOIN of the depots
   and the distinct months builds the full grid of sixty; a LEFT JOIN of
   parcels fills it, and a count of a parcels column gives the zeros.

   *Return: name, month, parcels*

5. **Each depot's share of its region** (Q1241)

   For every depot: its region, its collections, and its share of its REGION's
   collections as a percentage to one decimal. Count per depot in a CTE, then
   a window SUM partitioned by region for the denominator.

   *Return: region, name, parcels, region_pct*

6. **The busiest hour at each depot's counter** (Q1242)

   For every depot: the hour of the day ('08' to '17') in which the most
   parcels were handed in, and how many. A CTE of parcels per depot and hour,
   then ROW_NUMBER partitioned by depot, ordered by the count descending with
   the hour as a tiebreak, keeping number 1.

   *Return: name, hour, parcels*

## 3 - Customers and money (3)

Two aggregate tests joined by AND in one HAVING, a WHERE that keeps the unpaid
out of every aggregate, and NOT EXISTS correlated on the customer and the month.

7. **Big senders who pay well** (Q1243)

   The customers who have sent more than 60 parcels AND whose average postage
   is above 700 cents: name, parcels, average postage in whole cents. Both
   conditions are on aggregates, so both belong in one HAVING, joined by AND.

   *Return: name, parcels, avg_postage*

8. **How quickly invoices get paid, by method** (Q1244)

   For each payment method: the invoices paid that way, the average days from
   issue to payment to one decimal, and how many took more than 30 days. Paid
   invoices only -- the unpaid ones have NULL in both the method and the date,
   and would make a group of their own.

   *Return: method, paid, avg_days, over_30*

9. **June's postage, not yet on a bill** (Q1245)

   June 2026's invoices are not out yet. For the ten business customers with
   the most June postage outstanding: name, June parcels, and the postage in
   cents -- counting only customers who do NOT already have an invoice for the
   period '2026-06'. A NOT EXISTS on two columns, customer and period; order
   by the postage, then by customer_id.

   *Return: name, june_parcels, postage_cents*

## 4 - People and vehicles (3)

COALESCE for the couriers still here, a date modifier rather than + 30 with the
condition in ON, and the bare column SQLite takes from the row that held the
MAX.

10. **How long couriers stay** (Q1246)

    For each vehicle type: its couriers, how many have left, and the average
    days of service to the nearest whole day -- to the day they left, or to
    2026-06-30 for those still here. A fallback for the NULL leaving date,
    inside julianday.

    *Return: vehicle, couriers, left, avg_days*

11. **A new courier's first month** (Q1247)

    For each courier hired since the data began (2025 on): their name, hire
    date, and how many parcels they delivered in their first 30 days. The
    30-day test uses a date modifier on the hire date, and it belongs in the
    LEFT JOIN's ON clause so that a courier with no such delivery still
    appears with 0.

    *Return: name, hired_on, first_month_deliveries*

12. **The top courier at each depot** (Q1248)

    For every depot: the courier based there with the most deliveries, and the
    count. SQLite has a shortcut here: in a query that groups by depot and
    takes MAX of the count, a bare column such as the courier's name is taken
    from the row that held the maximum. Count per courier in a CTE first.

    *Return: depot, courier, deliveries*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A view, an ON CONFLICT DO UPDATE
against INSERT OR REPLACE, and ADD COLUMN with a DEFAULT before an UPDATE.

13. **A view of the lost parcels** (Q1249)

    Create a view named lost_parcels holding every column of parcels for the
    parcels that are not delivered AND whose latest scan is a failed attempt
    -- the same 'latest scan' test as question 1, inside the view's
    definition.

    *Checked: how many rows the view has, and how many of them are economy*

14. **One invoice corrected, one created, in one statement** (Q1250)

    Two invoices for the period '2026-05', both issued on 2026-06-01: customer
    4's, which exists and must be corrected to 2500 cents, and customer 8's,
    which does not exist and must be created at 1200 cents. ONE INSERT with
    two rows and an ON CONFLICT clause on the (customer_id, period) key that
    updates the amount instead of failing -- an upsert.

    *Checked: the two amounts, how many invoices there are, and the highest invoice_id*

15. **A flag column, added and filled** (Q1251)

    Add an integer column is_local to parcels, NOT NULL with a default of 0,
    then set it to 1 for every parcel whose origin and destination depots are
    the same. Two statements: an ALTER TABLE and an UPDATE.

    *Checked: how many parcels are flagged, and how many there are*

# Python

## 1 - Counting and finding (5)

zip with the list shifted for neighbours, the weight first in the pair so max()
picks by it, split('-') rather than a fixed slice, `t and t[-1]` before
indexing, and max(default=0).

1. **Did a failure come straight after an attempt?** (P506)

   Write a function `has_pair(trail, first, second)` that returns True when
   the second status comes IMMEDIATELY after the first somewhere in the trail,
   and False otherwise. zip the trail with itself shifted by one to walk the
   consecutive pairs; any() over them.

   ```
   has_pair(["collected", "out_for_delivery", "failed", "delivered"], "out_for_delivery", "failed") -> True
   ```

   *Return: True or False.*

2. **The code of the heaviest parcel** (P507)

   Two lists line up: parcel codes and their weights. Write a function
   `heaviest(codes, weights)` that returns the code of the heaviest parcel --
   on a tie, the one whose code sorts last -- or None when the lists are
   empty. max() over the zipped pairs with the weight first, then the code out
   of the winning pair.

   ```
   heaviest(["MB-0012", "CH-0007", "WW-0002"], [2500, 7500, 1200]) -> "CH-0007"
   ```

   *Return: a str, or None.*

3. **The number inside a parcel code** (P508)

   A parcel code is a depot code, a hyphen and a number with leading zeros:
   'MB-0012', 'CHB-0007'. Write a function `code_number(code)` that returns
   the number as an int. Split at the hyphen and convert the part after it;
   the depot code can be any length.

   ```
   code_number("MB-0012") -> 12
   ```

   *Return: an int.*

4. **How many trails end in a delivery** (P509)

   Write a function `completed(trails)` that takes a list of trails -- each a
   list of status words -- and returns how many end with 'delivered'. An empty
   trail has no last entry and does not count; test the trail is non-empty
   before looking at its last item.

   ```
   completed([["collected", "delivered"], ["collected", "failed"], []]) -> 1
   ```

   *Return: an int.*

5. **The longest trail in the batch** (P510)

   Write a function `longest_trail(trails)` that returns the number of scans
   in the longest trail, or 0 when there are no trails at all. max() over the
   lengths, with a default for the empty case.

   ```
   longest_trail([["collected", "delivered"], ["collected", "departed", "arrived"], ["collected"]]) -> 3
   ```

   *Return: an int.*

## 2 - Labels (5)

An index that is one less than the month, % 10 to keep one digit, the spaces and
unit as part of the string, replace() before upper(), and a method call inside
the braces.

6. **A billing period as words** (P511)

   Invoices carry a period like '2026-05'. Write a function
   `period_words(period)` that returns it as 'May 2026'. A list of the twelve
   month names, indexed by the month number -- mind that lists start at 0 --
   after split('-') and int().

   ```
   period_words("2026-05") -> "May 2026"
   ```

   *Return: a str.*

7. **A check digit on the end** (P512)

   To catch typing mistakes, a parcel number gets a check digit: the sum of
   its digits, modulo 10, written on the end. Write a function
   `with_check_digit(number)` that returns the number with that digit
   appended: '0012' becomes '00123'. sum() over the digits as ints, then % 10,
   then str().

   ```
   with_check_digit("0012") -> "00123"
   ```

   *Return: a str.*

8. **A box's size on the label** (P513)

   Write a function `box_label(length, width, height)` that returns the
   dimensions as '30 x 20 x 10 cm' -- the three numbers joined by ' x ', then
   a space and 'cm'. One f-string.

   ```
   box_label(30, 20, 10) -> "30 x 20 x 10 cm"
   ```

   *Return: a str.*

9. **A status as a badge** (P514)

   Write a function `badge(status)` that turns a status code into a badge for
   a screen: capitals, underscores as spaces, square brackets round it --
   '[OUT FOR DELIVERY]'. replace(), upper(), and an f-string for the brackets.

   ```
   badge("out_for_delivery") -> "[OUT FOR DELIVERY]"
   ```

   *Return: a str.*

10. **A tracking message** (P515)

    Write a function `tracking_message(code, status)` that returns a sentence
    for the customer: 'Parcel MB-0012 is out for delivery.' -- the status with
    its underscores turned to spaces, a full stop at the end.

    ```
    tracking_message("MB-0012", "out_for_delivery") -> "Parcel MB-0012 is out for delivery."
    ```

    *Return: a str.*

## 3 - Checks and filters (5)

The code kept and the weight tested, a rule that applies only if the status is
present, the LAST position remembered by a loop, a key that converts to int, and
a set of what came before.

11. **The codes of the parcels over the limit** (P516)

    Two lists line up: parcel codes and their weights. Write a function
    `heavy_codes(codes, weights, limit)` that returns the codes of the parcels
    weighing MORE than the limit, in order. zip() the two lists in a
    comprehension, test the weight, keep the code.

    ```
    heavy_codes(["MB-0012", "CH-0007", "WW-0002"], [2500, 12000, 11000], 10000) -> ["CH-0007", "WW-0002"]
    ```

    *Return: a list of str.*

12. **Is the trail well formed?** (P517)

    A trail is well formed when it starts with 'collected' and, if 'delivered'
    appears at all, it is the LAST entry. Write a function `trail_ok(trail)`
    that returns True or False; an empty trail is not well formed. Guard the
    empty case, then test the first entry, then the delivery rule.

    ```
    trail_ok(["collected", "departed", "delivered"]) -> True
    ```

    *Return: True or False.*

13. **The trail since the last failure** (P518)

    Write a function `since_last_failure(trail)` that returns the entries
    after the LAST 'failed' -- or the whole trail if there is none. index()
    finds the first occurrence only, so find the last by searching the
    reversed trail, or by looping to remember the latest position.

    ```
    since_last_failure(["collected", "out_for_delivery", "failed", "out_for_delivery", "failed", "out_for_delivery", "delivered"]) -> ["out_for_delivery", "delivered"]
    ```

    *Return: a list of str.*

14. **Codes in numeric order, not text order** (P519)

    Parcel codes are not always zero-padded, and 'MB-100' sorts before 'MB-7'
    as text. Write a function `by_number(codes)` that returns the codes sorted
    by the NUMBER after the hyphen. sorted() with a key that splits and
    converts.

    ```
    by_number(["MB-100", "MB-7", "MB-23"]) -> ["MB-7", "MB-23", "MB-100"]
    ```

    *Return: a list of str.*

15. **Which scans are repeats** (P520)

    A scanner sometimes reads the same code twice. Write a function
    `repeat_flags(codes)` that returns a list of True and False, one per code,
    True when that code has ALREADY appeared earlier in the list. A loop with
    a set of what has been seen so far.

    ```
    repeat_flags(["MB-1", "CH-2", "MB-1", "MB-1"]) -> [False, False, True, True]
    ```

    *Return: a list of bool.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,741 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
