# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
second set on this schema, with the topics mixed up -- six new tiers instead
of the seven stages the hospital sets wore -- and **fifteen Python**: tiny
functions of one or two lines, each about ONE tool named in the question's
title, none of them used by an earlier set.

| Stage | SQL questions |
|---|---|
| 1 - Set operations | 1-2 |
| 2 - CASE | 3-4 |
| 3 - Self-joins and EXISTS | 5-7 |
| 4 - Recursive CTEs | 8-9 |
| 5 - Text and NULLs | 10-12 |
| 6 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Strings | 1-5 |
| 2 - Numbers | 6-9 |
| 3 - Lists | 10-13 |
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
to its day -- which question 2 and question 8 both need.

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

None of the three runs statements of its own afterwards; each is graded on
what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE TABLE` then `INSERT ... SELECT`, with the WHERE that keeps withdrawn copies out |
| 14 | a `DELETE` with two conditions, where the forgotten one erases 324 debts |
| 15 | `ALTER TABLE ADD COLUMN ... DEFAULT`, then an `UPDATE` by `NOT EXISTS` |

## Things the data does on purpose

- **200 of the 1,500 members have never borrowed anything** -- the rows
  that decide question 1's EXCEPT (members on the left gives 200 too
  many) and question 15's UPDATE (a HAVING on MAX(loaned_on) cannot see
  them; 212 members are lapsed, 200 of them for that reason).
- **415 members have borrowed but never placed a hold**, question 1's
  answer.
- **20 of the 600 titles have no copies, and only 2
  have copies that were never loaned** -- question 6's two rows, which a
  NOT IN against copy ids inflates to twenty-nine.
- **257 members owe a fine and have a book out at the same time**, but
  never on the same loan: a fine's loan has been returned, which is why
  question 7 needs two EXISTS and one join finds nobody.
- **2026-03-07 is the one day of March 2026 with no hold placed**, the row
  question 8's calendar exists to keep.
- **117 copies are withdrawn**, the rows question 13's WHERE removes.
- **778 fines issued before 2025-07-01 are paid and 324 are
  not**; question 14 deletes the first group and must keep the second.
- **19 of branch 4's members have no recorded postcode area**, the
  group question 11 labels 'unknown'.
- **Member 1149 owes 6,480 pence**, the debt question 9 pays off in seven
  instalments.

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

## 1 - Set operations (2)

EXCEPT with the right table on the left, and UNION ALL over two queries whose
third columns have to be made the same kind of text.

1. **Borrowers who never queue** (Q862)

   Members who have borrowed at least once but have never placed a hold. Use
   EXCEPT: one SELECT over loans, one over holds. Members who have never
   borrowed are not wanted.

   *Return: member_id*

2. **One member's history, in one list** (Q863)

   Member 834's loans and holds as ONE list. Each loan is a row with the kind
   'loan', the copy's book_id and loaned_on; each hold is a row with the kind
   'hold', its book_id and the DAY it was placed, as 'YYYY-MM-DD' -- placed_at
   carries a time of day as well.

   *Return: kind, book_id, on_day*

## 2 - CASE (2)

A pivot by SUM over a comparison, where COUNT with ELSE 0 counts the zeros, and
a four-way CASE whose IS NULL branch has to come first.

3. **Condition of the stock, one row a branch** (Q864)

   For each branch, ONE row with the number of its copies in each condition as
   three columns: good, worn, damaged. That is a pivot -- SUM over a CASE, or
   over a comparison. Count withdrawn copies too.

   *Return: branch_id, good, worn, damaged*

4. **How loans ended** (Q865)

   Put every loan in one of four classes and count each: 'out' when
   returned_on is NULL, 'early' when it was returned before due_on, 'on time'
   when returned on due_on, and 'late' when returned after it.

   *Return: class, loans*

## 3 - Self-joins and EXISTS (3)

One table under two aliases with a strict inequality so each pair appears once;
NOT EXISTS that has to reach the book through copies; and two EXISTS on one
member that a single join cannot express.

5. **Colleagues in the same role** (Q866)

   Pairs of staff who work at the same branch in the same role, each pair
   ONCE, with the lower staff_id first. Nobody is paired with themselves.

   *Return: branch_id, role, staff_a, staff_b*

6. **Stocked but never borrowed** (Q867)

   Books that have at least one copy and whose copies have NEVER been loaned:
   book_id, title, and how many copies there are. A loan points at a copy, not
   a book, so the test has to go through copies.

   *Return: book_id, title, copies*

7. **In debt and still holding a book** (Q868)

   Members who owe an UNPAID fine and ALSO have a loan out right now --
   returned_on NULL. A fine hangs off a loan that has come back, so the loan
   that is out is a DIFFERENT loan: two separate tests on the member, not one
   join.

   *Return: member_id*

## 4 - Recursive CTEs (2)

A calendar manufactured by recursion so the empty day keeps its zero, and a
repayment loop whose stopping test and clamp are both needed.

8. **Every day of March, holds or not** (Q869)

   For EVERY day of March 2026, how many holds were placed that day --
   including the day with none, which a GROUP BY over holds alone cannot
   produce. Build the days with a recursive CTE, date(day, '+1 day'), and
   count the holds whose date(placed_at) is that day.

   *Return: day, holds*

9. **Paying it off in instalments** (Q870)

   Member 1149 owes 6480 pence. They pay 1000 pence on 2026-07-01 and the same
   again every 7 days until nothing is owed. List the instalments: its number,
   the day, and what remains AFTER it -- never below zero, so the last payment
   only clears the 480 left. Use a recursive CTE.

   *Return: instalment, pay_on, remaining*

## 5 - Text and NULLs (3)

SUBSTR from INSTR plus one, COALESCE as the label of the NULL group, and
MAX(days, 0) so that AVG sees a zero rather than skipping a NULL.

10. **Surnames of the staff** (Q871)

    Each staff member's surname: the part of name AFTER the one space in it,
    without the space. INSTR finds the space and SUBSTR takes from a position
    to the end.

    *Return: staff_id, surname*

11. **Where branch 4's members live** (Q872)

    For the members whose home branch is 4: how many live in each postcode
    area, with the members whose area was never recorded counted together
    under the label 'unknown'.

    *Return: area, members*

12. **Days late on average, on time counting as zero** (Q873)

    For each branch, over the RETURNED loans of its copies: the average number
    of days late, to two decimals, where a loan returned on time or early
    counts as 0 days late -- not as missing. julianday(returned_on) -
    julianday(due_on) is the days late, negative when early.

    *Return: branch_id, avg_days_late*

## 6 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. CREATE TABLE filled by INSERT ...
SELECT, a DELETE whose second condition keeps the debts, and ALTER TABLE ADD
COLUMN followed by an UPDATE that remembers the never-borrowers.

13. **A stock table from a query** (Q874)

    Create a table `branch_stock (branch_id INTEGER PRIMARY KEY, copies
    INTEGER NOT NULL)` and fill it with one row per branch: the number of its
    copies that are NOT withdrawn. Use INSERT ... SELECT, not typed values.

    *Checked: the table's rows*

14. **Clear out the old paid fines** (Q875)

    Delete the fines that are PAID and were issued before 2025-07-01. Unpaid
    fines from that time stay, however old they are.

    *Checked: how many fines remain, how many of those are unpaid, and what all the remaining fines add up to*

15. **A status column for members** (Q876)

    Add a column `status TEXT NOT NULL DEFAULT 'active'` to members, then set
    it to 'lapsed' for every member with no loan on or after 2026-01-01 --
    INCLUDING the members who have never borrowed at all.

    *Checked: how many members carry each status*

# Python

## 1 - Strings (5)

capitalize() against title(), zfill() against rjust(), isalpha() against
isalnum(), partition() against split(), and splitlines() against counting
newlines.

1. **capitalize(): one capital at the front** (P131)

   Write a function `sentence_case(s)` that returns s with its first character
   in upper case and EVERYTHING else in lower case, using capitalize():

   ```
   sentence_case("hELLO wORLD") -> "Hello world"
   ```

   *Return: the new string.*

2. **zfill(): padding a number with zeros** (P132)

   Write a function `pad_id(n, width)` that returns the number n as a string
   of at least `width` characters, padded on the left with zeros, using str()
   and zfill():

   ```
   pad_id(7, 4) -> "0007"
   ```

   A number already wider than width is returned as it is.

   *Return: the string.*

3. **isalpha(): letters and nothing else** (P133)

   Write a function `only_letters(s)` that returns True when s is made of
   letters only -- no digits, spaces or punctuation -- and False otherwise,
   using isalpha():

   ```
   only_letters("LS15") -> False
   ```

   *Return: True or False.*

4. **partition(): split at the first sign** (P134)

   Write a function `key_value(s)` that returns a tuple (key, value) from a
   setting written as 'key=value', splitting at the FIRST '=' only, using
   partition():

   ```
   key_value("eq=a=b") -> ("eq", "a=b")
   ```

   With no '=' at all the key is the whole string and the value is ''.

   *Return: the tuple.*

5. **splitlines(): how many lines** (P135)

   Write a function `line_count(text)` that returns how many lines text has,
   using splitlines(): a trailing newline does not start an extra line, and
   the empty string has no lines at all.

   ```
   line_count("a\nb\n") -> 2
   ```

   *Return: an integer.*

## 2 - Numbers (4)

** against ^, min() with default= for the empty list, isinstance() with a tuple
of types, and math.ceil() against round().

6. ****: raising to a power** (P136)

   Write a function `cube(n)` that returns n to the power of 3, using the **
   operator:

   ```
   cube(3) -> 27
   ```

   *Return: the number.*

7. **min(default=): the smallest, or None** (P137)

   Write a function `lowest(values)` that returns the smallest value in the
   list, or None when the list is empty, using min() with its default=
   argument:

   ```
   lowest([4, 2, 9]) -> 2
   lowest([]) -> None
   ```

   *Return: the smallest value, or None.*

8. **isinstance(): is it a number?** (P138)

   Write a function `is_number(x)` that returns True when x is an int or a
   float and False for anything else, using isinstance() with a tuple of
   types:

   ```
   is_number(2.5) -> True
   is_number("3") -> False
   ```

   *Return: True or False.*

9. **math.ceil(): rounding up** (P139)

   Write a function `boxes_needed(items, per_box)` that returns how many boxes
   hold all the items when each box takes per_box -- a part-filled box still
   counts -- using math.ceil() on the division. Remember the import.

   ```
   boxes_needed(7, 3) -> 3
   ```

   *Return: an integer.*

## 3 - Lists (4)

any() and all() each against the other, len(set()) for distinct values, and
[::2] against [1::2].

10. **any(): is at least one true?** (P140)

    Write a function `has_negative(values)` that returns True when at least
    one value in the list is below zero, using any() over a generator
    expression:

    ```
    has_negative([1, -2, 3]) -> True
    ```

    *Return: True or False.*

11. **all(): are they all true?** (P141)

    Write a function `all_passed(marks, pass_mark)` that returns True when
    every mark is at least pass_mark, using all() over a generator expression.
    An empty list passes -- nobody failed.

    ```
    all_passed([50, 30], 40) -> False
    ```

    *Return: True or False.*

12. **len(set()): how many different values** (P142)

    Write a function `distinct_count(values)` that returns how many DIFFERENT
    values the list holds, using len() of a set():

    ```
    distinct_count(["LS1", "LS1", "BD3"]) -> 2
    ```

    *Return: an integer.*

13. **[::2]: every other item** (P143)

    Write a function `every_other(values)` that returns a new list of the
    items at positions 0, 2, 4, ... -- the first and then every second one --
    using a slice with a step:

    ```
    every_other([1, 2, 3, 4, 5]) -> [1, 3, 5]
    ```

    *Return: the new list.*

## 4 - Dictionaries (2)

update() on a copy, because it returns None, and a dict comprehension that swaps
key and value.

14. **dict.update(): one dictionary over another** (P144)

    Write a function `merged(a, b)` that returns a NEW dictionary with
    everything from a and then everything from b, b winning where a key is in
    both, using update() on a copy of a. Neither argument is changed.

    ```
    merged({"x": 1, "y": 2}, {"y": 3}) -> {"x": 1, "y": 3}
    ```

    *Return: the new dictionary.*

15. **{k: v for ...}: a dictionary turned inside out** (P145)

    Write a function `invert(d)` that returns a new dictionary with d's values
    as keys and d's keys as values, using a dict comprehension over d.items():

    ```
    invert({"a": 1, "b": 2}) -> {1: "a", 2: "b"}
    ```

    *Return: the new dictionary.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
991 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
