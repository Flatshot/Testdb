# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the parcel-courier scheme,
the eighth set on it, at two tools per question with the tiers named by
task, on tools the first seven courier sets left out. Nine read the data
and **six change it**: three single statements and three procedures of
several steps. The prompts name the tool but do not write the statement.
**Fifteen Python** at the easy level of the last ten sets: everyday
tasks over plain lists and strings in the courier's terms, with no maths
and no dicts.

| Stage | SQL questions |
|---|---|
| 1 - Text, matched and built | 1-3 |
| 2 - More from windows | 4-6 |
| 3 - Positions, years and thresholds | 7-9 |
| 4 - Changing rows | 10-12 |
| 5 - Procedures | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Text checks and fixes | 1-5 |
| 2 - Safe values and labels | 6-10 |
| 3 - Lists, split and combined | 11-15 |

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

**Driver statements.** Question 13 tries three inserts into your
rebuilt table: an invoice paid before it was issued, which the new CHECK
must refuse; a valid one, which must get in; and a second invoice for a
customer and period already there, which the old UNIQUE must still
refuse. Question 14 issues a `ROLLBACK`: committed work stands, and a
transaction left open is undone. Question 15 deletes parcels 40 and 122,
which is what fires the trigger. Questions 10 to 12 are graded on what
your script leaves behind.

**The definition of a table** is in `schema.sql`. Question 13 needs the
whole of the `invoices` one.

| # | Construct |
|---|---|
| 10 | `INSERT INTO couriers (name, depot_id, vehicle, hired_on) VALUES ('...', (SELECT depot_id FROM depots WHERE name = '...'), ...), (...)` |
| 11 | `UPDATE depots SET bays = 4 * (SELECT COUNT(*) FROM couriers c WHERE c.depot_id = depots.depot_id AND c.left_on IS NULL) WHERE closed_on IS NULL` |
| 12 | `DELETE FROM scans WHERE status NOT IN ('collected', 'delivered') AND parcel_id IN (SELECT parcel_id FROM parcels WHERE delivered_at < '...')` |
| 13 | `BEGIN; CREATE TABLE invoices_new (... CHECK (paid_on >= issued_on)); INSERT INTO invoices_new SELECT * FROM invoices; DROP TABLE invoices; ALTER TABLE invoices_new RENAME TO invoices; COMMIT;` |
| 14 | `BEGIN; INSERT INTO depots (...) VALUES (...); UPDATE couriers SET depot_id = last_insert_rowid() WHERE ...; UPDATE customers SET depot_id = last_insert_rowid() WHERE ...; COMMIT;` |
| 15 | `CREATE TABLE removed (...); CREATE TRIGGER ... BEFORE DELETE ON parcels BEGIN INSERT INTO removed SELECT OLD.parcel_id, COUNT(*) FROM scans ...; DELETE FROM scans ...; END` |

## Things the data does on purpose

- **46 personal customers have a first name of four letters**, three names
  between them, question 1's rows; 42 customers have a postcode area ending in
  two digits, all of them DE22, question 2's total.
- **76 invoices for May 2026 are unpaid**, the references question 3 builds,
  for customer ids from one digit to three.
- **7 months set a record, though 9 improved on the month before**, the
  difference between question 4's frame and a plain LAG.
- **June 2025 had 1,202 parcels and June 2026 1,523**, question 5's last row;
  every one of the eighteen months has parcels, which is what lets an offset
  of twelve mean a year.
- **235 customers share their name with another, but only 20 with one at their
  own depot**, question 6's partition.
- **The fourth-busiest courier has delivered 643 parcels**, where question 7
  starts; no two of the top ten are tied.
- **4 of the 45 current couriers have not reached their first anniversary**,
  question 8's zero row, which a plain difference of years cannot produce.
- **613 customers have sent ten parcels or more and 25 a hundred or more**,
  the ends of question 9's table.
- **Central Hub has 48 bays and 2 couriers**, so question 11 cuts it to eight;
  3,083 parcels were delivered before April 2025, with 8,251 scans between
  their first and last, the ones question 12 deletes.
- **No invoice in the data was paid before it was issued**, so question 13's
  new CHECK has nothing to object to in the existing rows.
- **Docklands has 2 lorry drivers and 16 customers with an LE postcode, out of
  126 in the company**, the moves in question 14; parcels 40 and 122 are lost
  parcels with five and three scans, question 15's deletes.
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
codes, addresses and names for questions 1 to 5, form fields, numbers
and days for 6 to 10, lists of codes, stops and numbers for 11 to 15.
Each prompt shows one example call with its answer, and Run adds a few
more, including the empty list or the edge the question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Text, matched and built (3)

An underscore in LIKE for exactly one character, GLOB's [0-9] for one character
out of a set with * for the rest, and printf('%05d') to pad a number before ||
joins it into a reference.

1. **First names of exactly four letters** (Q1327)

   A personal customer's name is a first name, one space, and a surname. For
   each first name of exactly FOUR letters: how many personal customers have
   it. In a LIKE pattern % is any run of characters; there is a second
   wildcard that stands for exactly one.

   *Return: first_name, customers*

2. **Postcode areas that end in two digits** (Q1328)

   For each depot, by name: how many of its customers have a postcode_area
   that ENDS IN TWO DIGITS, like DE22. LIKE has no way to say 'a digit'. GLOB
   has: a character class in square brackets. Its wildcard for 'anything' is *
   and not %.

   *Return: depot, customers*

3. **A reference number for the reminder letters** (Q1329)

   Every UNPAID invoice for period 2026-05 needs a reference: 'INV-', the
   period, a hyphen, and the customer_id padded with zeros to FIVE digits --
   INV-2026-05-00004 for customer 4. printf pads a number; || joins the
   pieces.

   *Return: reference, amount_cents*

## 2 - More from windows (3)

A frame that ends at 1 PRECEDING so MAX is the best BEFORE this row, LAG with an
offset of twelve for the same month last year, and COUNT(*) OVER (PARTITION BY
name) to see a group's size without collapsing it.

4. **The months that set a record** (Q1330)

   A record month is one in which more parcels were collected than in ANY
   earlier month. List the record months, each with the best figure it had to
   beat. The first month of the data has nothing to beat and is not listed. A
   window MAX whose frame stops one row BEFORE the current one.

   *Return: month, parcels, previous_best*

5. **This month against the same month last year** (Q1331)

   For each month that has one: the parcels collected, and the parcels
   collected in the SAME month a year earlier. Months with no such earlier
   month are not listed. No month is missing from the data. LAG takes a second
   argument.

   *Return: month, parcels, a_year_earlier*

6. **Customers who share their name with another** (Q1332)

   Some customers have exactly the same name as another customer, anywhere in
   the company. For each depot, by name: how many of its customers have such a
   namesake. A window COUNT partitioned by name puts the size of each name's
   group on every row, without collapsing the rows.

   *Return: depot, customers*

## 3 - Positions, years and thresholds (3)

OFFSET as the number of rows to skip, a year difference less one where the
anniversary has not come, and a join on >= so one row can match several levels.

7. **Fourth, fifth and sixth place** (Q1333)

   Rank the couriers by parcels delivered, most first. Return the three in
   4th, 5th and 6th place. No two of the top ten are tied. LIMIT has a partner
   that skips rows first.

   *Return: courier, deliveries*

8. **Completed years of service** (Q1334)

   For couriers still employed: their COMPLETED years of service on
   2026-06-30, counted the way a birthday is -- a year counts only once its
   anniversary has come -- and how many couriers have each number. Subtracting
   the years is one too many for anyone whose anniversary falls later in the
   year; comparing the 'MM-DD' parts as text says who.

   *Return: years, couriers*

9. **How many customers reach each level** (Q1335)

   How many customers have sent AT LEAST 10 parcels? At least 15, 20, 25, 30,
   100? One row per level; a customer with 40 parcels is counted at five of
   them. Walk-ins are left out. A join does not have to be on equality: put
   the six levels in an inline table and join on >=.

   *Return: at_least, customers*

## 4 - Changing rows (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. One statement each: VALUES with two
rows and a scalar subquery for the foreign key, a correlated subquery in SET,
and NOT IN where OR would be true of everything.

10. **Two new starters at Hillcrest** (Q1336)

    Two couriers start at the Hillcrest depot on 2026-07-01: Ada Whitlock on a
    bike and Tom Reyes in a van. Add them in ONE INSERT with two rows. The
    depot is known by its name, so its id is looked up, not typed: a subquery
    in brackets can stand wherever a value can.

    *Checked: name, depot name, vehicle, hiring and leaving dates of every courier hired from July 2026 on*

11. **Bays to match the people** (Q1337)

    The bays are re-planned: every depot still open is to have FOUR bays for
    each courier currently working there, no more and no fewer. The closed
    depot keeps what it has. One UPDATE; the SET holds a subquery that counts
    the couriers of the depot being updated.

    *Checked: every depot's name and bays*

12. **Old trails, thinned to their two ends** (Q1338)

    Trails of old parcels are thinned to save space. For every parcel
    DELIVERED before 2025-04-01, delete the scans that are neither its
    'collected' scan nor its 'delivered' scan. Every other parcel keeps its
    whole trail. Take care how 'neither ... nor' is written: NOT IN says it
    safely.

    *Checked: scans left, for each status*

## 5 - Procedures (3)

Writable questions of several steps. SQLite has no CREATE PROCEDURE: a
transaction makes steps stand or fall together, the order of the steps is the
procedure, and a trigger body is a procedure the database runs for you.

13. **A new rule for a table that already exists** (Q1339)

    New rule: an invoice cannot be paid before it was issued. SQLite's ALTER
    TABLE cannot add a CHECK to an existing table, so the table is rebuilt, in
    one transaction, by the standard procedure: create invoices_new with
    everything invoices has PLUS the new CHECK; copy every row across; drop
    invoices; rename invoices_new to invoices. The present definition is in
    schema.sql -- start from it, so that no existing rule is lost. The
    question then tries three inserts: one paid before it was issued, one that
    is fine, and one repeating a customer and period already there.

    *Checked: invoices in the table, how many are for 2026-06, and the cents added up*

14. **Riverside opens, with staff and customers** (Q1340)

    A new depot, Riverside, opens in the east region on 2026-07-01 with 12
    bays. In ONE transaction: add the depot; move the lorry drivers of
    Docklands (depot 5) to it; move to it every Docklands customer whose
    postcode_area begins LE. The new depot's id is whatever the table gives it
    -- do not assume a number: last_insert_rowid() reports the id of the row
    an INSERT has just made. The question then issues a ROLLBACK: committed
    work survives it.

    *Checked: for Docklands and Riverside: region, bays, couriers listed, customers listed*

15. **A parcel that takes its trail with it** (Q1341)

    Deleting a parcel is refused while it has scans: the foreign key protects
    the trail. Store the procedure that makes it possible. Create a table
    removed with parcel_id as its primary key and a required whole number
    scans_removed, and a BEFORE DELETE trigger on parcels whose body does two
    things for the parcel about to go: records in removed how many scans it
    has, and deletes those scans. The question then deletes parcels 40 and
    122.

    *Checked: each row of removed, with the parcels and scans left in the database*

# Python

## 1 - Text checks and fixes (5)

strip() and lower() on both sides of ==, isdigit() before int(), a slice of
len(ending) where rstrip would strip characters, stars times len - 4, and
lower() before count().

1. **The same code, typed two ways** (P596)

   Write a function `same_code(a, b)` that returns True if the two codes are
   the same once spaces at either end are removed and capitals are ignored.
   Spaces INSIDE a code still count as a difference.

   ```
   same_code("MB-0012", " mb-0012 ") -> True
   same_code("MB-12", "MB -12") -> False
   ```

   *Return: a bool.*

2. **The house number at the start of an address** (P597)

   Write a function `house_number(address)` that returns the house number as
   an int when the FIRST word of the address is made of digits only, and None
   otherwise.

   ```
   house_number("12 High Street") -> 12
   house_number("Flat 3, 12 High Street") -> None
   ```

   *Return: an int, or None.*

3. **A company name without its ending** (P598)

   Write a function `without_ending(name, endings)` that returns the name with
   its ending cut off, if it ends with one of the endings in the list, and
   unchanged if it ends with none of them. Each ending in the list begins with
   a space.

   ```
   without_ending("Okonjo Books Ltd", [" Ltd", " & Co", " & Sons"]) -> "Okonjo Books"
   ```

   *Return: a str.*

4. **An account number with its last four showing** (P599)

   Write a function `masked(number)` that returns the string with every
   character except the last four replaced by a star. The result is the same
   length as the original; a string of four characters or fewer comes back
   unchanged.

   ```
   masked("12345678") -> "****5678"
   ```

   *Return: a str.*

5. **How many times a letter appears** (P600)

   Write a function `count_letter(text, letter)` that returns how many times
   the letter appears in the text, counting capitals and small letters as the
   same, whichever way the letter itself was given.

   ```
   count_letter("Bartholomew Baxter", "b") -> 2
   ```

   *Return: an int.*

## 2 - Safe values and labels (5)

strip then isdigit then int, min inside max, a comma after the colon in an
f-string, :02d over a range, and one normal form before `in`.

6. **A quantity typed into a form** (P601)

   Write a function `quantity(text)` that returns the whole number typed into
   a form field, ignoring spaces around it, or 0 if what was typed is not made
   of digits only. Nothing here should ever raise an error.

   ```
   quantity(" 12 ") -> 12
   quantity("abc") -> 0
   ```

   *Return: an int.*

7. **A bay number kept within the depot** (P602)

   Write a function `within(n, low, high)` that returns n if it lies between
   low and high, low if it is below, and high if it is above. low is never
   greater than high. min() and max(), one inside the other.

   ```
   within(15, 1, 10) -> 10
   within(0, 1, 10) -> 1
   ```

   *Return: an int.*

8. **A parcel count with commas** (P603)

   Write a function `count_label(n)` that returns the number with commas
   between the thousands, a space, and the word parcel -- or parcels for
   anything but exactly 1. An f-string's format can put the commas in.

   ```
   count_label(24000) -> "24,000 parcels"
   count_label(1) -> "1 parcel"
   ```

   *Return: a str.*

9. **Delivery slots, on the hour** (P604)

   Write a function `slots(first, last)` that returns the start time of every
   one-hour delivery slot from the hour `first` up to but not including the
   hour `last`, as 'HH:00' strings with two digits for the hour.

   ```
   slots(9, 12) -> ["09:00", "10:00", "11:00"]
   ```

   *Return: a list of str.*

10. **Is it the weekend?** (P605)

    A day arrives as its full name or its first three letters, in any mix of
    capitals, perhaps with spaces around it. Write a function
    `is_weekend(day)` that returns True for Saturday and Sunday. Reduce every
    way of writing a day to one form, then test with `in`.

    ```
    is_weekend("Saturday") -> True
    is_weekend(" Sat ") -> True
    is_weekend("MONDAY") -> False
    ```

    *Return: a bool.*

## 3 - Lists, split and combined (5)

range with a step and a slice to i + n, (len + 1) // 2, insert at index + 1,
all() where any() would let one bad item through, and rjust to the widest.

11. **Parcels shelved so many to a shelf** (P606)

    Write a function `shelves(items, n)` that returns the items as a list of
    lists, n to a shelf in order, with whatever is left over on a last,
    shorter shelf. No items means no shelves. range takes a step.

    ```
    shelves(["a", "b", "c", "d", "e", "f", "g"], 3) -> [["a", "b", "c"], ["d", "e", "f"], ["g"]]
    ```

    *Return: a list of lists.*

12. **One load between two vans** (P607)

    Write a function `halves(items)` that splits the list into a first half
    and a second half, in order, and returns the two lists. When the number of
    items is odd, the FIRST half gets the extra one.

    ```
    halves(["a", "b", "c", "d", "e"]) -> (["a", "b", "c"], ["d", "e"])
    ```

    *Return: a tuple of two lists.*

13. **An extra stop, straight after another** (P608)

    Write a function `insert_after(stops, stop, new)` that returns a NEW list
    with `new` placed immediately after the first occurrence of `stop`. If
    `stop` is not in the list, the result is an unchanged copy. The list
    passed in is not altered.

    ```
    insert_after(["Northgate", "Moorside", "Westway"], "Moorside", "Hillcrest") -> ["Northgate", "Moorside", "Hillcrest", "Westway"]
    ```

    *Return: a list.*

14. **Is every status one we know?** (P609)

    Write a function `all_known(statuses, allowed)` that returns True if EVERY
    status in the first list appears in the list of allowed ones. A trail with
    no statuses has nothing wrong with it.

    ```
    all_known(["collected", "lost"], ["collected", "departed", "arrived", "delivered"]) -> False
    ```

    *Return: a bool.*

15. **Numbers lined up on the right** (P610)

    Write a function `lined_up(numbers)` that returns the numbers as strings,
    all the same length -- as wide as the longest -- with spaces added on the
    LEFT so that the last digits line up in a column. An empty list gives an
    empty list.

    ```
    lined_up([5, 120, 34]) -> ["  5", "120", " 34"]
    ```

    *Return: a list of str.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,921 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
