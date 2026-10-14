# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
eighth set on this schema, on five tiers none of the library sets have
used: aggregates and totals, string tricks, pivots both ways, SQLite's bare
columns, and three writable statements new to the library. **Fifteen
Python**: tiny functions of one or two lines, each about ONE tool named in
the question's title, none of them used by an earlier set.

| Stage | SQL questions |
|---|---|
| 1 - Aggregates and totals | 1-5 |
| 2 - String tricks | 6-8 |
| 3 - Pivots both ways | 9-10 |
| 4 - SQLite bare columns | 11-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Strings | 1-4 |
| 2 - Numbers | 5-8 |
| 3 - Lists | 9-12 |
| 4 - Dictionaries | 13-15 |

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

**Driver statements.** Question 13 runs two updates of its own *after* your
script -- two real changes and one re-save of the same value, which your
trigger should log and ignore respectively. Questions 14 and 15 are graded
on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE TABLE condition_log ...; CREATE TRIGGER ... AFTER UPDATE OF condition ON copies WHEN OLD.condition <> NEW.condition` |
| 14 | `DELETE FROM holds WHERE <open> AND NOT EXISTS (SELECT 1 FROM copies c WHERE c.book_id = holds.book_id AND c.branch_id = holds.branch_id)` |
| 15 | `INSERT INTO copies (...) SELECT ... FROM books b WHERE NOT EXISTS (SELECT 1 FROM copies c WHERE c.book_id = b.book_id)` |

## Things the data does on purpose

- **Eastfield's copies are 12.5 per cent damaged**, the highest
  share; question 1 wants the branches over ten per cent AND over 350
  copies, both facts about the whole branch.
- **83 members have ten or more loans and have never been late**
  -- a SUM of the late test equal to zero, which COUNT of it never is.
- **22,453 distinct member-and-title pairs account for the 23,976 loans**;
  re-borrowing is the gap question 5 measures.
- **54 poetry titles**, questions 6 and 7's rows; **61 titles
  begin 'Poems for a', and 3 of those go on with a P** -- the ones
  LTRIM mangles in question 8.
- **strftime returns text**, so '2025' is never 2025 and question 9's
  pivot comes out all zeros when compared with a number.
- **176 open holds are at a branch with no copy of the book, and
  780 holds in all**; question 14 deletes the first group only.
- **20 books have no copies**, the rows question 15's INSERT ...
  SELECT fills in, once.

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

## 1 - Aggregates and totals (5)

HAVING with two or three aggregate conditions, where a WHERE would change what
is averaged; a total row by UNION ALL; and COUNT(DISTINCT) over two columns
joined with a separator.

1. **Big branches with a damage problem** (Q952)

   Branches holding at least 350 copies of which more than 10 per cent are
   damaged: branch_id, copies, and the damaged percentage to one decimal. Both
   conditions are about the branch as a whole, so both go in HAVING -- a WHERE
   on condition would change what is being counted.

   *Return: branch_id, copies, pct_damaged*

2. **Regulars who are never late** (Q953)

   Members with at least 10 loans, NONE of which came back late: member_id and
   their loan count. 'None late' is an aggregate condition -- a SUM of the
   late test equal to zero -- not a WHERE.

   *Return: member_id, loans*

3. **Long books from a long way back** (Q954)

   Genres whose books average more than 480 pages AND whose earliest
   publication year is before 1900: genre, the average pages rounded to a
   whole number, and that earliest year. The average is over ALL the genre's
   books.

   *Return: genre, avg_pages, earliest*

4. **Copies per branch, with a total row** (Q955)

   Copies per branch as six rows with the branch_id as text, plus a seventh
   row labelled 'all' with the total: a GROUP BY query UNION ALL a one-row
   total query. CAST the id to TEXT so the two queries' first columns agree.

   *Return: branch, copies*

5. **Readers of a title, not loans of it** (Q956)

   For each genre: loans, and how many DISTINCT member-and-title pairs those
   loans are -- a member who borrowed the same title three times is one pair.
   COUNT(DISTINCT) takes one expression, so join the two ids into one with ||.

   *Return: genre, loans, pairs*

## 2 - String tricks (3)

printf's minus sign for left justification, LOWER inside REPLACE for a slug, and
LTRIM's second argument, which is a set of characters and not a prefix.

6. **A column of titles, padded to the right** (Q957)

   The poetry titles each padded with spaces on the RIGHT to 24 characters and
   followed by '|', so the bars line up in a fixed-width listing: printf with
   %-24s.

   *Return: book_id, padded*

7. **Slugs for the poetry titles** (Q958)

   A web slug for each poetry title: the title in lower case with every space
   replaced by a hyphen -- 'lost-library'. LOWER and REPLACE, one inside the
   other.

   *Return: book_id, slug*

8. **After 'Poems for a'** (Q959)

   For the titles that begin 'Poems for a ', the rest of the title after that
   prefix -- 'Paper Tower' from 'Poems for a Paper Tower'. The prefix is
   twelve characters, so SUBSTR from position 13. LTRIM(title, 'Poems for a ')
   is NOT the same thing.

   *Return: book_id, rest*

## 3 - Pivots both ways (2)

Three SUMs into one row, where strftime's text never equals an integer, and
three counts into three rows by UNION ALL.

9. **Loans per genre, one column a year** (Q960)

   For each genre, its loans in 2025 and in 2026 as two columns: a pivot by
   conditional SUM. Compare the year as text -- strftime returns text, and
   '2025' is not 2025.

   *Return: genre, loans_2025, loans_2026*

10. **Branch 4's holds, one row a status** (Q961)

    The holds placed at branch 4 as THREE rows -- 'fulfilled', 'cancelled',
    'waiting' -- each with its count: an unpivot, three one-row queries joined
    by UNION ALL.

    *Return: status, holds*

## 4 - SQLite bare columns (2)

A column selected beside a single MIN or MAX comes from that row -- SQLite's
rule, and not most databases' -- so the latest loan's copy and the longest-
serving person's name need no subquery.

11. **Each Old Town member's latest loan** (Q962)

    For each member whose home branch is 6 and who has borrowed: their latest
    loaned_on, and the copy_id of THAT loan. In SQLite, a column selected
    alongside a single MAX comes from the row the MAX was found in -- a 'bare
    column' -- so no subquery is needed.

    *Return: member_id, last_loan, copy_id*

12. **The longest-serving person at each branch** (Q963)

    For each branch: the name and hired_on of its longest-serving member of
    staff, using MIN(hired_on) and the bare name column beside it.

    *Return: branch_id, name, hired_on*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger that logs a change only when
there was one, a correlated DELETE that keeps history, and an INSERT ... SELECT
that can run twice.

13. **A log of condition changes** (Q964)

    Create a table `condition_log (log_id INTEGER PRIMARY KEY, copy_id INTEGER
    NOT NULL, old_condition TEXT NOT NULL, new_condition TEXT NOT NULL)` and
    an AFTER UPDATE OF condition trigger on copies that inserts a row into it
    -- only when the condition actually CHANGED. The question then marks
    copies 1 and 2 damaged and re-saves copy 3 unchanged.

    *Checked: the log's copy_id, old and new, in log order*

14. **Holds that can never be met where they stand** (Q965)

    Delete the OPEN holds -- fulfilled_on and cancelled_on both NULL -- placed
    at a branch that holds no copy of the book at all. Closed holds stay,
    whatever branch they name. The test on copies is a correlated NOT EXISTS
    inside the DELETE's WHERE.

    *Checked: how many holds remain, how many of them are open, and how many open holds are still at a branch without the book*

15. **A copy for every title, and no more than that** (Q966)

    Give every book that has NO copies one copy at Central (branch 1),
    acquired '2026-07-01', in 'good' condition -- with a single INSERT ...
    SELECT whose WHERE NOT EXISTS skips the books already stocked, so running
    it twice adds nothing the second time.

    *Checked: how many copies there are, how many books still have none, and how many copies were acquired on 2026-07-01*

# Python

## 1 - Strings (4)

The + spec against str(), lstrip(chars) against strip(chars), textwrap.shorten()
against a slice, and !r against a plain f-string.

1. **f'{n:+}': always show the sign** (P221)

   Write a function `signed(n)` that returns the number as a string with its
   sign always shown -- '+5' as well as '-3' -- using the + format spec in an
   f-string:

   ```
   signed(5) -> "+5"
   ```

   *Return: the string.*

2. **lstrip(chars): leading zeros off** (P222)

   Write a function `without_leading_zeros(s)` that returns s with any zeros
   removed from its LEFT end only -- the zeros inside or at the end stay --
   using lstrip() with '0':

   ```
   without_leading_zeros("0042") -> "42"
   without_leading_zeros("100") -> "100"
   ```

   *Return: the new string.*

3. **textwrap.shorten(): cut at a word, with a marker** (P223)

   Write a function `shortened(text, width)` that returns the text cut to at
   most width characters at a WORD boundary, ending in ' [...]' when something
   was cut, using textwrap.shorten(). Text that already fits is returned as it
   is. Remember the import.

   ```
   shortened("one two three four", 13) -> "one two [...]"
   ```

   *Return: the string.*

4. **f'{s!r}': the value as Python would write it** (P224)

   Write a function `quoted(s)` that returns s wrapped in the quotes Python
   itself would print it with -- repr form -- using !r inside an f-string:

   ```
   quoted("Leeds") -> "'Leeds'"
   ```

   *Return: the string.*

## 2 - Numbers (4)

math.isqrt() against ** 0.5, bit_length() against len(bin()), math.dist()
against the taxi-cab sum, and pow(b, e, m) against a remainder by 10.

5. **math.isqrt(): the whole-number square root** (P225)

   Write a function `whole_root(n)` that returns the largest whole number
   whose square is at most n, as an int, using math.isqrt(). Remember the
   import.

   ```
   whole_root(17) -> 4
   ```

   *Return: an integer.*

6. **bit_length(): how many binary digits** (P226)

   Write a function `bits_needed(n)` that returns how many binary digits a
   non-negative integer needs -- 0 for zero, 8 for 255, 9 for 256 -- using the
   int method bit_length():

   ```
   bits_needed(255) -> 8
   ```

   *Return: an integer.*

7. **math.dist(): distance between two points** (P227)

   Write a function `distance_between(p, q)` that returns the straight-line
   distance between two points given as (x, y) tuples, using math.dist().
   Remember the import.

   ```
   distance_between((0, 0), (3, 4)) -> 5.0
   ```

   *Return: a float.*

8. **pow(b, e, m): a power, reduced as it goes** (P228)

   Write a function `last_two_digits(b, e)` that returns the last two digits
   of b to the power e -- the remainder on division by 100 -- using the three-
   argument form of pow():

   ```
   last_two_digits(2, 10) -> 24
   ```

   *Return: an integer.*

## 3 - Lists (4)

accumulate() for running totals, nlargest() against a slice of sorted(),
itemgetter(1) against sorting the tuples, and Counter() against fromkeys().

9. **itertools.accumulate(): running totals** (P229)

   Write a function `running_total(values)` that returns a list where each
   item is the sum of the values up to and including that position, using
   list() over itertools.accumulate(). Remember the import.

   ```
   running_total([1, 2, 3]) -> [1, 3, 6]
   ```

   *Return: the new list.*

10. **heapq.nlargest(): the top three** (P230)

    Write a function `top_three(values)` that returns the three largest
    values, largest first -- fewer when the list is shorter -- using
    heapq.nlargest(). Remember the import.

    ```
    top_three([5, 1, 9, 3, 7]) -> [9, 7, 5]
    ```

    *Return: the list.*

11. **itemgetter(): sort pairs by their second item** (P231)

    Write a function `by_second(pairs)` that returns the list of (name,
    number) pairs sorted by the NUMBER, using sorted() with key=itemgetter(1)
    from the operator module. Remember the import.

    ```
    by_second([("a", 3), ("b", 1), ("c", 2)]) -> [("b", 1), ("c", 2), ("a", 3)]
    ```

    *Return: the new list.*

12. **Counter(): how many of each** (P232)

    Write a function `tally(values)` that returns a dictionary mapping each
    value to how many times it appears, using collections.Counter(). Remember
    the import.

    ```
    tally(["a", "b", "a"]) -> {"a": 2, "b": 1}
    ```

    *Return: the dictionary.*

## 4 - Dictionaries (3)

sorted(d, key=d.get) against sorted(d), next(iter(d)) against d[0], and
sum(d.values()) against sum(d).

13. **sorted(d, key=d.get): keys in order of their values** (P233)

    Write a function `keys_by_value(d)` that returns the dictionary's keys as
    a list ordered by their VALUES, smallest value first, using sorted() over
    the dict with key=d.get:

    ```
    keys_by_value({"a": 3, "b": 1, "c": 2}) -> ["b", "c", "a"]
    ```

    *Return: the list of keys.*

14. **next(iter(d)): the first key** (P234)

    Write a function `first_key(d)` that returns the first key of a non-empty
    dictionary -- the one inserted first -- using next() over iter():

    ```
    first_key({"a": 1, "b": 2}) -> "a"
    ```

    *Return: the key.*

15. **sum(d.values()): the total of a tally** (P235)

    Write a function `total_of(d)` that returns the sum of all the
    dictionary's values, using sum() over values():

    ```
    total_of({"a": 1, "b": 2}) -> 3
    ```

    *Return: the total.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,171 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
