# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on a NEW schema, a regional
parcel courier, at two tools per question with the tiers named by task,
and three writable questions; the prompts name the tool but do not write
the statement. **Fifteen Python** at the easy level of the last three
sets: everyday tasks over plain lists and strings in the courier's terms,
with no maths and no dicts.

| Stage | SQL questions |
|---|---|
| 1 - The parcel's trail | 1-3 |
| 2 - Depots and routes | 4-6 |
| 3 - Customers and money | 7-9 |
| 4 - People and time | 10-12 |
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
instead is triggers, constraints and plain DML -- and each of questions 13
to 15 is one of those.

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

**Driver statements.** Question 13 inserts two scans *after* your script:
a 'delivered' scan for parcel 40, which the trigger must act on, and a
'failed' scan for parcel 122, which it must ignore. Questions 14 and 15
are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE TRIGGER complete_on_delivery AFTER INSERT ON scans WHEN NEW.status = 'delivered' BEGIN UPDATE parcels SET ... WHERE parcel_id = NEW.parcel_id; END` |
| 14 | `UPDATE parcels SET postage_cents = postage_cents + 500 WHERE collected_at >= '2026-06-01' AND weight_g > 10000` |
| 15 | `DELETE FROM customers WHERE NOT EXISTS (SELECT 1 FROM parcels ...) AND NOT EXISTS (SELECT 1 FROM invoices ...)` |

## Things the data does on purpose

- **5,954 of the 24,000 parcels were handed in by strangers at the counter**
  and have no customer, which question 7 counts as a category; it is also why
  question 15's NOT IN would delete nobody.
- **80 of the 700 customers have never sent a parcel**, the ones question 15
  removes; 73 have no postcode area recorded, and 15 of the 60 couriers have
  left.
- **Old Foundry closed on 2026-02-01**, and the 558 parcels its customers have
  sent since were all handed in at Central Hub, the switch question 6 shows
  month by month.
- **3,345 parcels came back to the depot at least once, 72 of them twice**,
  which is why question 3 counts with EXISTS rather than a join; 113 were
  never delivered at all.
- **Express gets 55.4 per cent of its parcels there within 48 hours and
  economy takes 94 hours on average**, question 2's figures -- in hours, after
  the julianday days are multiplied up.
- **29 per cent of parcels stay at one depot**, so the local 'routes' would
  crowd out question 4's list without the WHERE; Millbank sends 827 more
  parcels than it receives, question 5's biggest imbalance.
- **Postage is a base per service plus a rate per STARTED kilogram**, which
  question 9 recovers band by band when the ceiling is computed right.
- **332 invoices are unpaid, owed by 174 of the 247 business customers**,
  question 8's list; every invoice equals its month's postage.
- **19 couriers ride bikes** and make one or two drops on a working day,
  question 10's rate once the days are counted as distinct dates.
- **Volume grew from 1,099 parcels in January 2025 to 1,523 in June 2026**, as
  customers joined, the climb question 12's LAG shows; 31 of June's 1,523
  parcels weigh over ten kilograms, the ones question 14 surcharges.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form -- but the type counts: a tuple is not a list, and 0 is not False. A
function that prints its answer instead of returning it returns None, and
None matches nothing. The inputs are everyday values in the courier's terms:
a parcel's trail of status words or two lists of depots for questions 1 to
5, a number, a code or a few strings for 6 to 10, lists of parcel codes,
weights or dates for 11 to 15. Each prompt shows one example call with its
answer, and Run adds a few more, including the empty list or the edge the
question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - The parcel's trail (3)

ROW_NUMBER restarted per parcel by PARTITION BY, julianday differences
multiplied by 24 before they are compared with hours, and SUM of an EXISTS where
a join would count attempts.

1. **Each parcel's trail, step by step** (Q1222)

   For parcels 1 to 5: every scan, numbered from 1 within its own parcel in
   time order, with the status and the time. A window numbering function
   partitioned by parcel.

   *Return: parcel_id, step, status, scanned_at*

2. **How long each service really takes** (Q1223)

   For each service: the delivered parcels, the average hours from collection
   to delivery to one decimal, and the share delivered within 48 hours as a
   percentage to one decimal. julianday differences are in DAYS; the average
   of a true-or-false comparison is a share.

   *Return: service, delivered, avg_hours, within_48h_pct*

3. **Parcels that came back to the depot** (Q1224)

   For each service: its parcels, how many of them have a failed delivery
   attempt somewhere in their trail, and that as a percentage to one decimal.
   A parcel with two failed attempts counts once, which a join to scans would
   not do; EXISTS does.

   *Return: service, parcels, with_failure, pct*

## 2 - Depots and routes (3)

The same table joined twice under two aliases with the local parcels excluded,
two scalar subqueries where a double join would multiply, and two conditional
sums that follow the customers across a depot's closure.

4. **The ten busiest routes between depots** (Q1225)

   The ten depot-to-depot routes with the most parcels, by name, leaving out
   the local parcels that stay at one depot. Join depots twice, once for each
   end; group by the pair; order by the count, then by the two names so a tie
   cannot shuffle the list.

   *Return: from_depot, to_depot, parcels*

5. **Parcels in against parcels out, at every depot** (Q1226)

   For every depot: the parcels collected there, the parcels delivered to it,
   and the difference (in minus out). Two counts of the same table on two
   different keys -- scalar subqueries, or two conditional sums; joining
   parcels twice would multiply.

   *Return: name, sent, received, net*

6. **Where Old Foundry's customers went** (Q1227)

   Old Foundry closed on 2026-02-01. For each month from October 2025: how
   many parcels its customers (the ones whose home depot it is) handed in at
   Old Foundry, and how many at Central Hub. One GROUP BY on the month with
   two conditional sums on the origin.

   *Return: month, at_old_foundry, at_central_hub*

## 3 - Customers and money (3)

SUM(column IS NULL) for a NULL that means something, a WHERE before the GROUP BY
so every aggregate is over the unpaid rows, and (weight - 1) / 1000 + 1 for a
started kilogram.

7. **Walk-ins at the counter** (Q1228)

   For each service: its parcels, how many were handed in by someone with no
   customer account, and that as a percentage to one decimal. A parcel's
   customer_id is NULL for a walk-in: a NULL that means something, so it is
   counted, not skipped.

   *Return: service, parcels, walk_ins, pct*

8. **The ten customers who owe the most** (Q1229)

   The ten business customers with the most unpaid invoice money outstanding:
   their name, how many invoices are unpaid, the total owed in cents, and the
   issue date of the oldest. An unpaid invoice has no paid_on. Order by the
   total, then by customer_id to settle a tie.

   *Return: name, unpaid_invoices, owed_cents, oldest_issued*

9. **The postage table, recovered from the parcels** (Q1230)

   Postage is a base per service plus a rate per STARTED kilogram. For each
   service and each started-kilogram band from 1 to 5: how many parcels, and
   the postage they paid (one value per band). The band is integer arithmetic
   on weight_g such that 1 to 1000 grams is band 1 and 1001 to 2000 is band 2.

   *Return: service, kg_band, parcels, postage_cents*

## 4 - People and time (3)

COUNT(DISTINCT date(...)) for the days actually worked, CASE on strftime's TEXT
digit, and LAG left to return NULL on the first row.

10. **How many drops a bike courier makes in a day** (Q1231)

    For each courier on a bike: their deliveries, the number of DAYS on which
    they delivered something, and the deliveries per such day to two decimals.
    The days are a COUNT of DISTINCT dates; the span from first to last
    delivery would count the days off.

    *Return: name, deliveries, days, per_day*

11. **Which day of the week people post things** (Q1232)

    Parcels collected on each day of the week, with the day NAMED -- 'Monday',
    not '1'. strftime gives the weekday as a digit from '0' for Sunday; a CASE
    turns it into a word.

    *Return: weekday, parcels*

12. **Month on month** (Q1233)

    For each month: the parcels collected, and the change from the month
    before -- NULL for the first month, since there is nothing before it. A
    CTE of parcels per month, then a window function that looks one row back.

    *Return: month, parcels, change*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger whose WHEN clause picks the
scans that matter, an UPDATE narrowed by AND, and NOT EXISTS where NOT IN meets
a NULL.

13. **A delivery scan completes the parcel** (Q1234)

    When a scan with status 'delivered' is inserted, the parcel should be
    marked delivered: its delivered_at set to the scan's time and its
    courier_id to the scan's courier. Write an AFTER INSERT trigger on scans
    with a WHEN clause so that only delivery scans do this. The question then
    inserts a 'delivered' scan for parcel 40 and a 'failed' scan for parcel
    122.

    *Checked: parcel 40's delivered_at and courier_id, parcel 122's delivered_at, and how many parcels are delivered*

14. **A surcharge on June's heavy parcels** (Q1235)

    From June 2026 a parcel over ten kilograms carries a surcharge of 500
    cents. Add it, in one UPDATE, to the postage of every parcel collected in
    June 2026 that weighs more than 10,000 grams -- and to no other.

    *Checked: how many parcels were collected in June, and their postage added up*

15. **Clearing out the customers who never sent anything** (Q1236)

    Delete every customer who has never sent a parcel and has no invoice. Test
    'never sent' with NOT EXISTS, not NOT IN: parcels.customer_id is NULL on
    every walk-in row, and a NOT IN over a list that holds a NULL is never
    true.

    *Checked: how many customers remain, and how many of them have never sent a parcel*

# Python

## 1 - Counting and finding (5)

index() only after `in`, and -1 as an index means the LAST item; a slice up to
the delivery before count(); zip for position against position; a length check
before a negative index; split() per line summed.

1. **What happened just before the delivery** (P491)

   A parcel's trail is a list of status words in time order. Write a function
   `status_before(trail, status)` that returns the status that came right
   before the FIRST appearance of the given one, or None when it is missing or
   was the first entry.

   ```
   status_before(["collected", "departed", "arrived", "out_for_delivery", "delivered"], "delivered") -> "out_for_delivery"
   ```

   *Return: a str, or None.*

2. **How many attempts it took** (P492)

   Write a function `attempts(trail)` that returns how many 'out_for_delivery'
   entries come before the first 'delivered' -- or in the whole trail if the
   parcel was never delivered. Cut the list at the delivery with a slice, then
   count().

   ```
   attempts(["collected", "out_for_delivery", "failed", "out_for_delivery", "delivered"]) -> 2
   ```

   *Return: an int.*

3. **Parcels that never left their depot** (P493)

   Two lists line up parcel by parcel: where each was collected and where it
   was delivered. Write a function `local_count(origins, dests)` that returns
   how many parcels had the same depot at both ends. zip() walks the two lists
   together; a sum of comparisons counts.

   ```
   local_count(["Millbank", "Central Hub", "Westway"], ["Millbank", "Northgate", "Westway"]) -> 2
   ```

   *Return: an int.*

4. **The second-last scan** (P494)

   Write a function `from_end(trail, n)` that returns the n-th entry counting
   from the end -- 1 for the last, 2 for the one before it -- or None when the
   trail is too short. A negative index, behind a length check.

   ```
   from_end(["collected", "departed", "arrived", "delivered"], 2) -> "arrived"
   ```

   *Return: a str, or None.*

5. **Words across every line of a label** (P495)

   An address label is a list of lines. Write a function `total_words(lines)`
   that returns how many words there are across all the lines. split() with no
   argument handles any spacing; sum() over a generator adds the counts.

   ```
   total_words(["Flat 2", "14 Harbour Street", "Millbank"]) -> 6
   ```

   *Return: an int.*

## 2 - Labels (5)

A threshold that picks the unit, a conditional expression between two f-strings,
capitalize() against title(), a filter before join(), and max() of three sides.

6. **Grams or kilograms, whichever reads better** (P496)

   Write a function `weight_label(grams)` that returns '750 g' for anything
   under a kilogram and '2.5 kg' from a kilogram up, the kilograms to one
   decimal. An if on the threshold; division by 1000 and round(..., 1) for the
   heavier case.

   ```
   weight_label(2500) -> "2.5 kg"
   ```

   *Return: a str.*

7. **A route label that knows when nothing moved** (P497)

   Write a function `route_label(origin, dest)` that returns 'Millbank ->
   Central Hub' for a parcel that moved between depots and 'Millbank (local)'
   for one delivered from the depot it was handed in at. A conditional
   expression choosing between two f-strings.

   ```
   route_label("Millbank", "Millbank") -> "Millbank (local)"
   ```

   *Return: a str.*

8. **A status code as words** (P498)

   Status codes are written like 'out_for_delivery'. Write a function
   `status_words(code)` that returns them as a phrase with a capital only at
   the start: 'Out for delivery'. replace() the underscores, then
   capitalize().

   ```
   status_words("out_for_delivery") -> "Out for delivery"
   ```

   *Return: a str.*

9. **An address on one line, blanks skipped** (P499)

   Address forms arrive with some lines left blank. Write a function
   `address_line(parts)` that joins the non-empty parts with ', ' into one
   line, skipping the blanks so no two commas meet. A generator that keeps the
   truthy parts, inside join().

   ```
   address_line(["Flat 2", "", "14 Harbour Street", "Millbank"]) -> "Flat 2, 14 Harbour Street, Millbank"
   ```

   *Return: a str.*

10. **Will the box fit through the hatch?** (P500)

    A parcel fits through the sorting hatch when NONE of its three sides is
    longer than the hatch. Write a function `fits(length, width, height,
    hatch)` that returns True or False. max() takes several arguments, so the
    longest side is one call.

    ```
    fits(30, 20, 10, 40) -> True
    ```

    *Return: True or False.*

## 3 - Checks and filters (5)

startswith() with the hyphen rather than `in`, zip the weights first then
sorted(), a comprehension whose expression is the test, min() and max() rather
than [0] and [-1], and a set comprehension before sorted().

11. **The parcels from one depot** (P501)

    A parcel code starts with its origin depot's two-letter code and a hyphen:
    'MB-0012'. Write a function `codes_from(codes, depot)` that returns the
    codes from that depot, in order. startswith() with the depot code and the
    hyphen, in a comprehension.

    ```
    codes_from(["MB-0012", "CH-0007", "MB-0031", "WW-0002"], "MB") -> ["MB-0012", "MB-0031"]
    ```

    *Return: a list of str.*

12. **Parcel codes, lightest first** (P502)

    Two lists line up: parcel codes and their weights. Write a function
    `by_weight(codes, weights)` that returns the codes in order of weight,
    lightest first, codes alone. zip() the weights with the codes, sorted(),
    then take the codes back out.

    ```
    by_weight(["MB-0012", "CH-0007", "WW-0002"], [2500, 750, 1200]) -> ["CH-0007", "WW-0002", "MB-0012"]
    ```

    *Return: a list of str.*

13. **Which parcels are over the limit** (P503)

    Write a function `over_limit(weights, limit)` that returns a list of True
    and False, one per parcel in order, saying whether it is over the limit. A
    comprehension whose expression is the comparison itself.

    ```
    over_limit([2500, 750, 12000], 10000) -> [False, False, True]
    ```

    *Return: a list of bool.*

14. **The first and last collection** (P504)

    Write a function `date_range(dates)` that returns the earliest and latest
    of a list of ISO dates as a tuple, or None for an empty list. ISO dates
    compare correctly as text, so min() and max() do it without parsing.

    ```
    date_range(["2026-03-04", "2025-11-30", "2026-01-15"]) -> ("2025-11-30", "2026-03-04")
    ```

    *Return: a tuple of two str, or None.*

15. **Which depots a batch of codes mentions** (P505)

    Write a function `depots_in(codes)` that returns the distinct depot codes
    -- the part before the hyphen -- mentioned in a list of parcel codes, in
    alphabetical order. Split each code at the hyphen, collect the first parts
    in a set, sort.

    ```
    depots_in(["MB-0012", "CH-0007", "MB-0031", "WW-0002"]) -> ["CH", "MB", "WW"]
    ```

    *Return: a sorted list of str.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,711 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
