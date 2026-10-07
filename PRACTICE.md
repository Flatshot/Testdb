# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
third set on this schema and the second with the topics mixed up -- six
tiers that neither library set before it used -- and **fifteen Python**:
tiny functions of one or two lines, each about ONE tool named in the
question's title, none of them used by an earlier set.

| Stage | SQL questions |
|---|---|
| 1 - Subqueries | 1-2 |
| 2 - String aggregation and DISTINCT | 3-4 |
| 3 - Outer joins and NULL tests | 5-7 |
| 4 - Window frames | 8-10 |
| 5 - Ordering and limits | 11-12 |
| 6 - Constraints | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Strings | 1-5 |
| 2 - Numbers | 6-9 |
| 3 - Sets and sequences | 10-13 |
| 4 - Dictionaries | 14-15 |

## The schema

Nine tables. `books` are titles; `copies` are the physical things, each at a
`branch`, in some condition, perhaps withdrawn. `loans` is the centre: a copy,
a member, `loaned_on`, a `due_on` that already includes any renewals, and a
`returned_on` that is NULL while the book is still out. `holds` is a queue --
members waiting for a book, ordered by `placed_at`, each ending in a
fulfilment, a cancellation, or neither yet. `fines` hang off loans: a late
return costs 20p a day, capped, paid or not. `members` have a home branch and
`copies` have a branch, two foreign keys to the same table. `staff` work at a
branch; `authors` wrote the books. Double-click a table in the left pane to
see its columns.

**Dates are text**, 'YYYY-MM-DD', and `holds.placed_at` is a datetime,
'YYYY-MM-DD HH:MM'. They compare correctly as text; `julianday()` turns
either into a number of days you can subtract, and `date()` cuts a datetime
to its day.

**The data ends at 2026-06-30.** Anything that would have ended after that is
open instead -- 685 loans have no return date, 118 of them already
past due; 337 holds are still waiting; 1,380 fines are unpaid.

## The writable stage

SQLite has no stored procedures, variables, loops or TRY/CATCH. What it has
instead is constraints, triggers, views, DDL and plain DML -- and each of
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

**Driver statements.** Questions 13 and 14 run inserts of their own *after*
your script -- the bookings your CHECKs should sort, the holds your index
should sort. Question 15 is graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE TABLE` with a CHECK on one column and a CHECK comparing two |
| 14 | `CREATE UNIQUE INDEX ... WHERE`: a partial index, where the unconditional one cannot be built |
| 15 | `INSERT ... ON CONFLICT(name) DO UPDATE SET ... = excluded....` |

## Things the data does on purpose

- **The average borrower has 18.4 loans; the average member has
  16.0**, because 200 members have none. Question 2 wants the
  first, and 170 borrowers are above it.
- **100 authors have three or more books, and 11 have none**
  -- question 3's groups and question 6's anti-join.
- **27 of Old Town's members have no loan since 2026-01-01**,
  the rows question 5 keeps only when the date test is in ON.
- **109 members have no recorded postcode area**, the rows that `<>`
  loses in question 7.
- **441 member names are shared**, which is why question 11's page
  needs member_id as a tie-break; and the tenth and eleventh most overdue
  loans share a due date, which is why question 12's does.
- **8 members have held the same book twice** in the history, so
  question 14's unconditional UNIQUE index cannot even be created.
- **Copies, staff and members all point at branch 6**, so question 15's
  INSERT OR REPLACE, which deletes before it inserts, fails on a foreign
  key.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Each question here is one or two lines about one tool,
named in its title.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Subqueries (2)

A scalar subquery as a denominator, where the arithmetic around it has to be
made floating-point, and a derived table in FROM so that per-member counts exist
as rows before they are averaged.

1. **Each branch's share of the stock** (Q877)

   For each branch: how many copies it holds, and what percentage of ALL
   copies that is, to one decimal. The total is a scalar subquery -- (SELECT
   COUNT(*) FROM copies) -- used inside the outer query's arithmetic.

   *Return: branch_id, copies, pct*

2. **Above the average borrower** (Q878)

   Members who have borrowed more often than the AVERAGE BORROWER -- the
   average of loans per member over the members who have at least one loan,
   not over all 1,500 members. Build the per-member counts once as a derived
   table in FROM, and take the average of that.

   *Return: member_id, loans*

## 2 - String aggregation and DISTINCT (2)

GROUP_CONCAT with the ORDER BY inside its parentheses, and COUNT(DISTINCT)
beside a COUNT that is COUNT(*) under another name.

3. **An author's titles on one line** (Q879)

   For each author with three or more books in the catalogue: author_id and
   their titles joined into ONE string with '; ' between them, in alphabetical
   order of title. GROUP_CONCAT takes an ORDER BY inside its parentheses.

   *Return: author_id, titles*

4. **Loans and readers, per genre** (Q880)

   For each genre: how many loans its books have had, and how many DIFFERENT
   members made them. A member who borrowed ten children's books is ten loans
   and one reader.

   *Return: genre, loans, readers*

## 3 - Outer joins and NULL tests (3)

A date test that belongs in ON rather than WHERE, an anti-join that needs the
right table on the left, and IS NOT where <> loses every NULL.

5. **Every member of Old Town, borrowing or not** (Q881)

   For EVERY member whose home branch is 6: member_id and how many loans they
   have taken out since 2026-01-01 -- 0 for the members with none, who must
   still appear. The date test belongs in the join's ON clause, not in WHERE.

   *Return: member_id, loans_2026*

6. **Authors with nothing in the catalogue** (Q882)

   Authors who have no books at all, found with a LEFT JOIN and a test for
   NULL on the books side -- an anti-join -- rather than NOT IN or NOT EXISTS.

   *Return: author_id, name*

7. **Everyone outside LS1** (Q883)

   For each home branch, how many of its members do NOT live in postcode area
   'LS1' -- counting the members with no recorded area among them, since they
   are not in LS1 either.

   *Return: home_branch_id, members*

## 4 - Window frames (3)

SUM(SUM()) OVER (ORDER BY) for a running total, LAG against LEAD, and ROWS
BETWEEN 2 PRECEDING AND CURRENT ROW against the default frame.

8. **Fines issued in 2026, running total** (Q884)

   For each month of 2026 in the data: the pence of fines issued that month,
   and the running total from January up to and including that month. A window
   SUM over the monthly SUM, ordered by month.

   *Return: month, pence, cumulative*

9. **Loans month on month** (Q885)

   For each month of the data: how many loans started, and the change from the
   previous month -- this month minus last, NULL for the first month. LAG
   looks back one row.

   *Return: month, loans, change*

10. **A three-month moving average** (Q886)

    For each month of the data: the average number of loans started over that
    month and the two before it, to one decimal -- so the first month averages
    itself alone and the second averages two. The frame is ROWS BETWEEN 2
    PRECEDING AND CURRENT ROW.

    *Return: month, moving_avg*

## 5 - Ordering and limits (2)

OFFSET counts rows to skip, and a top ten is only right in the right direction
with a tie-break on the boundary.

11. **The third page of members** (Q887)

    The member list is shown twenty to a page, sorted by name and, where two
    members share a name, by member_id. Return the THIRD page -- rows 41 to 60
    of that ordering.

    *Return: member_id, name*

12. **The ten most overdue loans** (Q888)

    As of 2026-06-30, the ten loans that are still out and furthest past their
    due date: the earliest due_on first, ties broken by the lower loan_id.
    Only loans with returned_on NULL and due_on before that day count.

    *Return: loan_id, due_on*

## 6 - Constraints (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A table with a column CHECK and a table
CHECK, a partial UNIQUE index, and an UPSERT where OR REPLACE would break a
foreign key.

13. **A room-booking table that checks itself** (Q889)

    Create a table `room_bookings (booking_id INTEGER PRIMARY KEY, member_id
    INTEGER NOT NULL REFERENCES members(member_id), room TEXT NOT NULL,
    starts_at TEXT NOT NULL, ends_at TEXT NOT NULL)` with two CHECKs: room is
    'study' or 'meeting', and ends_at is after starts_at. The question then
    tries three bookings: a good one, one in room 'garden', and one that ends
    before it starts.

    *Checked: how many bookings exist*

14. **One open hold per member per book** (Q890)

    Create a UNIQUE index that stops a member holding more than ONE open hold
    -- fulfilled_on and cancelled_on both NULL -- on the same book, while
    leaving their closed holds alone: a PARTIAL index, with a WHERE. The
    question then inserts a second open hold for member 844 on book 275, who
    already has one waiting, and an open hold for member 842 on book 349,
    whose earlier hold was fulfilled.

    *Checked: how many holds exist, and how many open holds member 842 has on book 349*

15. **Add or update a branch in one statement** (Q891)

    Record two branches so that the script works whether or not the name
    exists: 'Old Town' in 'Castleford', and 'Westgate' in 'Leeds', both
    opened_on '2026-09-01'. Where a branch of that name already exists, UPDATE
    its town and leave its branch_id alone; otherwise insert it. Use INSERT
    ... ON CONFLICT(name) DO UPDATE -- not INSERT OR REPLACE.

    *Checked: every branch's branch_id, name and town*

# Python

## 1 - Strings (5)

rstrip(chars) against rstrip(), swapcase() against upper(), removeprefix()
against lstrip(), rfind() against find(), and casefold() against ==.

1. **rstrip(chars): trailing punctuation off** (P146)

   Write a function `no_trailing_punctuation(s)` that returns s with any run
   of '.', ',', '!' or '?' removed from its END only, using rstrip() with
   those characters as its argument:

   ```
   no_trailing_punctuation("Wait...") -> "Wait"
   ```

   *Return: the new string.*

2. **swapcase(): upper for lower and back** (P147)

   Write a function `flip_case(s)` that returns s with every upper-case letter
   made lower and every lower-case letter made upper, using swapcase():

   ```
   flip_case("Hello World") -> "hELLO wORLD"
   ```

   *Return: the new string.*

3. **removeprefix(): a title off the front** (P148)

   Write a function `without_title(name)` that returns name with a leading 'Dr
   ' removed -- and the name unchanged when it does not start with that --
   using removeprefix():

   ```
   without_title("Dr Draper") -> "Draper"
   ```

   *Return: the new string.*

4. **rfind(): the last space** (P149)

   Write a function `last_space(s)` that returns the position of the LAST
   space in s, or -1 when there is none, using rfind():

   ```
   last_space("Bartholomew van Hollingsworth") -> 15
   ```

   *Return: an integer.*

5. **casefold(): the same name, whatever the case** (P150)

   Write a function `same_name(a, b)` that returns True when the two strings
   are the same ignoring case, using casefold() on both before comparing:

   ```
   same_name("Leeds", "LEEDS") -> True
   ```

   *Return: True or False.*

## 2 - Numbers (4)

math.sqrt() of a sum, math.floor() against int() below zero, the , format spec,
and statistics.median() against mean().

6. **math.sqrt(): the diagonal of a rectangle** (P151)

   Write a function `diagonal(w, h)` that returns the length of the diagonal
   of a w by h rectangle -- the square root of w*w + h*h -- using math.sqrt().
   Remember the import.

   ```
   diagonal(3, 4) -> 5.0
   ```

   *Return: a float.*

7. **math.floor(): rounding down, below zero too** (P152)

   Write a function `round_down(x)` that returns the largest whole number that
   is not above x, as an int, using math.floor() -- so -2.5 goes DOWN to -3:

   ```
   round_down(-2.5) -> -3
   ```

   *Return: an integer.*

8. **f'{n:,}': thousands separators** (P153)

   Write a function `with_commas(n)` that returns the integer n as a string
   with a comma every three digits, using an f-string with the , format spec:

   ```
   with_commas(1234567) -> "1,234,567"
   ```

   *Return: the string.*

9. **statistics.median(): the middle value** (P154)

   Write a function `middle(values)` that returns the median of a non-empty
   list -- the middle value once sorted, or the mean of the two middle values
   when the count is even -- using statistics.median(). Remember the import.

   ```
   middle([1, 2, 10]) -> 2
   ```

   *Return: the median.*

## 3 - Sets and sequences (4)

& against |, - the right way round, list(reversed()) against reverse(), and
sorted(set()) against sorted().

10. **&: what two lists have in common** (P155)

    Write a function `common(a, b)` that returns a SET of the values that
    appear in both lists, using set() on each and the & operator:

    ```
    common(["LS1", "LS9", "BD3"], ["BD3", "LS1", "WF1"]) -> {"LS1", "BD3"}
    ```

    *Return: the set.*

11. **-: what is wanted but not held** (P156)

    Write a function `still_needed(wanted, have)` that returns a SET of the
    wanted values that are not in have, using set() on each and the -
    operator:

    ```
    still_needed(["pen", "ink", "paper"], ["ink"]) -> {"pen", "paper"}
    ```

    *Return: the set.*

12. **reversed(): a reversed copy** (P157)

    Write a function `backwards_copy(values)` that returns a NEW list with the
    items in the opposite order, leaving the original alone, using list() over
    reversed():

    ```
    backwards_copy([1, 2, 3]) -> [3, 2, 1]
    ```

    *Return: the new list.*

13. **sorted(set()): the distinct values, in order** (P158)

    Write a function `distinct_sorted(values)` that returns a LIST of the
    different values in the list, each once, in ascending order, using
    sorted() over set():

    ```
    distinct_sorted(["LS9", "LS1", "LS9", "BD3"]) -> ["BD3", "LS1", "LS9"]
    ```

    *Return: the list.*

## 4 - Dictionaries (2)

pop() with a default against pop() without, and fromkeys() with a value against
fromkeys() alone.

14. **dict.pop(key, default): take a value out** (P159)

    Write a function `take(d, key)` that removes key from the dictionary and
    returns its value -- or returns None, with nothing removed, when the key
    is not there -- using pop() with a default:

    ```
    take({"a": 1}, "z") -> None
    ```

    *Return: the value, or None.*

15. **dict.fromkeys(): every key starting at zero** (P160)

    Write a function `zero_counts(keys)` that returns a dictionary with every
    key in the list mapped to 0 -- a tally ready to be counted into -- using
    dict.fromkeys() with a value:

    ```
    zero_counts(["good", "worn"]) -> {"good": 0, "worn": 0}
    ```

    *Return: the dictionary.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,021 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
