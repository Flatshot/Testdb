# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the parcel-courier scheme,
the seventh set on it, at two tools per question with the tiers named by
task, on tools the first six courier sets left out. Nine read the data
and **six change it**: three single statements and three procedures of
several steps. The prompts name the tool but do not write the statement.
**Fifteen Python** at the easy level of the last nine sets: everyday
tasks over plain lists and strings in the courier's terms, with no maths
and no dicts.

| Stage | SQL questions |
|---|---|
| 1 - Joins and lookups | 1-3 |
| 2 - Calendar buckets | 4-6 |
| 3 - Whole groups | 7-9 |
| 4 - Changing rows | 10-12 |
| 5 - Procedures | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Text, tidied | 1-5 |
| 2 - Checks and searches | 6-10 |
| 3 - Lists, built and reshaped | 11-15 |

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
creates a table or a view, a second Run fails because the first one's is
still there: press Reset.

**Driver statements.** Question 14 issues a `ROLLBACK` *after* your
script. If your work was committed, there is nothing of yours left to
roll back and it stands. If your transaction was left open, everything it
did is undone and the check query shows the data as it was. Question 15
collects three new parcels, two at depot 3 and one at depot 10, which is
what makes the trigger fire. Questions 10 to 13 are graded on what your
script leaves behind.

| # | Construct |
|---|---|
| 10 | `INSERT INTO depots (name, region, bays, opened_on) SELECT '...', region, bays, '...' FROM depots WHERE name = ...` |
| 11 | `UPDATE couriers SET vehicle = 'van' WHERE courier_id IN (SELECT courier_id FROM (SELECT ..., ROW_NUMBER() OVER (PARTITION BY depot_id ORDER BY hired_on) ...) WHERE rn = 1)` |
| 12 | `DELETE FROM invoices WHERE paid_on IS NULL AND (customer_id, period) IN (SELECT ... GROUP BY 1, 2 HAVING COUNT(*) = 1)` |
| 13 | `BEGIN; CREATE TEMP TABLE ... AS SELECT courier_id ...; UPDATE couriers ...; UPDATE couriers ... IN (SELECT ...); COMMIT;` |
| 14 | `BEGIN; UPDATE parcels ...; UPDATE customers SET joined_on = (SELECT MIN(joined_on) ...) ...; DELETE FROM customers ...; COMMIT;` |
| 15 | `CREATE TABLE depot_load (...); INSERT INTO depot_load SELECT ... GROUP BY ...; CREATE TRIGGER ... AFTER INSERT ON parcels BEGIN UPDATE depot_load ...; END` |

## Things the data does on purpose

- **8 depots have hired since 2025 and 7 have lost a courier, but only 9 are
  in one list or the other**: Millbank only lost, two depots only hired, and
  Central Hub did neither, which is question 1's full join.
- **Business customers have 10,683 parcels and 2,298 invoices**, the two child
  tables that multiply each other in question 2 if they are joined before they
  are added up.
- **No two couriers at a depot were hired on the same day**, so question 3's
  most recent hire is never a tie.
- **The second quarter of 2026 is the busiest, with 4,455 parcels**, question
  4's last row; 1 June 2026 was a Monday, and the week of the 29th has only
  two days in June and 101 parcels, question 5's last.
- **283 of the 620 senders sent their first parcel in January 2025**, question
  6's first and biggest cohort.
- **The average express parcel costs 1,316 cents and the average economy one
  514**, which is why question 7 compares a parcel with its own service and
  not with everything.
- **49 customers have paid every invoice, against 221 who have paid at least
  one**, question 8's gap; 22 have only ever paid one way, question 9's total.
- **8 of the ten depots have a bike courier still employed**, the promotions
  in question 11; 156 unpaid invoices are for a month with a single parcel,
  the ones question 12 deletes.
- **Northgate lists 5 couriers and Moorside 6**, the numbers that change
  places in question 13.
- **There are 3 customers called Dmitri Sowerby**, two of them at depot 5 and
  merged in question 14; the third is someone else.
- **Northgate has collected 1,900 parcels**, the tally question 15's trigger
  moves on by two.
- **The data ends at 2026-06-30 23:59**, so a date in July 2026 is always
  after everything already there.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form -- but the type counts: a tuple is not a list, and 0 is not False. A
function that prints its answer instead of returning it returns None, and
None matches nothing. The inputs are everyday values in the courier's terms:
labels, messages and phone numbers for questions 1 to 5, codes, names,
times and form fields for 6 to 10, ranges, pairs and lists of codes for
11 to 15.
Each prompt shows one example call with its answer, and Run adds a few
more, including the empty list or the edge the question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Joins and lookups (3)

FULL OUTER JOIN for a row wherever either side has one, aggregating each child
table before joining so the two do not multiply, and ORDER BY ... LIMIT 1 in a
correlated subquery so the name and the date come from one row.

1. **Hires and leavers, depot by depot** (Q1312)

   For each depot, by name: how many couriers it has hired since 2025-01-01,
   and how many of its couriers have left. Some depots hired and lost nobody,
   some lost and hired nobody; a depot with neither is not listed, and a
   missing count is 0. Two grouped subqueries, and the join that keeps the
   unmatched rows of BOTH sides.

   *Return: depot, hired, left*

2. **Postage and invoices, side by side** (Q1313)

   For each depot, by name, and its BUSINESS customers only: the postage on
   all their parcels, and the amount on all their invoices. A customer has
   many parcels and many invoices, so joining both tables to the customer at
   once pairs every parcel with every invoice. Add each one up on its own
   first, then join the totals.

   *Return: depot, postage_cents, invoiced_cents*

3. **Each depot's newest courier** (Q1314)

   For each depot, by name: the courier it hired most recently, and the date.
   Couriers who have since left count. The name and the date must belong to
   the SAME courier: a correlated subquery that sorts that depot's couriers
   and takes one.

   *Return: depot, courier, hired_on*

## 2 - Calendar buckets (3)

(month + 2) / 3 for the quarter and || for its label, 'weekday 0' forward to
Sunday then '-6 days' back to Monday, and MIN per customer before grouping by
month so each sender is counted once.

4. **Parcels and postage by quarter** (Q1315)

   For each calendar quarter of collection, labelled like '2025-Q1': the
   parcels collected and their postage. January to March is Q1. strftime has
   no code for the quarter; it comes from the month number by integer
   arithmetic, and the label is put together with ||.

   *Return: quarter, parcels, postage_cents*

5. **June, week by week** (Q1316)

   Parcels collected in June 2026, counted by week. A week runs Monday to
   Sunday and is labelled with the DATE of its Monday. The 'weekday N' date
   modifier only ever moves a date forward, to the next such weekday or not at
   all, so reaching the Monday behind you takes a second modifier after it.

   *Return: week_starting, parcels*

6. **The month each sender first sent** (Q1317)

   For each month, as 'YYYY-MM': how many customers sent their FIRST parcel in
   it. A customer is counted once, in the month of their earliest collection;
   walk-ins are left out. An aggregate per customer, then a second grouping on
   what it found.

   *Return: month, new_senders*

## 3 - Whole groups (3)

AVG ... OVER (PARTITION BY) beside every row of its group, COUNT(*) =
COUNT(column) for 'none of them is NULL', and MIN = MAX for 'there is only one
value'.

7. **Parcels that cost twice their service's average** (Q1318)

   For each service: how many parcels paid MORE THAN DOUBLE the average
   postage of their own service. A window AVG puts the group's average beside
   every row; the comparison then needs an outer query.

   *Return: service, parcels*

8. **Customers with nothing outstanding** (Q1319)

   For each depot, by name: how many of its customers have been invoiced and
   have paid EVERY invoice. A depot with no such customer is not listed.
   COUNT(*) counts rows and COUNT(column) counts the rows where the column is
   not NULL; HAVING can compare the two.

   *Return: depot, customers*

9. **Customers who always pay the same way** (Q1320)

   Some customers have paid every invoice they have paid by the same method.
   For each method: how many customers have only ever used that one. Unpaid
   invoices have no method and do not count either way. A group holds a single
   value exactly when its smallest and its largest are the same.

   *Return: method, customers*

## 4 - Changing rows (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. One statement each: INSERT ... SELECT
mixing columns with literals, an UPDATE whose WHERE reads a window function
through a subquery, and a DELETE matching pairs as row values.

10. **A second depot, copied from the first** (Q1321)

    A new depot opens on 2026-07-01, called 'Harbour Point East'. It is in the
    same region as Harbour Point and has the same number of bays, whatever
    those are -- read them, do not type them in. One INSERT ... SELECT whose
    SELECT reads the row being copied and supplies the new name and date
    itself.

    *Checked: name, region, bays, opening and closing dates of every depot whose name starts 'Harbour Point'*

11. **The longest-serving bike courier gets a van** (Q1322)

    At each depot, the bike courier who has been there longest and is STILL
    EMPLOYED moves up to a van. A depot with no such courier promotes nobody.
    One UPDATE; which couriers is decided by a subquery that numbers the
    candidates within their depot with a window function.

    *Checked: for each vehicle, the couriers listed and how many of them are still employed*

12. **Invoices not worth chasing** (Q1323)

    An invoice for a single parcel is not worth chasing. Cancel -- delete --
    every UNPAID invoice whose period saw that customer send exactly ONE
    parcel. An invoice's period is the 'YYYY-MM' in which its parcels were
    collected. A DELETE whose WHERE matches (customer, period) PAIRS, as a row
    value, against a grouped subquery.

    *Checked: invoices left, their cents added up, how many are unpaid*

## 5 - Procedures (3)

Writable questions of several steps. SQLite has no CREATE PROCEDURE: a
transaction makes steps stand or fall together, the order of the steps is the
procedure, and a trigger is a stored body that runs on its own from then on.

13. **Two depots swap their couriers** (Q1324)

    Northgate (depot 3) and Moorside (depot 4) exchange their entire courier
    lists: everyone listed at one becomes listed at the other, leavers
    included. Two plain UPDATEs in a row will not do it -- after the first,
    the two groups cannot be told apart -- and the foreign key will not let
    anyone be parked at a depot that does not exist. Remember who was where
    before moving anyone; a TEMP table is one place to keep it. One
    transaction.

    *Checked: for depots 3 and 4: couriers listed, and the lowest courier_id among them*

14. **One customer, registered twice** (Q1325)

    Customers 67 and 201 are the same person, Dmitri Sowerby, registered twice
    at depot 5. (A third customer of that name, at another depot, is someone
    else.) Merge them into 67, in one transaction: 201's parcels become 67's;
    67 takes whichever joined_on of the two is EARLIER; then 201 is deleted.
    The order is part of the answer -- foreign keys are on, and a deleted row
    can no longer be read. The question then issues a ROLLBACK: committed work
    survives it.

    *Checked: customers of that name at depot 5, 67's joined_on, 67's parcels, and parcels with no customer*

15. **A running tally the database keeps itself** (Q1326)

    Counting 24,000 parcels every time someone asks is wasteful. Set up a
    tally in three steps: create a table depot_load with depot_id as its
    primary key and a required whole number parcels; fill it with the number
    of parcels each depot has COLLECTED so far; then create an AFTER INSERT
    trigger on parcels that adds one to the origin depot's row. The question
    then collects three new parcels, two at depot 3 and one at depot 10.

    *Checked: every row of depot_load*

# Python

## 1 - Text, tidied (5)

split() then join for spacing, two slices where capitalize() would lower the
rest, a generator that keeps what isdigit() approves, find() checked for -1
before it is used, and a character times len().

1. **A label with its spacing put right** (P581)

   Write a function `tidy_spaces(label)` that returns the label with no spaces
   at either end and exactly one space between words, however many were typed.
   split() with no argument, then join.

   ```
   tidy_spaces("  Central   Hub ") -> "Central Hub"
   ```

   *Return: a str.*

2. **A first letter capitalised, the rest left alone** (P582)

   Write a function `start_capital(text)` that returns the text with its first
   character in upper case and every other character exactly as it was. The
   empty string comes back empty. Two slices.

   ```
   start_capital("deliver to Central Hub") -> "Deliver to Central Hub"
   ```

   *Return: a str.*

3. **Just the digits of a phone number** (P583)

   Phone numbers arrive with spaces, hyphens and brackets. Write a function
   `digits_only(text)` that returns only the digits, in order, as one string.
   A string has a method that says whether it is a digit.

   ```
   digits_only("0115 496-0123") -> "01154960123"
   ```

   *Return: a str.*

4. **The note in brackets** (P584)

   Write a function `in_brackets(text)` that returns what is between the first
   '(' and the ')' that follows it, not including the brackets. If there is no
   '(' the answer is the empty string. find() returns a position, or -1.

   ```
   in_brackets("Parcel 12 (fragile) for Northgate") -> "fragile"
   ```

   *Return: a str.*

5. **A heading, underlined** (P585)

   Write a function `underlined(title)` that returns the title, a newline, and
   then a row of '=' signs exactly as long as the title. A string times a
   number repeats it.

   ```
   underlined("Northgate") -> "Northgate\n========="
   ```

   *Return: a str, with one newline in it (written \n above).*

## 2 - Checks and searches (5)

startswith given a tuple, lower() on both sides of `in`, shape before numbers so
int() cannot raise, a range that counts down, and any() over strip().

6. **Does the code belong to one of our depots?** (P586)

   Write a function `has_prefix(code, prefixes)` that returns True if the code
   starts with ANY of the prefixes in the list. The prefixes are not all the
   same length. startswith accepts several candidates at once, as a tuple.

   ```
   has_prefix("NGT-0042", ["MB", "NGT", "CH"]) -> True
   has_prefix("NG-0042", ["MB", "NGT", "CH"]) -> False
   ```

   *Return: a bool.*

7. **Names that contain the search term** (P587)

   Write a function `matching(names, term)` that returns the names containing
   the search term, in their original order and spelling. Capitals make no
   difference, in the names or in the term.

   ```
   matching(["Yilmaz Bicycles", "Achebe Bakery Direct", "Okonjo BAKERY Ltd"], "bakery") -> ["Achebe Bakery Direct", "Okonjo BAKERY Ltd"]
   ```

   *Return: a list of str.*

8. **Is that really a time?** (P588)

   Write a function `valid_time(text)` that returns True only for a real
   24-hour clock time written 'HH:MM': five characters, a colon in the middle,
   two digits either side, hours 00 to 23 and minutes 00 to 59. Check the
   shape first, the numbers second.

   ```
   valid_time("23:59") -> True
   valid_time("14:65") -> False
   valid_time("9:30") -> False
   ```

   *Return: a bool.*

9. **The last time the parcel was on a van** (P589)

   Write a function `last_position(items, value)` that returns the position,
   counting from 0, of the LAST item equal to value, or -1 if there is none. A
   range can count downwards.

   ```
   last_position(["van", "depot", "van", "door"], "van") -> 2
   ```

   *Return: an int.*

10. **Is any field on the form blank?** (P590)

    Write a function `any_blank(fields)` that returns True if any field in the
    list is blank. A field holding only spaces is as blank as an empty one. An
    empty form has no blank fields. any(), over a test on each field.

    ```
    any_blank(["Rosa Baxter", "  ", "NG7"]) -> True
    ```

    *Return: a bool.*

## 3 - Lists, built and reshaped (5)

range to last + 1, one comprehension per column, `not in` against the list being
built, a filter that says what stays, and a slice that starts at n - 1.

11. **Bay numbers from a range on the rota** (P591)

    The rota gives bays as text: either one number, '4', or a first and a last
    with a hyphen, '3-6'. Write a function `bay_numbers(text)` that returns
    every bay meant, as a list of ints, both ends included.

    ```
    bay_numbers("3-6") -> [3, 4, 5, 6]
    bay_numbers("4") -> [4]
    ```

    *Return: a list of int.*

12. **Codes in one list, postage in another** (P592)

    A batch is a list of [code, cents] pairs. Write a function `unzip(pairs)`
    that returns two LISTS, the codes and the cents, each in the original
    order. An empty batch gives two empty lists.

    ```
    unzip([["MB-2", 410], ["CH-7", 1200]]) -> (["MB-2", "CH-7"], [410, 1200])
    ```

    *Return: a tuple of two lists.*

13. **Two manifests, merged** (P593)

    Write a function `merged(first, second)` that returns one list holding
    every code from both lists exactly once: first's codes in order, then any
    from second not seen yet. A code repeated inside either list still appears
    once.

    ```
    merged(["A-1", "B-2"], ["B-2", "C-3", "A-1", "D-4"]) -> ["A-1", "B-2", "C-3", "D-4"]
    ```

    *Return: a list.*

14. **A status struck from the trail, everywhere** (P594)

    Write a function `without(items, value)` that returns a NEW list with
    every item equal to value left out, and the rest in order. The list passed
    in is not changed.

    ```
    without(["van", "depot", "van", "door"], "van") -> ["depot", "door"]
    ```

    *Return: a list.*

15. **Every third parcel is spot-checked** (P595)

    Write a function `every_nth(items, n)` that returns every nth item,
    starting with the nth itself: for n = 3, the 3rd, 6th, 9th and so on.
    Fewer than n items gives an empty list. A slice takes a start and a step.

    ```
    every_nth(["a", "b", "c", "d", "e", "f", "g"], 3) -> ["c", "f"]
    ```

    *Return: a list.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,891 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
