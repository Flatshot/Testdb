# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
thirteenth set on this schema, two tools per question, with the tiers named
by task -- queues, money owed, stock on the shelf, who reads what -- and
three writable questions that each take two steps. **Fifteen Python**:
fourteen functions each built around one simple loop over plain values,
and the classic FizzBuzz as a printed program.

| Stage | SQL questions |
|---|---|
| 1 - Queues | 1-3 |
| 2 - Money owed | 4-6 |
| 3 - Stock on the shelf | 7-9 |
| 4 - Who reads what | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Counting | 1-4 |
| 2 - Searching | 5-8 |
| 3 - Building | 9-12 |
| 4 - Reducing | 13-14 |
| 5 - The classic | 15-15 |

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

**Driver statements.** Question 13 runs one update of its own *after* your
script -- a copy coming back whose book has a queue at that branch.
Questions 14 and 15 are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `AFTER UPDATE OF returned_on ON loans WHEN NEW.returned_on IS NOT NULL BEGIN UPDATE holds SET fulfilled_on = NEW.returned_on WHERE hold_id = (SELECT ... ORDER BY placed_at LIMIT 1); END` |
| 14 | `UPDATE fines SET amount_pence = MIN(amount_pence, 500) WHERE paid_on IS NULL AND loan_id IN (SELECT l.loan_id FROM loans l JOIN members m ... WHERE m.joined_on < '2016-01-01')` |
| 15 | `INSERT INTO copies (...) SELECT ... FROM (SELECT book_id FROM holds WHERE <open> GROUP BY book_id HAVING COUNT(*) >= 3) t WHERE NOT EXISTS (<an available copy>)` |

## Things the data does on purpose

- **56 books have three or more members waiting, and 3 of
  them have no copy on any shelf** -- the three question 15 buys for, and
  the three question 2's EXISTS marks 0.
- **519 fines were paid within a week and 2,186 later; 1,380
  are unpaid**, and a CASE without the IS NULL branch files the unpaid
  under 'later'.
- **368 members owe more than they have ever paid**, by pence; counting
  fines instead of adding them gives a smaller, different set.
- **88 books are held at a single branch, but only 62 have a
  single copy** -- question 8's COUNT(DISTINCT branch_id) against COUNT(*).
- **207 members have borrowed from every genre**, question 11's
  COUNT(DISTINCT genre) = 8.
- **Member 1149 owes the most, 6,480 pence, and the five biggest debtors
  together hold under a tenth of the debt** -- a long tail, which question
  4's cumulative share shows.
- **27 unpaid fines over 500 pence belong to members who joined
  before 2016**, the rows question 14 caps.

## How the Python questions are graded

Every question in this set but the last is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Each question here is one simple loop -- a for or a
while -- with an if, a counter or a list built up inside it, and nothing to
import. The last question is a **program**, graded on what it prints: Run
shows its output, Check compares it line by line with the reference.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Queues (3)

The holds: a position by ROW_NUMBER with the wait by julianday, a HAVING over
queue lengths beside an EXISTS that holds a NOT EXISTS, and fulfilment grouped
by strftime with AVG over a date difference.

1. **The queue for book 587, with the wait so far** (Q1027)

   The open holds on book 587 -- fulfilled_on and cancelled_on both NULL --
   each with its position in the queue, 1 for the earliest placed_at, and the
   whole days it has waited up to 2026-06-30. ROW_NUMBER for the position,
   julianday for the wait.

   *Return: hold_id, position, days_waiting*

2. **Long queues, and whether a copy is free** (Q1028)

   Books with three or more open holds: book_id, how many are waiting, and 1
   or 0 for whether a copy of the book is available right now -- not withdrawn
   and with no open loan. A GROUP BY with HAVING over holds, and an EXISTS in
   the SELECT list that contains a NOT EXISTS.

   *Return: book_id, waiting, has_available*

3. **How long holds took, by the month they were placed** (Q1029)

   For each month holds were placed -- strftime of placed_at -- how many of
   those holds have been fulfilled, and their average wait in days to one
   decimal: AVG of julianday(fulfilled_on) minus julianday(placed_at), which
   skips the holds never fulfilled on its own.

   *Return: month, fulfilled, avg_days*

## 2 - Money owed (3)

The fines: a running SUM over a CTE against a scalar total, a CASE over a date
difference with the NULL branch first, and two conditional SUMs compared in
HAVING.

4. **The five biggest debtors and their share of the debt** (Q1030)

   The five members who owe the most in unpaid fines, ties by lower member_id:
   member_id, pence owed, and the cumulative percentage of ALL unpaid pence
   that the debtors so far account for, to one decimal. A CTE of unpaid totals
   per member, a running SUM ordered by owed descending, the grand total as a
   scalar subquery, and LIMIT 5.

   *Return: member_id, owed, cum_pct*

5. **How quickly fines get paid** (Q1031)

   Every fine in one of three classes with its count: 'unpaid' when paid_on is
   NULL, 'within a week' when paid within 7 days of issue --
   julianday(paid_on) minus julianday(issued_on) at most 7 -- and 'later'
   otherwise. The NULL test goes first in the CASE.

   *Return: speed, fines*

6. **Members who owe more than they have ever paid** (Q1032)

   Members whose UNPAID fines add up to more pence than their PAID fines:
   member_id, unpaid pence, paid pence. Two conditional SUMs -- CASE on
   paid_on, ELSE 0 -- and a HAVING that compares them.

   *Return: member_id, unpaid_pence, paid_pence*

## 3 - Stock on the shelf (3)

The copies: SUM of a two-part availability test, COUNT(DISTINCT branch_id) = 1
with the branch name as a bare column, and percentages by a partitioned window
packed by json_group_object.

7. **Children's books available at each branch** (Q1033)

   For each branch, how many of its children's copies are available right now:
   not withdrawn, and with no loan whose returned_on is NULL. A join to books
   for the genre, and a SUM over the two-part test with the NOT EXISTS inside
   it.

   *Return: branch_id, available*

8. **Books held at one branch only** (Q1034)

   Books all of whose copies are at a SINGLE branch, however many copies:
   book_id, that branch's name, and the copy count. GROUP BY book with HAVING
   COUNT(DISTINCT branch_id) = 1, MIN(branch_id) to name the branch -- every
   copy's branch is the same one -- joined to branches.

   *Return: book_id, branch_name, copies*

9. **Each branch's condition mix, as JSON percentages** (Q1035)

   For each branch, a JSON object whose keys are the conditions and whose
   values are the percentage of the branch's copies in that condition, to one
   decimal. A CTE counting copies per branch and condition, a window SUM
   partitioned by branch for the denominator, then json_group_object grouped
   by branch with the CTE ordered by branch_id, condition.

   *Return: branch_id, mix*

## 4 - Who reads what (3)

The members: two windows over one grouped CTE for a favourite genre and a
threshold, COUNT(DISTINCT genre) against a scalar subquery, and a LEFT JOIN
count inside a CTE banded by CASE.

10. **Each Old Town regular's favourite genre** (Q1036)

    For each member of branch 6 with at least 10 loans: the genre they have
    borrowed most, ties by genre name, and how many loans of it. A CTE of
    loans per member and genre, a window SUM for the member's total and
    ROW_NUMBER for the ranking, then rank 1 where the total is 10 or more.

    *Return: member_id, genre, loans*

11. **Readers of every genre** (Q1037)

    Members who have borrowed from ALL eight genres: member_id and their total
    loans. Two joins to reach the genre, a GROUP BY member, and HAVING
    COUNT(DISTINCT genre) = 8 -- or equal to the number of genres as a
    subquery.

    *Return: member_id, loans*

12. **Loans per member, by age band** (Q1038)

    Members in three age bands by year of birth against 2026 -- 'under 30',
    '30 to 59', '60 and over' -- with how many members each band has and their
    average loans per member to one decimal, counting the members with NO
    loans as 0. A CTE per member with the band and a LEFT JOIN count, then a
    GROUP BY the band.

    *Return: band, members, avg_loans*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger whose body is an UPDATE with
a LIMIT 1 subquery, an UPDATE scoped through IN (SELECT ... JOIN ...), and an
INSERT ... SELECT with HAVING and NOT EXISTS.

13. **A returned copy goes to the front of the queue** (Q1039)

    Write an AFTER UPDATE OF returned_on trigger on loans that, when a loan is
    marked returned, marks as fulfilled -- with fulfilled_on = NEW.returned_on
    -- the OLDEST open hold on that copy's book AT THE COPY'S BRANCH, if there
    is one, and only that one: an UPDATE of holds whose WHERE picks the
    hold_id with a subquery ordered by placed_at LIMIT 1. The question then
    returns loan 19031 on 2026-07-01.

    *Checked: how many of the book's holds are still open, and the oldest hold at that branch's fulfilled_on*

14. **A cap on old members' unpaid fines** (Q1040)

    Members who joined before 2016 get their UNPAID fines capped at 500 pence:
    set amount_pence to MIN(amount_pence, 500) for those fines only. The
    member is two joins away from a fine, so the WHERE uses a subquery over
    loans and members; paid fines and newer members are untouched.

    *Checked: the count and total of unpaid fines, and the total of paid fines*

15. **Order a copy for every hopeless queue** (Q1041)

    For every book with three or more open holds and NO available copy -- none
    that is not withdrawn and free of open loans -- add one copy at Central
    (branch 1), acquired '2026-07-01', condition 'good'. One INSERT ... SELECT
    whose source is a grouped subquery with HAVING, filtered by a NOT EXISTS
    over copies.

    *Checked: how many copies were acquired on 2026-07-01, and how many books with three or more open holds still have no available copy*

# Python

## 1 - Counting (4)

< against <=, % 2 == 0 against == 1, break against skip, and startswith()
against in.

1. **How many are negative** (P296)

   Write a function `count_negatives(values)` that returns how many values are
   below zero. A for loop with an if on v < 0 and a counter; zero itself is
   not negative.

   ```
   count_negatives([3, -1, -4, 0, 5]) -> 2
   ```

   *Return: an integer.*

2. **The sum of the even numbers** (P297)

   Write a function `sum_even(values)` that returns the total of the even
   values only. A for loop with an if on v % 2 == 0 and a running total.

   ```
   sum_even([1, 2, 3, 4, 5, 6]) -> 12
   ```

   *Return: the total.*

3. **How many come before the stop value** (P298)

   Write a function `count_before(values, stop)` that returns how many items
   come before the first one equal to stop -- all of them when stop never
   appears. A for loop that breaks at the stop value and counts otherwise.

   ```
   count_before(["a", "b", "stop", "c"], "stop") -> 2
   ```

   *Return: an integer.*

4. **Words that start with a letter** (P299)

   Write a function `count_starting(words, letter)` that returns how many
   words start with the given letter, case-sensitively. A for loop with an if
   on w.startswith(letter) and a counter.

   ```
   count_starting(["Beyond", "Bright", "Dark", "blue"], "B") -> 2
   ```

   *Return: an integer.*

## 2 - Searching (4)

A best-so-far from values[0] rather than 0, 'all' proved by failing to find a
counter-example, a strict > under a first-match return, and a last index
recorded rather than returned.

5. **The largest value, by hand** (P300)

   Write a function `largest(values)` that returns the biggest value in a non-
   empty list WITHOUT using max(). Start a best at values[0], then a for loop
   that replaces it whenever a value is bigger.

   ```
   largest([-5, -1, -7]) -> -1
   ```

   *Return: the value.*

6. **Are they all positive?** (P301)

   Write a function `all_positive(values)` that returns True when every value
   is above zero -- and True for an empty list, since nothing fails. A for
   loop that returns False at the first value that is not positive, then True
   after the loop. Do not use all() for this one.

   ```
   all_positive([1, 0, 3]) -> False
   ```

   *Return: True or False.*

7. **The first long word** (P302)

   Write a function `first_long_word(words, n)` that returns the first word
   with MORE than n characters, or None if there is none. A for loop with an
   if on len(w) > n and a return inside it.

   ```
   first_long_word(["pen", "ink", "paper", "notebook"], 4) -> "paper"
   ```

   *Return: the word, or None.*

8. **Where a value LAST appears** (P303)

   Write a function `last_position_of(target, values)` that returns the index
   of the LAST occurrence of target, or -1 if it is absent. A for loop over
   range(len(values)) that records the index each time it matches and returns
   the record after the loop.

   ```
   last_position_of(7, [3, 7, 9, 7]) -> 3
   ```

   *Return: an integer.*

## 3 - Building (4)

A return at the right indentation, len(w) rather than len(words), a running
product from 1, and an if that filters while the append transforms.

9. **Every value doubled** (P304)

   Write a function `doubled(values)` that returns a new list with each value
   multiplied by 2, in order. A for loop that appends v * 2 to a result list.

   ```
   doubled([1, 2, 3]) -> [2, 4, 6]
   ```

   *Return: the new list.*

10. **The length of each word** (P305)

    Write a function `word_lengths(words)` that returns a list of the lengths
    of the words, in order. A for loop that appends len(w) to a result list.

    ```
    word_lengths(["pen", "paper", ""]) -> [3, 5, 0]
    ```

    *Return: the new list.*

11. **A running product** (P306)

    Write a function `running_product(values)` that returns a list where each
    position holds the product of the values up to and including it. A for
    loop with a running product that starts at 1 and is appended after each
    multiplication.

    ```
    running_product([2, 3, 4]) -> [2, 6, 24]
    ```

    *Return: the new list.*

12. **The squares of the odd values** (P307)

    Write a function `odd_squares(values)` that returns a list of the squares
    of the ODD values only, in order. A for loop with an if on v % 2 != 0 and
    an append of v * v.

    ```
    odd_squares([1, 2, 3, 4, 5]) -> [1, 9, 25]
    ```

    *Return: the new list.*

## 4 - Reducing (2)

A while that halves with //= and returns the count, and enumerate for
alternating signs.

13. **How many times it halves** (P308)

    Write a function `times_halvable(n)` that returns how many times a
    positive integer can be divided by 2 before it becomes odd. A while loop
    running while n % 2 == 0, using n //= 2 and a counter.

    ```
    times_halvable(12) -> 2
    ```

    *Return: an integer.*

14. **Add, subtract, add, subtract** (P309)

    Write a function `alternating_sum(values)` that returns the first value
    minus the second plus the third minus the fourth and so on. A for loop
    over enumerate(values) with an if on whether the index is even, adding or
    subtracting accordingly.

    ```
    alternating_sum([10, 3, 2, 1]) -> 8
    ```

    *Return: the result.*

## 5 - The classic (1)

FizzBuzz printed for 1 to 30, where the branch for 15 has to come first.

15. **FizzBuzz, 1 to 30** (P310)

    Write a program that prints the numbers 1 to 30, one per line -- except
    that multiples of 3 print Fizz, multiples of 5 print Buzz, and multiples
    of both print FizzBuzz. A for loop over range(1, 31) with an if / elif /
    elif / else, testing 15 first.

    *Print: thirty lines, the first five being 1, 2, Fizz, 4, Buzz.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,321 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
