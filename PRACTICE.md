# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the parcel-courier scheme,
the fifth set on it, at two tools per question with the tiers named by
task, on tools the first four courier sets left out, and three writable
questions; the prompts name the tool but do not write the statement.
**Fifteen Python** at the easy level of the last seven sets: everyday
tasks over plain lists and strings in the courier's terms, with no maths
and no dicts.

| Stage | SQL questions |
|---|---|
| 1 - Sets and ties | 1-3 |
| 2 - Dates, precisely | 4-6 |
| 3 - Text, types and lists | 7-9 |
| 4 - Flags and totals | 10-12 |
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
instead is constraints, indexes, triggers and plain DML -- and each of
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

**Driver statements.** Question 13 inserts three scans *after* your
script: a second 'delivered' scan for parcel 1, which the index must
refuse, a first one for parcel 40 and a 'failed' scan for parcel 1, which
it must let through. Question 15 deletes every unpaid invoice issued
before July 2025, which the trigger must log. Question 14 is graded on
what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE UNIQUE INDEX one_delivery ON scans(parcel_id) WHERE status = 'delivered'` |
| 14 | `UPDATE depots SET bays = bays + CASE region WHEN 'central' THEN 10 ELSE 4 END WHERE closed_on IS NULL` |
| 15 | `CREATE TABLE written_off (...); CREATE TRIGGER log_write_off AFTER DELETE ON invoices BEGIN INSERT INTO written_off (...) VALUES (OLD.invoice_id, OLD.customer_id, OLD.amount_cents); END` |

## Things the data does on purpose

- **605 of the 620 senders have used both express and economy**, question 1's
  intersection; with UNION it would be all of them.
- **13 couriers delivered in 2025 and not in 2026**, question 2's set
  difference, and every one has a leaving date; the other way round there is
  nobody.
- **4 depots tie on six couriers each**, the tie question 3's DENSE_RANK steps
  over without a gap and RANK does not.
- **1,492 parcels were delivered in June 2026, 60 of them on the 30th**, the
  day a BETWEEN ending at '2026-06-30' loses in question 4.
- **793 parcels were collected on the last day of a month, against 415 on a
  31st**, the gap question 5's date modifiers close.
- **51 of the 60 couriers were hired before the data begins**, so question 6's
  clamp to 2025-01-01 is what keeps their days inside the period.
- **10 business names run to five words**, question 7's longest; 73 customers
  have a NULL postcode area, the rows typeof labels 'null' in question 8.
- **4 depots collect more than the average depot's 2,400**, question 10's
  list, which dividing by the nine open depots would cut to three; 5 depots
  have a lorry driver still working, question 11's flags.
- **Old Foundry collected nothing in June 2026**, so question 12's SUM for it
  is NULL and its TOTAL 0.0; 84 unpaid invoices were issued before July 2025,
  the ones question 15's driver deletes.
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
clock times, codes and statuses for questions 1 to 5, counts, times,
weights and dates for 6 to 10, codes, weights and trails for 11 to 15.
Each prompt shows one example call with its answer, and Run adds a few
more, including the empty list or the edge the question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Sets and ties (3)

INTERSECT for 'both' where UNION is 'either', EXCEPT whose operand order is the
question, and DENSE_RANK, which counts the distinct values ahead where RANK
counts the rows.

1. **Customers who have used both ends of the price list** (Q1282)

   For each kind of customer: how many have sent at least one EXPRESS parcel
   and at least one ECONOMY parcel. Two lists of customer ids, one per
   service, combined with the set operator that keeps only what is in both.

   *Return: kind, both_services*

2. **Couriers who delivered last year and not this** (Q1283)

   The couriers who delivered at least one parcel in 2025 and none in 2026:
   name and vehicle. Two lists of courier ids by delivery year, subtracted
   with the set operator whose order of operands matters.

   *Return: name, vehicle*

3. **Depots ranked by staff, ties sharing a place** (Q1284)

   Every depot with the number of couriers based there, and its rank by that
   number, most couriers first -- depots with the same number share a rank,
   and the next rank follows straight on with no gap. Count per depot in a
   CTE, then the ranking window function that does not skip.

   *Return: name, couriers, rank*

## 2 - Dates, precisely (3)

>= the first day and < the day after instead of BETWEEN, 'start of month', '+1
month', '-1 day' for a month's last day whatever its length, and scalar MAX and
MIN to clamp a span to the period.

4. **June's deliveries, and the day BETWEEN loses** (Q1285)

   For each vehicle type: the parcels its couriers delivered in June 2026.
   delivered_at carries a time of day, so a range that ends at '2026-06-30'
   stops at midnight on the 30th; use a half-open range, up to but not
   including the first of July.

   *Return: vehicle, deliveries*

5. **Handed in on the last day of the month** (Q1286)

   For each service: its parcels, and how many were collected on the LAST day
   of a calendar month -- the 31st of January, the 28th of February 2025, the
   30th of April. The last day of any date's month comes from chaining date
   modifiers: back to the start of the month, forward a month, back a day.

   *Return: service, parcels, month_end*

6. **Days on the payroll inside the data** (Q1287)

   For each vehicle type: its couriers, and the average number of days they
   were employed INSIDE the data period, 2025-01-01 to 2026-06-30, to one
   decimal. A courier hired in 2019 counts from the period's start; one who
   left counts to their leaving date. The two-argument MAX and MIN pick the
   later of two dates and the earlier.

   *Return: vehicle, couriers, avg_days*

## 3 - Text, types and lists (3)

Spaces counted by LENGTH minus LENGTH(REPLACE(...)) and one added for the words,
typeof with COUNT(*) so the NULLs are counted, and json_each to join a list that
arrives as text.

7. **How many words in a customer's name** (Q1288)

   For each kind of customer and each number of words a name has: how many
   customers. Words are spaces plus one, and the spaces are counted by
   measuring the name with and without them -- LENGTH and REPLACE.

   *Return: kind, words, customers*

8. **What the postcode area column actually holds** (Q1289)

   For each kind of customer: the storage types found in postcode_area and how
   many customers have each. typeof() names a value's type, and NULL is one of
   them.

   *Return: kind, storage_type, customers*

9. **Parcels bound for the depots on a list** (Q1290)

   A caller hands you depot ids as a JSON array, '[3, 6, 10, 42]'. For each
   depot on the list that exists: its name and how many parcels were addressed
   to it. json_each() turns the array into rows you can join on.

   *Return: name, parcels*

## 4 - Flags and totals (3)

HAVING compared with the average of the per-depot counts, EXISTS as a 1-or-0
column where a LEFT JOIN's COUNT(*) counts the empty match, and TOTAL for the
depot with nothing in June.

10. **Depots busier than the average depot** (Q1291)

    The depots where more parcels have been collected than at the AVERAGE
    depot, with their count. The average is an aggregate of an aggregate --
    the mean of the per-depot counts, the closed depot included -- compared
    with in HAVING.

    *Return: name, parcels*

11. **Which depots can take a lorry load** (Q1292)

    For every depot: a 1 or 0 saying whether it has a lorry driver still
    working there, and how many. EXISTS is an expression, so it can sit in the
    SELECT list as a column; a scalar subquery gives the count.

    *Return: name, has_lorry, lorry_drivers*

12. **June's postage at every depot, zero included** (Q1293)

    For every depot, the closed one included: the postage of the parcels
    collected there in June 2026, in dollars. A LEFT JOIN from depots with the
    June condition in ON, and TOTAL rather than SUM: SUM of no rows is NULL,
    TOTAL of no rows is 0.0.

    *Return: name, june_postage*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A UNIQUE index with a WHERE of its own,
a CASE inside SET with a WHERE on the UPDATE, and OLD in an AFTER DELETE
trigger.

13. **One delivery scan per parcel, enforced** (Q1294)

    A parcel may have many scans but only ONE with status 'delivered'. Create
    a UNIQUE index on scans that enforces exactly that and nothing more -- a
    partial index, with a WHERE of its own. The question then inserts a second
    'delivered' scan for parcel 1, a first one for parcel 40, and a 'failed'
    scan for parcel 1.

    *Checked: how many scans dated July got in, and how many of them are deliveries*

14. **More loading bays, more in the centre** (Q1295)

    Every depot still open gets more loading bays: ten more in the central
    region, four more elsewhere. ONE UPDATE whose SET adds a CASE on region,
    with a WHERE that leaves the closed depot alone.

    *Checked: each region's bays added up*

15. **A record of every invoice written off** (Q1296)

    No invoice should vanish without a trace. Create a table written_off with
    invoice_id as its primary key, customer_id and amount_cents, all required;
    then an AFTER DELETE trigger on invoices that copies the removed row's
    three values into it. The question then deletes every unpaid invoice
    issued before July 2025.

    *Checked: how many rows the log has, the cents added up, and its lowest invoice_id*

# Python

## 1 - Counting and finding (5)

start <= t < end so windows sit side by side, next() with a default, count * 2 >
len for a strict majority, sets before len() so repeats count once, and
split('-') before int().

1. **Scans inside a time window** (P551)

   Scan times are 'HH:MM' strings. Write a function `in_window(times, start,
   end)` that returns how many fall in the window that includes its start and
   EXCLUDES its end. Zero-padded clock text compares correctly, so a chained
   comparison inside sum() does it.

   ```
   in_window(["08:05", "09:00", "09:59", "10:00", "11:30"], "09:00", "10:00") -> 2
   ```

   *Return: an int.*

2. **The code with a given number** (P552)

   Write a function `find_code(codes, n)` that returns the first code whose
   number after the hyphen equals n, or None if no code has that number.
   next() over a generator, with a second argument for the nothing-found case.

   ```
   find_code(["MB-0012", "CH-0007", "WW-0100"], 7) -> "CH-0007"
   ```

   *Return: a str, or None.*

3. **Was most of the batch delivered?** (P553)

   Write a function `mostly_delivered(statuses)` that returns True when MORE
   than half of the statuses are 'delivered', and False otherwise -- exactly
   half is not more than half, and an empty batch is False. count(), doubled,
   against the length.

   ```
   mostly_delivered(["delivered", "delivered", "failed"]) -> True
   ```

   *Return: True or False.*

4. **How many codes two vans share** (P554)

   Two vans' manifests are lists of parcel codes, and a code may have been
   scanned twice. Write a function `shared(first, second)` that returns how
   many DIFFERENT codes appear on both. Two sets, intersected, measured.

   ```
   shared(["MB-1", "MB-2", "MB-2", "CH-3"], ["MB-2", "CH-3", "WW-4"]) -> 2
   ```

   *Return: an int.*

5. **The numbers in a batch, added up** (P555)

   As a quick check on a batch, the numbers after the hyphens are added up.
   Write a function `number_total(codes)` that returns that sum. The depot
   code can be any length, so split at the hyphen rather than slicing.

   ```
   number_total(["MB-0012", "CHB-0007", "WW-100"]) -> 119
   ```

   *Return: an int.*

## 2 - Labels (5)

:+d for a sign on both directions with zero as its own case, both times in
minutes before subtracting, a single value when the range is empty, ljust with a
fill character, and reversed parts joined with slashes.

6. **A change with its sign showing** (P556)

   Write a function `change_label(before, after)` that returns the change as a
   whole-number percentage of before with its sign: '+39%' for a rise, '-5%'
   for a fall, '0%' for no change, and 'n/a' when before is 0. The format spec
   '+' shows a plus on positive numbers.

   ```
   change_label(1099, 1523) -> "+39%"
   ```

   *Return: a str.*

7. **Minutes from one scan to the next** (P557)

   Write a function `minutes_between(start, end)` that takes two 'HH:MM' times
   on the same day, the second not before the first, and returns the minutes
   between them. Turn each into minutes since midnight -- hours times 60 plus
   minutes -- and subtract.

   ```
   minutes_between("08:05", "09:20") -> 75
   ```

   *Return: an int.*

8. **A weight band as a label** (P558)

   Write a function `band_label(low, high)` that returns a weight band in
   kilograms as '2-5 kg', or as just '3 kg' when the two ends are the same. A
   conditional expression between two f-strings.

   ```
   band_label(2, 5) -> "2-5 kg"
   ```

   *Return: a str.*

9. **A line of the price list** (P559)

   Write a function `price_line(name, cents, width)` that returns the name
   padded on the right with dots to the width, then the price as '$3.50':
   'Economy.....$3.50'. str.ljust() takes a fill character; the price is whole
   dollars and two-digit cents.

   ```
   price_line("Economy", 350, 12) -> "Economy.....$3.50"
   ```

   *Return: a str.*

10. **A date the British way round** (P560)

    Write a function `uk_date(iso)` that turns 'YYYY-MM-DD' into 'DD/MM/YYYY':
    the three parts in the opposite order, joined by slashes. split(),
    reverse, join().

    ```
    uk_date("2026-03-04") -> "04/03/2026"
    ```

    *Return: a str.*

## 3 - Checks and filters (5)

A set of lower-cased codes beside a list of originals, zip of [::2] with [1::2],
a membership test before rebuilding, < on every neighbouring pair, and a list
times a number that may be negative.

11. **Repeats dropped, whatever their case** (P561)

    A scanner reads the same code in different cases. Write a function
    `unique_codes(codes)` that keeps the FIRST spelling of each code and drops
    later ones that differ only in case, order otherwise unchanged. A loop
    with a set of the lower-cased codes seen so far.

    ```
    unique_codes(["MB-12", "mb-12", "CH-7", "Mb-12"]) -> ["MB-12", "CH-7"]
    ```

    *Return: a list of str.*

12. **A flat list of scans, paired up** (P562)

    A scanner sends one flat list: a code, its status, the next code, its
    status, and so on. Write a function `pair_up(items)` that returns a list
    of (code, status) tuples; a code left over at the end with no status is
    dropped. zip the even positions with the odd ones, each a slice with a
    step.

    ```
    pair_up(["MB-1", "collected", "MB-2", "delivered"]) -> [("MB-1", "collected"), ("MB-2", "delivered")]
    ```

    *Return: a list of tuples.*

13. **An urgent parcel moved to the front** (P563)

    Write a function `to_front(codes, urgent)` that returns a new list with
    the urgent code first and the others in their original order -- or an
    unchanged copy if the urgent code is not in the list at all. A membership
    test, then the code plus everything that is not it.

    ```
    to_front(["MB-1", "CH-2", "WW-3"], "CH-2") -> ["CH-2", "MB-1", "WW-3"]
    ```

    *Return: a list of str.*

14. **Are the weights strictly rising?** (P564)

    Parcels are stacked lightest on top. Write a function `rising(weights)`
    that returns True when each weight is STRICTLY greater than the one before
    -- two equal weights in a row do not count -- and True for a list of one
    or none. all() over the neighbouring pairs from zip.

    ```
    rising([500, 750, 1200]) -> True
    ```

    *Return: True or False.*

15. **A trail padded to a fixed length** (P565)

    A report needs every trail to have at least n entries. Write a function
    `pad_to(trail, n, filler)` that returns the trail with the filler added on
    the end until it is n long -- and a trail already n long or longer
    unchanged, nothing cut off. A list times a number, added on.

    ```
    pad_to(["collected", "delivered"], 4, "-") -> ["collected", "delivered", "-", "-"]
    ```

    *Return: a list of str.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,831 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
