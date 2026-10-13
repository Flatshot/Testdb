# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
seventh set on this schema, on five tiers none of the library sets have
used: CTE chains; IN, EXISTS and JOIN; formatting; numeric functions; and
three writable statements new to the library. **Fifteen Python**: tiny
functions of one or two lines, each about ONE tool named in the question's
title, none of them used by an earlier set.

| Stage | SQL questions |
|---|---|
| 1 - CTE chains | 1-3 |
| 2 - IN, EXISTS and JOIN | 4-6 |
| 3 - Formatting | 7-9 |
| 4 - Numeric functions | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Strings | 1-4 |
| 2 - Numbers | 5-8 |
| 3 - Lists | 9-12 |
| 4 - Sets and dictionaries | 13-15 |

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

**Driver statements.** Question 13 runs three deletes of its own *after*
your script -- an open hold, a fulfilled one and a cancelled one. Questions
14 and 15 are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `BEFORE DELETE ON holds WHEN OLD.fulfilled_on IS NULL AND OLD.cancelled_on IS NULL` |
| 14 | `CREATE VIEW open_loans ...; CREATE VIEW overdue_by_branch AS SELECT ... FROM open_loans ...` |
| 15 | `UPDATE staff SET role = 'manager' WHERE staff_id = (SELECT ... ORDER BY hired_on LIMIT 1)` |

## Things the data does on purpose

- **211 members are above their own branch's average borrower,
  170 above the service's** -- question 1's chain against one
  global average.
- **1,181 members have had a fine, and there are 4,085 fines**; a join
  without DISTINCT returns the second number of rows for question 4.
- **110 days saw loans but no hold fulfilled**; NOT IN against
  fulfilled_on returns none of them, because the column holds NULLs.
- **213 members have a hold at their own branch, out of 885
  who have placed one** -- question 6's single EXISTS against two INs.
- **4 members owe 5,000 pence or more**, question 8's rows;
  1149 owes the most, 1,380 fines are unpaid in all.
- **Old Town has 2 librarians and no manager**; question
  15 promotes the longer-serving one, and only that one.
- **Holds 1, 2 and 7 are open, fulfilled and cancelled respectively**, the
  three question 13's trigger must tell apart.

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

## 1 - CTE chains (3)

Two or three WITH clauses that read each other: counts, then averages of the
counts; days, then days ranked within months; months, then years summed from
them.

1. **Above the average for their own branch** (Q937)

   Members who have borrowed more often than the average borrower of THEIR OWN
   home branch. Three steps in WITH: loans per member with their home branch;
   the average of those counts per branch; then the members above their
   branch's figure.

   *Return: member_id, home_branch_id, loans*

2. **The busiest day of each month** (Q938)

   For each month of the data, the day with the most loans started, and how
   many: a CTE of loans per day, a second CTE that numbers the days within
   their month by loans descending -- ties broken by the earlier day -- and a
   final SELECT of the days numbered 1.

   *Return: month, day, loans*

3. **Each month's share of its year** (Q939)

   For each month: its loans, and what percentage of THAT YEAR's loans they
   are, to one decimal. A CTE of loans per month that also carries the year, a
   second CTE summing the first per year, and a join between the two on the
   year.

   *Return: month, loans, pct_of_year*

## 2 - IN, EXISTS and JOIN (3)

Three spellings of 'has at least one', where the join needs DISTINCT; a NOT IN
that a single NULL turns into nothing; and two conditions that must hold for the
same row.

4. **Members who have ever been fined** (Q940)

   Every member who has had at least one fine, paid or not, ONCE each:
   member_id and name. Fines reach the member through loans. EXISTS, IN or a
   join with DISTINCT all work; a plain join does not.

   *Return: member_id, name*

5. **Days with loans but no hold fulfilled** (Q941)

   Days on which loans started but NO hold was fulfilled: the day and how many
   loans. Beware NOT IN against holds.fulfilled_on, which is NULL for the open
   holds -- a single NULL in a NOT IN list makes the whole test unknown for
   every row. Exclude the NULLs, or use NOT EXISTS.

   *Return: day, loans*

6. **A hold at their own branch** (Q942)

   Members who have placed a hold to collect at their OWN home branch -- a
   single hold whose branch_id equals the member's home_branch_id. Two
   conditions on the same hold row, which is one correlated EXISTS, not two IN
   tests.

   *Return: member_id*

## 3 - Formatting (3)

printf for a zero-padded code and for money with two decimals, and strftime for
a date written the British way -- formatting as the last step, with the stored
form left alone.

7. **Membership codes** (Q943)

   For the members of branch 6: a membership code made of 'M' and the
   member_id zero-padded to four digits -- M0011, M0014 -- using
   printf('%04d', ...) and ||.

   *Return: member_id, code*

8. **What the biggest debtors owe, in pounds** (Q944)

   Members whose UNPAID fines add up to 5000 pence or more: member_id and the
   total as text in pounds with exactly two decimals and a leading pound sign
   -- '£55.60', not 55.6. printf('%.2f', ...) does the decimals.

   *Return: member_id, owed*

9. **Opening dates, written the British way** (Q945)

   Each branch's opening date written day/month/year -- 12/05/1902 for
   1902-05-12 -- using strftime.

   *Return: branch_id, opened*

## 4 - Numeric functions (3)

ROUND against CAST, ABS for a distance from the average, and / with % to split
pence into pounds and pence.

10. **Average pages per genre, to the nearest page** (Q946)

    The average page count of each genre's books, as a whole number rounded to
    the NEAREST page -- ROUND, not CAST, which truncates.

    *Return: genre, avg_pages*

11. **How far each branch is from the average stock** (Q947)

    For each branch: its copies, and how far that is from the average branch's
    copies -- total copies over six -- as a whole number that is never
    negative: ABS of the difference, rounded.

    *Return: branch_id, copies, deviation*

12. **Pounds and pence, split** (Q948)

    The total of fines, unpaid and paid separately, split into whole pounds
    and the pence left over -- 4149 pounds and 60 pence from 414,960 -- with
    integer division and the % remainder operator.

    *Return: paid, pounds, pence*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A BEFORE DELETE trigger that protects
open holds, a view built on a view, and an UPDATE whose WHERE is a LIMIT 1
subquery.

13. **Open holds cannot be deleted** (Q949)

    Write a BEFORE DELETE trigger on holds that refuses -- RAISE(ABORT, ...)
    -- to delete a hold that is still OPEN, fulfilled_on and cancelled_on both
    NULL; closed holds may go. The question then deletes hold 1 (open), hold 2
    (fulfilled) and hold 7 (cancelled).

    *Checked: which of the three holds still exist*

14. **A view on a view** (Q950)

    Create a view `open_loans (loan_id, copy_id, member_id, due_on)` of the
    loans with no returned_on, then a second view `overdue_by_branch
    (branch_id, overdue)` that reads open_loans -- not loans -- joined to
    copies, counting per branch the open loans due before 2026-06-30.

    *Checked: the second view's rows*

15. **Old Town gets a manager** (Q951)

    Branch 6 has no manager. Promote its longest-serving librarian -- the
    earliest hired_on among branch 6's librarians -- to 'manager', and nobody
    else. One UPDATE whose WHERE finds that one staff_id with a subquery.

    *Checked: how many managers each branch has, and who branch 6's is*

# Python

## 1 - Strings (4)

rpartition() against partition(), rjust() against ljust(), rsplit(maxsplit=1)
against split(), and isascii() against isalpha().

1. **rpartition(): split at the LAST dot** (P206)

   Write a function `name_and_extension(filename)` that returns a tuple (name,
   extension) split at the LAST '.', using rpartition(). With no dot,
   rpartition puts the whole string in the last part, so the name is '' and
   the extension is the string.

   ```
   name_and_extension("archive.tar.gz") -> ("archive.tar", "gz")
   ```

   *Return: the tuple.*

2. **rjust(): numbers lined up on the right** (P207)

   Write a function `right_aligned(s, width)` that returns s padded on the
   LEFT with spaces to the given width, so that a column of them lines up on
   the right, using rjust():

   ```
   right_aligned("42", 6) -> "    42"
   ```

   A string already wider than width is returned unchanged.

   *Return: the string.*

3. **rsplit(maxsplit=1): everything but the last word** (P208)

   Write a function `without_last_word(s)` that returns s with its last word
   removed -- and a one-word string unchanged -- using rsplit() with a single
   split from the right and taking the first part:

   ```
   without_last_word("The Glass Path") -> "The Glass"
   ```

   *Return: the string.*

4. **isascii(): plain characters only** (P209)

   Write a function `plain_ascii(s)` that returns True when every character in
   s is plain ASCII -- no accents, no symbols beyond the keyboard -- using
   isascii(). The empty string counts as True.

   ```
   plain_ascii("LS15!") -> True
   ```

   *Return: True or False.*

## 2 - Numbers (4)

math.hypot() against adding the legs, math.comb() against math.perm(),
statistics.mode() against max(), and hex() against format(n, 'x').

5. **math.hypot(): straight-line distance** (P210)

   Write a function `distance(dx, dy)` that returns the straight-line distance
   covered by moving dx across and dy up, using math.hypot(). Remember the
   import.

   ```
   distance(3, 4) -> 5.0
   ```

   *Return: a float.*

6. **math.comb(): ways to choose** (P211)

   Write a function `ways_to_choose(n, k)` that returns how many different
   groups of k can be picked from n items, order not mattering, using
   math.comb(). Remember the import.

   ```
   ways_to_choose(5, 2) -> 10
   ```

   *Return: an integer.*

7. **statistics.mode(): the commonest value** (P212)

   Write a function `most_common(values)` that returns the value that appears
   most often in a non-empty list -- the first one met, when several tie --
   using statistics.mode(). Remember the import.

   ```
   most_common(["b", "a", "a"]) -> "a"
   ```

   *Return: the value.*

8. **hex(): a number in base sixteen** (P213)

   Write a function `as_hex(n)` that returns the hexadecimal form of a non-
   negative integer as a string WITH the 0x prefix, using hex():

   ```
   as_hex(255) -> "0xff"
   ```

   *Return: the string.*

## 3 - Lists (4)

del against pop(), [x] * n against x * n, filter(None) against a test for None,
and tuple() against list().

9. **del: remove the item at a position** (P214)

   Write a function `drop_at(values, i)` that returns a NEW list with the item
   at position i removed, leaving the original alone, using the del statement
   on a copy:

   ```
   drop_at([1, 2, 3], 1) -> [1, 3]
   ```

   *Return: the new list.*

10. **[x] * n: a list of n copies** (P215)

    Write a function `repeated(x, n)` that returns a list holding x n times,
    using list repetition with *:

    ```
    repeated("ab", 3) -> ["ab", "ab", "ab"]
    ```

    *Return: the list.*

11. **filter(None, ...): drop everything falsy** (P216)

    Write a function `truthy_only(values)` that returns a list of the values
    that count as true -- dropping 0, '', None, empty lists and the like --
    using list() over filter() with None as the function:

    ```
    truthy_only([0, 1, "", "a", None]) -> [1, "a"]
    ```

    *Return: the new list.*

12. **tuple(): a list made unchangeable** (P217)

    Write a function `freeze(values)` that returns the items of the list as a
    tuple, using tuple():

    ```
    freeze([1, 2]) -> (1, 2)
    ```

    *Return: the tuple.*

## 4 - Sets and dictionaries (3)

add() returns None, isdisjoint() against !=, and dict(pairs) against
dict.fromkeys(pairs).

13. **add(): one more member of a set** (P218)

    Write a function `with_added(items, x)` that returns a SET of the items
    with x included -- the set is unchanged when x was already in it -- using
    set() and add():

    ```
    with_added([1, 2], 3) -> {1, 2, 3}
    ```

    *Return: the set.*

14. **isdisjoint(): nothing in common?** (P219)

    Write a function `no_overlap(a, b)` that returns True when the two lists
    share no value at all, using set() on a and isdisjoint():

    ```
    no_overlap([1, 2], [3]) -> True
    ```

    *Return: True or False.*

15. **dict(pairs): a dictionary from (key, value) tuples** (P220)

    Write a function `to_dict(pairs)` that returns a dictionary built from a
    list of (key, value) tuples, using dict(). When a key appears twice, the
    later value wins.

    ```
    to_dict([("a", 1), ("b", 2)]) -> {"a": 1, "b": 2}
    ```

    *Return: the dictionary.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,141 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
