# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the parcel-courier scheme,
the third set on it, at two tools per question with the tiers named by
task, on tools the first two courier sets left out, and three writable
questions; the prompts name the tool but do not write the statement.
**Fifteen Python** at the easy level of the last five sets: everyday
tasks over plain lists and strings in the courier's terms, with no maths
and no dicts.

| Stage | SQL questions |
|---|---|
| 1 - Along the trail | 1-3 |
| 2 - Regions and routes | 4-6 |
| 3 - Weight and money | 7-9 |
| 4 - Couriers and time | 10-12 |
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
instead is triggers, generated columns and temporary tables -- and each of
questions 13 to 15 is one of those.

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

**Driver statements.** Question 13 inserts two 'delivered' scans *after*
your script: one for parcel 1, which is already delivered and must be
refused, and one for parcel 40, which is lost and must be accepted. The
refusal is reported in the status bar, not treated as an error. Questions
14 and 15 are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE TRIGGER no_double_delivery BEFORE INSERT ON scans WHEN NEW.status = 'delivered' AND (SELECT delivered_at FROM parcels WHERE parcel_id = NEW.parcel_id) IS NOT NULL BEGIN SELECT RAISE(ABORT, '...'); END` |
| 14 | `ALTER TABLE parcels ADD COLUMN weight_kg REAL GENERATED ALWAYS AS (weight_g / 1000.0) VIRTUAL` |
| 15 | `CREATE TABLE refunds (...); CREATE TEMP TABLE lost AS SELECT parcel_id ...; INSERT INTO refunds (parcel_id, cents) SELECT ... WHERE parcel_id IN (SELECT parcel_id FROM lost)` |

## Things the data does on purpose

- **27,146 delivery attempts were made, and each took about 223 minutes to its
  outcome**, which question 1 times with LEAD; one in eight ends in a failure
  on every vehicle.
- **The 271 parcels not yet delivered sit at 4 different stages**, by their
  latest scan, and 113 of them are not moving at all -- question 2's
  LAST_VALUE, once the frame is opened.
- **Every region sends most of its parcels to itself, the south 2,401 of
  them**, question 4's matrix; the south still sends 1,136 more than it
  receives, question 5's biggest imbalance.
- **Only 40 of the 620 senders have used two depots**, question 6's count with
  COUNT(DISTINCT); mostly Old Foundry's customers after it closed.
- **The heaviest quarter of parcels starts at 2,759 grams**, question 7's
  fourth band; express costs 578.1 cents a kilogram to economy's 229.2,
  question 8's ratio of sums.
- **Millbank's customers owe 193,580 cents on unpaid invoices**, question 9's
  biggest figure, beside the most paid.
- **A bike courier is idle 205.5 days of their span on average**, question
  10's figure once the days are counted as distinct dates; the running total
  of question 11 passes 12,000 after 9 months.
- **5 couriers have been here under a year**, the band question 12's CASE
  loses when the ranges are tested widest-first.
- **The lost parcels' postage comes to 79,650 cents**, question 15's refunds;
  a CHECK keeps postage positive, which is why the refund is a row elsewhere.
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
trails, weights, codes and dates for questions 1 to 5, ids, counts and
names for 6 to 10, codes, services and trails for 11 to 15. Each prompt
shows one example call with its answer, and Run adds a few more, including
the empty list or the edge the question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Along the trail (3)

LEAD rather than LAG to pair an attempt with its outcome, LAST_VALUE with ROWS
BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING, and SUM of a comparison
where COUNT of a CASE with ELSE 0 counts everything.

1. **What happens after the van leaves** (Q1252)

   For each vehicle type: how many 'out_for_delivery' scans its couriers made
   that were followed by another scan, the average minutes from that scan to
   the next one, and how many of those next scans were a failure. A window
   function that looks one row FORWARD within the parcel's trail, in a CTE;
   then group by the courier's vehicle.

   *Return: vehicle, attempts, avg_minutes, failed*

2. **Where the moving parcels are** (Q1253)

   For the parcels not yet delivered: how many are at each stage, by the
   status of their LATEST scan. LAST_VALUE over the parcel's trail gives it on
   every row once the frame is opened to the whole partition -- the default
   frame stops at the current row -- and DISTINCT then collapses each parcel
   to one row.

   *Return: last_status, parcels*

3. **Attempts, failures and deliveries, vehicle by vehicle** (Q1254)

   For each vehicle type, three counts side by side as columns: its couriers'
   'out_for_delivery' scans, 'failed' scans and 'delivered' scans. One GROUP
   BY and three conditional sums -- a pivot by hand.

   *Return: vehicle, attempts, failures, deliveries*

## 2 - Regions and routes (3)

json_group_object fed one row per key, UNION ALL where UNION would fold the
stack to ten rows, and COUNT(DISTINCT) in HAVING where COUNT would pass nearly
everyone.

4. **Where each region's parcels go, as one JSON object** (Q1255)

   For each origin region: a JSON object whose keys are the five destination
   regions and whose values are the parcel counts, keys in alphabetical order.
   Count by region pair first -- not by depot pair -- then json_group_object
   per origin region.

   *Return: region, destinations*

5. **Parcels leaving each region, and arriving** (Q1256)

   For each region: the parcels collected there, the parcels delivered to it,
   and the difference (in minus out). Stack the two ends of every parcel with
   UNION ALL -- a row tagged 'out' for the origin, one tagged 'in' for the
   destination -- and total the stack in one GROUP BY.

   *Return: region, out, in_, net*

6. **Customers who use more than one depot** (Q1257)

   For each kind of customer: how many of its senders have handed parcels in
   at MORE THAN ONE depot. Per customer, the number of DIFFERENT origin
   depots, tested in HAVING; then a count per kind.

   *Return: kind, multi_depot*

## 3 - Weight and money (3)

NTILE ordered by the thing you want bands of, total over total rather than an
average of rates, and FILTER (WHERE ...) on one aggregate so the others see
every row.

7. **Parcels in four weight bands of equal size** (Q1258)

   Split the parcels into four equal groups by weight, the lightest quarter
   first: for each, the lightest and heaviest weight, and the average postage
   in whole cents. A window function that deals rows into numbered buckets,
   ordered by weight, in a CTE.

   *Return: quartile, min_g, max_g, avg_postage*

8. **What a kilogram costs to send** (Q1259)

   For each service: the postage per kilogram in cents, to one decimal, as a
   RATIO OF SUMS -- all the postage over all the weight -- and not as an
   average of each parcel's own rate.

   *Return: service, cents_per_kg*

9. **Paid and unpaid, side by side, by home depot** (Q1260)

   For each depot, of the customer's home: the invoice money paid, the invoice
   money unpaid, and the number of unpaid invoices -- all three from one GROUP
   BY. SQLite's FILTER clause puts a condition on one aggregate without
   touching the others.

   *Return: name, paid_cents, unpaid_cents, unpaid_invoices*

## 4 - Couriers and time (3)

A span in days minus COUNT(DISTINCT date), SUM OVER (ORDER BY) for a running
total, and a CASE whose ranges are tested from the narrowest up.

10. **Days without a delivery** (Q1261)

    For each vehicle type: its couriers who have delivered, and their average
    number of idle days -- the days inside the span from their first delivery
    to their last on which they delivered nothing, to one decimal. Per
    courier, the span in days (last minus first, plus one) minus the distinct
    delivery days; then average by vehicle.

    *Return: vehicle, couriers, avg_idle_days*

11. **Parcels to date, month by month** (Q1262)

    For each month: the parcels collected, and the running total of parcels
    collected since the data began. A CTE of parcels per month, then a window
    SUM with an ORDER BY, whose default frame runs from the first row to the
    current one.

    *Return: month, parcels, to_date*

12. **Couriers by how long they have been here** (Q1263)

    Couriers in three tenure bands as of 2026-06-30 -- 'under a year', '1 to 3
    years', '3 years or more' -- and within each band by vehicle, with the
    count. A CASE with ranges on the days since hiring, tested from the
    shortest band up so that each WHEN can assume the earlier ones failed;
    couriers who have left still count by their hire date.

    *Return: band, vehicle, couriers*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger WHEN with a subquery before
RAISE, 1000.0 in a generated column, and a TEMP table named once and used once.

13. **A parcel cannot be delivered twice** (Q1264)

    Write a BEFORE INSERT trigger on scans that refuses a 'delivered' scan for
    a parcel that already has a delivered_at, by raising an error -- and lets
    every other scan through. The question then inserts a 'delivered' scan for
    parcel 1, which is delivered, and one for parcel 40, which is not.

    *Checked: how many scans dated 2026-07-01 or later got in*

14. **Kilograms, computed on the fly** (Q1265)

    Add a column weight_kg to parcels that is computed from weight_g rather
    than stored: a REAL generated column, VIRTUAL, holding the weight in
    kilograms with its fraction. Mind the division.

    *Checked: the column's average to three decimals, its maximum, and the maximum's storage type*

15. **Refunds for the lost parcels** (Q1266)

    Three steps: create a table refunds with parcel_id as its primary key and
    a cents column; create a TEMP table of the lost parcels' ids -- not
    delivered, and the latest scan a failure, as in question 2; then INSERT
    into refunds, from a SELECT, each lost parcel's id and its postage.

    *Checked: how many refunds there are, and the cents added up*

# Python

## 1 - Counting and finding (5)

index(value, start) with `in` on the same slice, n - 1 for the n-th largest,
int() before comparing a number in text, < not <= for 'strictly before', and the
last entry rather than anywhere in the trail.

1. **The next attempt after a point in the trail** (P521)

   Write a function `next_after(trail, status, start)` that returns the
   position of the first occurrence of the status at or after position
   `start`, or -1 if there is none from there on. index() takes a second
   argument that says where to begin looking; test with `in` on a slice first.

   ```
   next_after(["out_for_delivery", "failed", "out_for_delivery", "delivered"], "out_for_delivery", 1) -> 2
   ```

   *Return: an int.*

2. **The second-heaviest parcel** (P522)

   Write a function `nth_heaviest(weights, n)` that returns the n-th largest
   weight -- 1 for the heaviest, 2 for the next -- or None when there are
   fewer than n weights. sorted() largest first, then an index, behind a
   length check.

   ```
   nth_heaviest([2500, 7500, 1200, 3000], 2) -> 3000
   ```

   *Return: an int, or None.*

3. **Codes numbered above a line** (P523)

   A parcel code's number follows the hyphen, zero-padded. Write a function
   `numbered_above(codes, n)` that returns the codes whose number is greater
   than n, in order. Split at the hyphen and convert the part after it inside
   the comprehension's test.

   ```
   numbered_above(["MB-0012", "CH-0100", "WW-0099"], 50) -> ["CH-0100", "WW-0099"]
   ```

   *Return: a list of str.*

4. **Deliveries before the cut-off** (P524)

   Write a function `before(dates, cutoff)` that returns how many of the ISO
   dates fall strictly before the cut-off date. ISO dates compare correctly as
   text, so a sum of comparisons does it with no parsing.

   ```
   before(["2026-03-04", "2025-11-30", "2026-01-15"], "2026-01-01") -> 1
   ```

   *Return: an int.*

5. **Is anything in the batch lost?** (P525)

   A parcel is lost when its trail ENDS on 'failed'. Write a function
   `any_lost(trails)` that returns True when any trail in the list ends that
   way and False otherwise, empty trails ignored. any() over a generator that
   tests each trail's last entry behind a non-empty check.

   ```
   any_lost([["collected", "delivered"], ["collected", "out_for_delivery", "failed"]]) -> True
   ```

   *Return: True or False.*

## 2 - Labels (5)

:04d and replace() inside the braces, == 1 for the plural with // and % for the
money, round() of a fraction of the width, quotes only round the fields that
need them, and len(w) - 1 stars.

6. **An invoice number from its parts** (P526)

   Invoices are numbered 'INV-202605-0004': the period with its hyphen
   removed, then the customer id padded with zeros to four digits. Write a
   function `invoice_number(customer_id, period)` that builds it. replace()
   for the period and a format spec for the padding.

   ```
   invoice_number(4, "2026-05") -> "INV-202605-0004"
   ```

   *Return: a str.*

7. **A one-line summary of the month** (P527)

   Write a function `month_summary(parcels, cents)` that returns '18 parcels,
   $148.20': the count with 'parcel' made plural unless it is exactly 1, then
   the money as dollars with two digits of cents. An if for the plural, // and
   % with a :02d for the money.

   ```
   month_summary(18, 14820) -> "18 parcels, $148.20"
   ```

   *Return: a str.*

8. **A percentage as a bar of hashes** (P528)

   Write a function `bar(pct, width)` that returns a bar of '#' characters
   whose length is the percentage of the width, rounded to the nearest whole
   character, padded with '.' to the full width: bar(45, 20) is nine hashes
   and eleven dots. round(), then string multiplication for each part.

   ```
   bar(45, 20) -> "#########..........."
   ```

   *Return: a str.*

9. **An address as a CSV line** (P529)

   Write a function `csv_line(fields)` that joins the fields with commas,
   wrapping in double quotes any field that itself contains a comma, so the
   line can be read back. A comprehension with a conditional expression,
   inside join().

   ```
   csv_line(["Flat 2, 14 Harbour Street", "Millbank", "NG1"]) -> '"Flat 2, 14 Harbour Street",Millbank,NG1'
   ```

   *Return: a str.*

10. **A name reduced to initials and stars** (P530)

    For a screen that must not show a full name, write a function
    `mask_name(name)` that keeps the first letter of each word and replaces
    the rest with stars, one per letter: 'H**** U****'. A comprehension over
    split(), joined with spaces.

    ```
    mask_name("Hamid Uddin") -> "H**** U****"
    ```

    *Return: a str.*

## 3 - Checks and filters (5)

Two parts tested separately after a length check, a key that is a list's index
method, i + 1 so the status is in neither half, removeprefix() against
replace(), and a filtered generator inside max(default=None).

11. **Only the codes that are well formed** (P531)

    A well-formed code is letters, a hyphen, then digits: 'MB-0012', 'HC-7'.
    Write a function `well_formed(codes)` that keeps only the codes that have
    exactly one hyphen with letters before it and digits after it. split('-')
    into two parts, then isalpha() and isdigit() on them.

    ```
    well_formed(["MB-0012", "CH0007", "WW-00A2", "HC-7"]) -> ["MB-0012", "HC-7"]
    ```

    *Return: a list of str.*

12. **Services in priority order** (P532)

    Parcels are loaded express first, then standard, then economy. Write a
    function `by_priority(services)` that returns the services sorted into
    that order, repeats kept. A list of the three names in priority order, and
    sorted() with its index() as the key.

    ```
    by_priority(["economy", "express", "standard", "express"]) -> ["express", "express", "standard", "economy"]
    ```

    *Return: a list of str.*

13. **The trail before and after arrival** (P533)

    Write a function `split_at(trail, status)` that returns two lists as a
    tuple: the entries before the status's first appearance, and the entries
    after it -- the status itself in neither. When the status is missing, the
    first list is the whole trail and the second is empty. `in`, index() and
    two slices.

    ```
    split_at(["collected", "departed", "arrived", "out_for_delivery", "delivered"], "arrived") -> (["collected", "departed"], ["out_for_delivery", "delivered"])
    ```

    *Return: a tuple of two lists.*

14. **Codes with the depot stripped off** (P534)

    Write a function `strip_depot(codes, prefix)` that returns each code with
    the prefix removed from its FRONT if it is there, and unchanged otherwise.
    str.removeprefix() does exactly that for one string; a comprehension
    applies it to all.

    ```
    strip_depot(["MB-0012", "MB-0031", "CH-0007"], "MB-") -> ["0012", "0031", "CH-0007"]
    ```

    *Return: a list of str.*

15. **The latest delivery in the batch** (P535)

    Two lists line up scan by scan: the date and the status. Write a function
    `latest_delivery(dates, statuses)` that returns the most recent date among
    the scans whose status is 'delivered', or None if there is none. zip() the
    lists, keep the delivered dates, and max() with a default.

    ```
    latest_delivery(["2026-03-04", "2026-03-06", "2026-03-05"], ["delivered", "failed", "delivered"]) -> "2026-03-05"
    ```

    *Return: a str, or None.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,771 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
