# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
fifteenth set on this schema, two tools per question, with the tiers named
by task -- renewals, the catalogue, staff and salaries, a day in the life --
and three writable questions that each take two steps. **Fifteen Python**
functions each built around one simple loop over plain numbers or strings,
with no imports.

| Stage | SQL questions |
|---|---|
| 1 - Renewals | 1-3 |
| 2 - The catalogue | 4-6 |
| 3 - Staff and salaries | 7-9 |
| 4 - A day in the life | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Counting | 1-4 |
| 2 - Searching | 5-8 |
| 3 - Building | 9-12 |
| 4 - Reducing | 13-15 |

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

**Driver statements.** Question 13 runs three updates of its own *after*
your script -- a proper renewal, one that leaves the due date alone, and
one that adds only a week. Questions 14 and 15 are graded on what your
script leaves behind.

| # | Construct |
|---|---|
| 13 | `BEFORE UPDATE OF renewals ON loans WHEN NEW.renewals > OLD.renewals AND NEW.due_on <> date(OLD.due_on, '+14 days') BEGIN SELECT RAISE(ABORT, ...); END` |
| 14 | `UPDATE staff SET salary = (SELECT ROUND(AVG(...)) ... WHERE ... branch_id = staff.branch_id) WHERE role = 'librarian' AND salary < (the same average)` |
| 15 | `CREATE TABLE late_returns AS SELECT ... FROM loans WHERE returned_on > due_on; CREATE INDEX idx_late_member ON late_returns (member_id);` |

## Things the data does on purpose

- **49.6 per cent of loans were renewed at least once**, and the
  genres barely differ -- question 1's ranking turns on decimals.
- **Loans never renewed come back late 26.5 per cent of the time, loans
  renewed twice 4.6 per cent** -- but the late ones are about as late
  either way, which question 2's two averages show side by side.
- **11 authors have written two or more cookbooks**, and
  96 of the 600 titles were published since 2020, a sixth of the
  catalogue in question 5's last decade.
- **The service spends 395 pounds of salary per copy held**; three
  branches are above that, Central furthest.
- **49 loans came back on Monday 2 March 2026, 9 of
  them late** -- the nine fines of the day, and the rows an inner join
  keeps in question 12.
- **6 librarians earn less than their own branch's librarian
  average**, the rows question 14 raises.
- **4,085 loans came back late**, the rows of question 15's table;
  returned IS NOT NULL would make it 23,291.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Each question here is one simple loop -- a for or a
while -- with an if, a counter or a list built up inside it, and nothing to
import.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Renewals (3)

AVG of renewals > 0 under a DENSE_RANK, a conditional AVG that leaves the on-
time loans out beside a rate that counts them, and HAVING with a ratio that has
to be floating-point.

1. **Which genres get renewed** (Q1057)

   For each genre, the percentage of its loans that were renewed at least
   once, to one decimal, and the genre's place by that rate, 1 for the
   highest. AVG of the comparison renewals > 0 through the two joins, and
   DENSE_RANK over the grouped rate.

   *Return: genre, pct_renewed, place*

2. **Does renewing help?** (Q1058)

   For each renewal count 0, 1 and 2, over the RETURNED loans: the percentage
   returned late, and the average days late AMONG the late ones, both to one
   decimal. A CASE with no ELSE inside the second AVG, so on-time loans are
   NULL and skipped rather than counted as 0.

   *Return: renewals, pct_late, avg_days_late*

3. **The keenest renewers** (Q1059)

   The ten members with the most renewals per loan among members with at least
   10 loans, ties by lower member_id: member_id, loans, and renewals per loan
   to two decimals. GROUP BY with HAVING on the count, a floating-point ratio
   of SUM over COUNT, ORDER BY and LIMIT.

   *Return: member_id, loans, renewals_per_loan*

## 2 - The catalogue (3)

MAX(pages) with the title as a bare column, a running window SUM over decades
against the catalogue's size, and LIKE narrowing the rows before a HAVING and a
json_group_array.

4. **The longest book in each genre** (Q1060)

   For each genre: the title and page count of its longest book. MAX(pages)
   with title as a bare column -- SQLite brings the title from the row the MAX
   came from. Each genre's maximum is held by one book.

   *Return: genre, title, pages*

5. **The catalogue by decade of publication** (Q1061)

   Books per decade of publication -- published_year / 10 * 10 -- with the
   cumulative percentage of the catalogue published by the end of that decade,
   to one decimal. A running window SUM over the grouped counts, divided by
   the catalogue's 600.

   *Return: decade, books, cum_pct*

6. **Authors with more than one cookbook** (Q1062)

   Authors with two or more titles ending in 'Cookbook': author_id, the total
   pages of those cookbooks, and the titles as a JSON array in alphabetical
   order. A LIKE in the WHERE, GROUP BY author, HAVING on the count,
   SUM(pages) and json_group_array with ORDER BY.

   *Return: author_id, cookbook_pages, titles*

## 3 - Staff and salaries (3)

DENSE_RANK and MAX OVER the same partition, a CASE over a julianday difference
in years, and two scalar subqueries per branch against a scalar average where a
join would multiply.

7. **Where each person stands in their role** (Q1063)

   Every member of staff with their place by salary within their ROLE, 1 for
   the best paid, and how far below the role's top salary they are. DENSE_RANK
   partitioned by role, and MAX(salary) OVER the same partition minus the
   salary.

   *Return: staff_id, role, place, gap*

8. **Pay by length of service** (Q1064)

   Staff in three bands by years of service on 2026-06-30 -- 'under 5', '5 to
   14', '15 and over' -- with how many are in each and their average salary in
   whole pounds. Years of service are the julianday difference over 365.25;
   the band is a CASE with the smallest band tested first.

   *Return: band, staff, avg_salary*

9. **Wage bill per copy, where it runs high** (Q1065)

   Branches whose total staff salary per copy held is above the service-wide
   figure -- all salaries over all copies. Staff and copies are two children
   of a branch, so each total is its own scalar subquery; the comparison is
   against a scalar subquery too. Whole pounds per copy.

   *Return: branch_id, salary_per_copy*

## 4 - A day in the life (3)

Four counts stacked by UNION ALL with date() on the datetime, strftime('%H')
under ROW_NUMBER, and a LEFT JOIN with COALESCE so the on-time returns keep
their rows.

10. **Monday 2 March 2026, in four numbers** (Q1066)

    For 2026-03-02, four rows labelled 'loans', 'returns', 'holds' and 'fines'
    with how many of each happened that day: loans started, loans returned,
    holds placed -- date() of placed_at -- and fines issued. Four one-row
    queries stacked by UNION ALL.

    *Return: event, count*

11. **When members place holds** (Q1067)

    The three hours of the day in which the most holds have been placed, ties
    by the earlier hour: the hour as strftime's %H, and the count. GROUP BY
    the hour, ROW_NUMBER over the counts, keep the first three.

    *Return: hour, holds*

12. **Monday's returns, and what they cost** (Q1068)

    Every loan returned on 2026-03-02: loan_id, 1 or 0 for whether it was
    late, and the fine in pence -- 0 when there is none. A LEFT JOIN to fines
    so on-time returns keep their row, and COALESCE for the missing amount.

    *Return: loan_id, late, fine_pence*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger comparing NEW with date
arithmetic on OLD, an UPDATE with a correlated AVG in SET and WHERE, and CREATE
TABLE AS SELECT followed by CREATE INDEX.

13. **A renewal moves the due date by exactly a fortnight** (Q1069)

    Write a BEFORE UPDATE OF renewals trigger on loans that refuses --
    RAISE(ABORT, ...) -- any update that raises renewals unless the new due_on
    is exactly OLD.due_on plus 14 days. The question then renews loan 156
    properly, loan 180 without moving its due date, and loan 4107 with only
    seven days added.

    *Checked: the renewals and due_on of the three loans*

14. **Bring the underpaid librarians up to their branch's average** (Q1070)

    Every librarian paid LESS than the average librarian salary at their own
    branch is raised to that average, rounded to whole pounds. One UPDATE
    whose SET and WHERE both use a correlated subquery over staff for the same
    branch and role. Nobody else changes.

    *Checked: the total salary of each role*

15. **A table of late returns, indexed** (Q1071)

    Create a table `late_returns` with CREATE TABLE ... AS SELECT holding, for
    every loan returned AFTER its due date, the loan_id, member_id, and
    days_late as a whole number -- then CREATE INDEX idx_late_member ON
    late_returns (member_id). On-time and open loans are not in it.

    *Checked: how many rows the table holds, the largest days_late, and whether the index exists*

# Python

## 1 - Counting (4)

isupper() against == upper(), range(n) for 'below n', if f: against a string
comparison, and in against count().

1. **How many capital letters** (P326)

   Write a function `count_upper(s)` that returns how many characters of s are
   upper-case letters. A for loop over the characters, an if on ch.isupper(),
   and a counter.

   ```
   count_upper("The Glass Path") -> 3
   ```

   *Return: an integer.*

2. **The sum of the odd numbers below n** (P327)

   Write a function `sum_odds_below(n)` that returns the sum of the odd whole
   numbers that are less than n. A for loop over range(n) with an if on i % 2
   == 1 and a running total.

   ```
   sum_odds_below(10) -> 25
   ```

   *Return: an integer.*

3. **How many are True** (P328)

   Write a function `count_true(flags)` that returns how many items in a list
   of booleans are True. A for loop with an if on the flag itself -- if flag:
   -- and a counter.

   ```
   count_true([True, False, True]) -> 2
   ```

   *Return: an integer.*

4. **Words that contain a letter** (P329)

   Write a function `count_containing(words, letter)` that returns how many
   words contain the letter at least once, case-sensitively. A for loop with
   an if on letter in w and a counter.

   ```
   count_containing(["pen", "paper", "ink"], "p") -> 2
   ```

   *Return: an integer.*

## 2 - Searching (4)

A tracked index with a strict >, 'any' proved by one example without an else, a
last match recorded, and abs() for nearness.

5. **Where the largest value is** (P330)

   Write a function `index_of_max(values)` that returns the POSITION of the
   largest value in a non-empty list, the first such position if it appears
   more than once. A for loop over range(1, len(values)) that remembers the
   best position so far, starting at 0.

   ```
   index_of_max([3, 9, 2, 9]) -> 1
   ```

   *Return: an integer.*

6. **Is any of them negative?** (P331)

   Write a function `any_negative(values)` that returns True when at least one
   value is below zero, and False otherwise -- including for an empty list. A
   for loop that returns True at the first negative value, then False after
   the loop. Do not use any() for this one.

   ```
   any_negative([1, -2, 3]) -> True
   ```

   *Return: True or False.*

7. **The last word longer than n** (P332)

   Write a function `last_long_word(words, n)` that returns the LAST word with
   more than n characters, or None if there is none. A for loop that records
   each match in a variable and returns it after the loop.

   ```
   last_long_word(["pen", "paper", "ink", "notebook", "map"], 3) -> "notebook"
   ```

   *Return: the word, or None.*

8. **The value nearest a target** (P333)

   Write a function `nearest_to(values, target)` that returns the value in a
   non-empty list closest to target -- the FIRST such value when two are
   equally close. A for loop with a best so far that starts at values[0] and
   is replaced when abs(v - target) is strictly smaller than abs(best -
   target).

   ```
   nearest_to([3, 9, 14], 10) -> 9
   ```

   *Return: the value.*

## 3 - Building (4)

i * i, w[0] added to a string, two appends per item, and append before subtract
in a while.

9. **The first n squares** (P334)

   Write a function `squares(n)` that returns the list of the squares of 1 to
   n. A for loop over range(1, n + 1) that appends i * i.

   ```
   squares(5) -> [1, 4, 9, 16, 25]
   ```

   *Return: the list.*

10. **Initials, built up by loop** (P335)

    Write a function `initials(words)` that returns a string of the first
    character of each word, in order. A for loop that adds w[0] to a result
    string that starts empty. Every word has at least one character.

    ```
    initials(["Aisha", "Ekwueme"]) -> "AE"
    ```

    *Return: the string.*

11. **Each item twice** (P336)

    Write a function `repeat_each(values)` that returns a new list with every
    item appearing twice in a row. A for loop that appends each item two
    times.

    ```
    repeat_each([1, 2, 3]) -> [1, 1, 2, 2, 3, 3]
    ```

    *Return: the new list.*

12. **Counting down in steps** (P337)

    Write a function `countdown_by(n, step)` that returns the list n, n -
    step, n - 2 * step, ... for as long as the value stays above zero. A while
    loop on n > 0 that appends n and then subtracts step.

    ```
    countdown_by(10, 3) -> [10, 7, 4, 1]
    ```

    *Return: the list.*

## 4 - Reducing (3)

abs() for a gap either way, int(ch) under isdigit(), and a check at every step
rather than at the end.

13. **The biggest jump between neighbours** (P338)

    Write a function `max_gap(values)` that returns the largest absolute
    difference between two neighbouring values, 0 for a list of fewer than
    two. A for loop over range(1, len(values)) comparing abs(values[i] -
    values[i - 1]) with a best so far that starts at 0.

    ```
    max_gap([1, 4, 9, 11]) -> 5
    ```

    *Return: the gap.*

14. **The digits in a string, added up** (P339)

    Write a function `sum_digits_in(s)` that returns the sum of the digit
    characters in s, 0 if there are none. A for loop over the characters with
    an if on ch.isdigit() that adds int(ch) to a total.

    ```
    sum_digits_in("LS15") -> 6
    ```

    *Return: an integer.*

15. **Does the balance ever go below zero?** (P340)

    Write a function `stays_positive(changes)` that returns True when a
    balance starting at zero never drops below zero as the changes are applied
    in order, and False as soon as it does. A for loop with a running total
    and a return of False inside it, then True after the loop.

    ```
    stays_positive([10, -20, 15]) -> False
    ```

    *Return: True or False.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,381 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
