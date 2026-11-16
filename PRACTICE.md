# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the parcel-courier scheme,
the sixth set on it, at two tools per question with the tiers named by
task, on tools the first five courier sets left out. Nine read the data
and **six change it**, twice as many as before: three single statements
and three procedures of several steps. The prompts name the tool but do
not write the statement. **Fifteen Python** at the easy level of the last
eight sets: everyday tasks over plain lists and strings in the courier's
terms, with no maths and no dicts.

| Stage | SQL questions |
|---|---|
| 1 - Text and patterns | 1-3 |
| 2 - Windows and shares | 4-6 |
| 3 - Rows as values | 7-9 |
| 4 - Changing rows | 10-12 |
| 5 - Procedures | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Finding and counting | 1-5 |
| 2 - Labels and text | 6-10 |
| 3 - Working with lists | 11-15 |

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
UPDATE, an INSERT and a DELETE. 13 to 15 are **procedures**. SQLite has no
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

**Driver statements.** Question 13 issues a `ROLLBACK` *after* your
script. If your work was committed, there is nothing of yours left to
roll back and it stands. If your transaction was left open, everything it
did is undone and the check query shows the data as it was. Question 15 inserts two rows into your view, delivering parcels 40
and 122, which is how the procedure in the trigger gets called. Questions
10, 11, 12 and 14 are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 10 | `UPDATE invoices SET (paid_on, method) = (...) WHERE paid_on IS NULL AND customer_id IN (SELECT ...)` |
| 11 | `INSERT OR IGNORE INTO invoices (...) SELECT ... FROM customers WHERE ...` |
| 12 | `DELETE FROM scans WHERE status = 'failed' AND scan_id NOT IN (SELECT MIN(scan_id) ... GROUP BY parcel_id)` |
| 13 | `BEGIN; UPDATE depots ...; UPDATE couriers ...; UPDATE customers ...; COMMIT;` |
| 14 | `BEGIN; CREATE TABLE lost_parcels AS SELECT ...; DELETE FROM scans ...; DELETE FROM parcels ...; COMMIT;` |
| 15 | `CREATE VIEW deliveries AS ...; CREATE TRIGGER deliver INSTEAD OF INSERT ON deliveries BEGIN UPDATE parcels ...; INSERT INTO scans ...; END` |

## Things the data does on purpose

- **41 customers have a name that ends in Supplies and 64 have one that
  contains it**, the difference being the Garden Supplies businesses that
  question 1's pattern must not catch.
- **The commonest surname among personal customers has 27 holders**, question
  2's top row; business names begin with the family name instead, which is why
  they are left out.
- **106 customers have a postcode area of one letter and a digit**, S1 or S8,
  the ones the first two characters split in question 3; 73 have no area at
  all.
- **Every depot has exactly one first hire**, so question 4 has ten zeros;
  measured from the company's first hire it has one.
- **3 depots have two customers tied as June's biggest sender**, the extra
  rows RANK keeps in question 6.
- **115 parcels have made parcel 1's journey from Docklands to Old Foundry**,
  question 8's total; 85 of the 620 senders have touched all ten depots,
  question 9's last row.
- **38 of the 332 unpaid invoices belong to Old Foundry's customers**, the
  ones question 10 settles; 10 of Northgate's 27 businesses have no invoice
  for May, the ones question 11 adds.
- **72 parcels have a second failed scan**, the rows question 12 deletes out
  of 3,345 parcels with any.
- **4 of Southfield's nine couriers have already left**, and stay on its books
  in question 13 when the other five and its 63 customers move to Millbank.
- **113 of the 271 undelivered parcels are lost**, with 523 scans between
  them, question 14's archive; parcels 40 and 122 are two of them, which
  question 15 delivers.
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
labels, statuses, codes and bay numbers for questions 1 to 5, names,
numbers and postcode areas for 6 to 10, lists of codes and names for 11
to 15.
Each prompt shows one example call with its answer, and Run adds a few
more, including the empty list or the edge the question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Text and patterns (3)

LIKE with the wildcard on one side only, so the word must end the name; INSTR
for where the space is and SUBSTR from one past it; RTRIM with a list of
characters to strip, however many there are.

1. **Businesses whose name ends in Supplies** (Q1297)

   Some businesses trade in 'Garden Supplies' and are called '... Garden
   Supplies Ltd'; others are simply '... Supplies'. For each depot, by name:
   how many of its customers have a name that ENDS with the word Supplies.
   LIKE, with a wildcard on one side only.

   *Return: depot, customers*

2. **The surnames with the most customers** (Q1298)

   A personal customer's name is a first name, one space, and a surname. For
   each surname: how many personal customers carry it. Keep the surnames with
   20 customers or more. INSTR to find the space, SUBSTR to cut.

   *Return: surname, customers*

3. **Customers by postcode town** (Q1299)

   A postcode_area is one or two letters and then digits: NG5, DE22, S1. The
   letters alone name the town. For each town: how many customers, and how
   many of them are businesses. Customers with no postcode_area are a group of
   their own. RTRIM takes a second argument.

   *Return: town, customers, businesses*

## 2 - Windows and shares (3)

FIRST_VALUE with PARTITION BY so each depot has its own first hire, a window
over rows that are already grouped for a share of the grand total, and RANK = 1
where ROW_NUMBER = 1 would pick between equals.

4. **How long after the depot's first hire** (Q1300)

   For every courier: how many days after their depot's FIRST hire they were
   taken on, as a whole number -- 0 for the first hire itself. Couriers who
   have left count like anyone else. FIRST_VALUE over a window per depot, and
   julianday for the gap.

   *Return: courier, depot, days_after_first*

5. **Each region's share of the postage** (Q1301)

   For each region -- the region of the depot where a parcel was collected:
   its parcels, and its share of ALL postage as a percentage to one decimal
   place. The grand total can sit beside the grouped rows: a window function
   over the whole result, its OVER left empty.

   *Return: region, parcels, pct_of_postage*

6. **June's biggest sender at each depot, ties included** (Q1302)

   For each depot: the customer who sent the most parcels collected in June
   2026, the depot being the customer's HOME depot. Where two customers tie
   for first, list both. RANK, partitioned, in a subquery so its result can be
   filtered.

   *Return: depot, customer, parcels*

## 3 - Rows as values (3)

VALUES as a table written on the spot and named by a CTE, two columns compared
as one row with a two-column subquery, and UNION, which drops the duplicates
UNION ALL keeps.

7. **How much of the postage is the weight surcharge** (Q1303)

   Postage is a base price for the service plus a surcharge for weight. The
   base prices are in no table: economy 350, standard 500, express 900 cents.
   For each service: its parcels, and the surcharge collected in total --
   postage above the base. Write the price list as an inline table with
   VALUES, named in a CTE, and join to it.

   *Return: service, parcels, surcharge_cents*

8. **Every parcel on parcel 1's route** (Q1304)

   Parcel 1 went from one depot to another. For each service: how many parcels
   have made exactly that journey -- the same origin AND the same destination,
   parcel 1 included. Compare the two columns as ONE row value with a subquery
   that returns two columns.

   *Return: service, parcels*

9. **How many depots a customer's post has touched** (Q1305)

   A parcel touches two depots, where it was collected and where it was
   delivered to. For each customer, count the DIFFERENT depots their parcels
   have touched at either end; then say how many customers there are for each
   count. Walk-ins are left out. Two lists of (customer, depot) stacked by the
   set operator that drops duplicates.

   *Return: depots_touched, customers*

## 4 - Changing rows (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. One statement each: SET (a, b) = (x, y)
where a CHECK ties two columns together, INSERT OR IGNORE against a UNIQUE
constraint, and a DELETE that keeps MIN(id) per group.

10. **Old Foundry's debts, settled** (Q1306)

    The customers of the closed depot have settled up. Mark every UNPAID
    invoice of a customer whose home depot is Old Foundry as paid on
    2026-07-01 by transfer. The table's CHECK refuses an invoice that has only
    one of paid_on and method, so both are set in ONE UPDATE; which customers
    is a subquery's business.

    *Checked: invoices and cents for each method, the unpaid included*

11. **A minimum charge for the quiet accounts** (Q1307)

    Every business customer whose home depot is Northgate (depot 3) must have
    an invoice for period 2026-05. Those without one get a minimum charge: 500
    cents, issued 2026-06-01, not yet paid. Those who already have one keep it
    exactly as it is. One INSERT ... SELECT that offers a row for every such
    business and lets the table's UNIQUE (customer_id, period) turn away the
    ones already there: INSERT has a conflict clause for that.

    *Checked: the invoices for 2026-05: how many, their cents added up, how many unpaid*

12. **One failed attempt per parcel is enough** (Q1308)

    Some parcels have two 'failed' scans. For each parcel keep the failed scan
    with the lowest scan_id and delete its other failed scans. Scans of every
    other status stay. A DELETE whose WHERE holds a grouped subquery: the ids
    to keep.

    *Checked: scans left, and how many of them are failures*

## 5 - Procedures (3)

Writable questions of several steps. SQLite has no CREATE PROCEDURE: a
transaction makes steps stand or fall together, the order of the steps is the
procedure, and an INSTEAD OF trigger on a view is a stored body you call with
INSERT.

13. **Closing Southfield, all or nothing** (Q1309)

    SQLite has no stored procedures; the nearest thing is a script whose steps
    stand or fall together. Southfield (depot 7) closes on 2026-07-01. In ONE
    transaction: record the closing date on the depot; move its couriers who
    are still employed to Millbank (depot 8); move every customer whose home
    depot it is to Millbank. Couriers who have already left stay on
    Southfield's books. The question then issues a ROLLBACK: committed work
    survives it, work left in an open transaction does not.

    *Checked: Southfield's closing date, couriers still listed there, couriers at Millbank, customers at Millbank*

14. **Lost parcels, archived and then removed** (Q1310)

    A parcel is LOST when it was never delivered and has a 'failed' scan.
    Write the procedure that clears the lost parcels out, as one transaction,
    in an order that works: create a table lost_parcels holding the parcel_id,
    customer_id and postage_cents of every lost parcel (CREATE TABLE ... AS);
    delete those parcels' scans; delete the parcels. Foreign keys are on, so a
    parcel that still has scans cannot be deleted -- and once its scans are
    gone, they can no longer say it was lost.

    *Checked: rows in lost_parcels and their postage added up, parcels left, scans left*

15. **A delivery procedure you call with INSERT** (Q1311)

    A trigger body is the one place SQLite stores a procedure. Create a view
    deliveries showing the parcel_id, courier_id and delivered_at of every
    delivered parcel, and an INSTEAD OF INSERT trigger on it that does two
    things with the row it is offered: records the courier and the time on
    that parcel, and adds a 'delivered' scan for it at the parcel's
    DESTINATION depot, with the same courier and time. The question then
    delivers two lost parcels, 40 and 122, by inserting into the view.

    *Checked: for parcels 40 and 122: the courier, the delivery time, and the depot and status of any scan dated July*

# Python

## 1 - Finding and counting (5)

max with key=len or key=list.count and a default for the empty case, zip of a
list with itself one step along, a while loop past everything taken, and zip of
two lists to compare position by position.

1. **The longest word on the label** (P566)

   Write a function `longest_word(label)` that returns the longest word in a
   label, the words being whatever split() gives. If several are equally long,
   the first of them; if the label has no words, the empty string. max() takes
   a key, and a default.

   ```
   longest_word("Yilmaz Garden Supplies Ltd") -> "Supplies"
   ```

   *Return: a str.*

2. **How often the status changed** (P567)

   Write a function `count_changes(statuses)` that returns how many times an
   item differs from the one just before it. zip the list with itself, one
   step along.

   ```
   count_changes(["depot", "depot", "van", "van", "depot", "door"]) -> 3
   ```

   *Return: an int.*

3. **The code scanned most often** (P568)

   Write a function `most_scanned(codes)` that returns the code that appears
   most often in the list. On a tie, the one that appears FIRST in the list;
   for an empty list, None. max() again, with the list's own count method as
   the key.

   ```
   most_scanned(["MB-2", "CH-7", "MB-2", "WW-1", "CH-7", "MB-2"]) -> "MB-2"
   ```

   *Return: a str, or None.*

4. **The lowest free loading bay** (P569)

   Bays are numbered from 1. Write a function `first_free(taken)` that returns
   the lowest bay number that is not in the list. The list is in no particular
   order. A while loop that counts up until `not in`.

   ```
   first_free([1, 2, 4, 5]) -> 3
   ```

   *Return: an int.*

5. **How much of the manifest matches the van** (P570)

   Write a function `matches(manifest, loaded)` that returns how many
   POSITIONS hold the same code in both lists: first against first, second
   against second. If one list is longer, its extra items match nothing.

   ```
   matches(["A-1", "B-2", "C-3", "D-4"], ["A-1", "C-3", "B-2", "D-4"]) -> 2
   ```

   *Return: an int.*

## 2 - Labels and text (5)

A slice three short to leave room for the dots, the exception tested before the
rule, enumerate told to start at 1, split() then word[0] then one upper(), and
rstrip with the characters to remove.

6. **A line cut to fit the label** (P571)

   Write a function `fit(text, width)` for a label `width` characters wide.
   Text that fits is returned unchanged. Text that is too long is cut and
   ended with three dots, so that the result is EXACTLY width characters, dots
   included. width is always 3 or more.

   ```
   fit("Okonjo Garden Supplies & Sons", 16) -> "Okonjo Garden..."
   ```

   *Return: a str.*

7. **1st, 2nd, 3rd, 4th** (P572)

   Write a function `ordinal(n)` that returns a positive whole number with its
   ending: 1st, 2nd, 3rd, then th. The last digit decides -- 21st, 32nd, 103rd
   -- except that anything ending in 11, 12 or 13 takes th.

   ```
   ordinal(22) -> "22nd"
   ordinal(12) -> "12th"
   ```

   *Return: a str.*

8. **The steps of a delivery, numbered** (P573)

   Write a function `numbered(steps)` that returns a new list with each step's
   number in front of it, counting from 1, then a full stop and a space.
   enumerate can be told where to start.

   ```
   numbered(["Collect", "Sort", "Deliver"]) -> ["1. Collect", "2. Sort", "3. Deliver"]
   ```

   *Return: a list of str.*

9. **A depot's initials** (P574)

   Write a function `initials(name)` that returns the first letter of each
   word, joined together and in capitals, whatever case the name was typed in.
   Extra spaces between words do not matter.

   ```
   initials("Central Hub") -> "CH"
   initials("old foundry") -> "OF"
   ```

   *Return: a str.*

10. **The letters of a postcode area** (P575)

    A postcode area is one or two letters and then digits. Write a function
    `town(area)` that returns the letters alone. rstrip takes an argument: the
    characters to strip.

    ```
    town("DE22") -> "DE"
    town("S1") -> "S"
    ```

    *Return: a str.*

## 3 - Working with lists (5)

zip and then the slices past the shorter length, a conditional expression at the
front of a comprehension, % len to wrap round, sorted with key=str.lower, and
sorted on both sides of ==.

11. **Two loads, taken turn about** (P576)

    Write a function `interleave(first, second)` that returns one list taking
    items from the two in turn: first's first, second's first, first's second,
    and so on. When one list runs out, the rest of the other follows in order.

    ```
    interleave(["A-1", "A-2", "A-3", "A-4"], ["B-1"]) -> ["A-1", "B-1", "A-2", "A-3", "A-4"]
    ```

    *Return: a list.*

12. **A relabelled parcel, corrected everywhere** (P577)

    Write a function `relabel(codes, old, new)` that returns a NEW list in
    which every item equal to old has become new, and everything else is as it
    was. The list passed in is not changed. A comprehension with a conditional
    expression.

    ```
    relabel(["MB-2", "CH-7", "MB-2", "WW-1"], "MB-2", "MB-9") -> ["MB-9", "CH-7", "MB-9", "WW-1"]
    ```

    *Return: a list.*

13. **Who is next on the rota** (P578)

    The rota is a list of names, each appearing once, and it goes round: after
    the last name comes the first again. Write a function `next_up(rota,
    name)` that returns the name after the given one. name is always on the
    rota. index(), and the remainder operator to wrap.

    ```
    next_up(["Grace", "Samir", "Nadia"], "Nadia") -> "Grace"
    ```

    *Return: a str.*

14. **Names in order, whatever their capitals** (P579)

    Write a function `in_order(names)` that returns the names in alphabetical
    order as a reader would expect it, taking no notice of capital letters.
    Each name comes back spelled exactly as it went in. sorted() with a key.

    ```
    in_order(["westway", "Central Hub", "Millbank", "docklands"]) -> ["Central Hub", "docklands", "Millbank", "westway"]
    ```

    *Return: a list of str.*

15. **Do the two vans carry the same load?** (P580)

    Write a function `same_load(van_a, van_b)` that returns True if the two
    lists hold the same codes the same number of times, in any order. A code
    that is on one van twice must be on the other twice.

    ```
    same_load(["A-1", "B-2", "A-1"], ["B-2", "A-1", "A-1"]) -> True
    same_load(["A-1", "B-2", "A-1"], ["A-1", "B-2", "B-2"]) -> False
    ```

    *Return: a bool.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,861 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
