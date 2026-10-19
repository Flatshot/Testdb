# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
eleventh set on this schema and the third at two tools per question, with
three writable questions that each take two steps. **Fifteen Python**
functions each built around one simple for or while loop over plain
numbers or strings, with no imports.

| Stage | SQL questions |
|---|---|
| 1 - Dates and windows | 1-2 |
| 2 - Grain and JSON | 3-4 |
| 3 - EXISTS and text | 5-6 |
| 4 - Recursion and plans | 7-8 |
| 5 - Aggregates and NULLs | 9-10 |
| 6 - Set operations and dates | 11-12 |
| 7 - Changing the data | 13-15 |

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

**Driver statements.** Question 13 runs two inserts of its own *after* your
script -- the holds your trigger should log. Questions 14 and 15 are graded
on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE TABLE hold_log ...; CREATE TRIGGER ... AFTER INSERT ON holds BEGIN INSERT INTO hold_log (payload) VALUES (json_object(...NEW...)); END` |
| 14 | `UPDATE loans SET due_on = date(due_on, CASE renewals WHEN 0 THEN '+7 days' ... END) WHERE returned_on IS NULL` |
| 15 | `CREATE VIEW member_rank AS SELECT member_id, COUNT(*), DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) FROM loans GROUP BY member_id` |

## The query-plan stage

Question 7 cannot be graded on its rows alone, because the slow query and
the fast one return exactly the same rows. It opens with the slow query
already in the editor -- correct, and the thing to improve -- and **Check
answer** also runs `EXPLAIN QUERY PLAN` on yours: it must say USING INTEGER
PRIMARY KEY and must not build an AUTOMATIC index. **Explain plan** (the
button, or F6) shows you the plan of whatever is in the editor.

## Things the data does on purpose

- **100 authors have three or more books**, question 3's rows, where
  the join to copies repeats each title once per copy.
- **88 'The' titles have no copy at Central, but 155
  have a copy somewhere else** -- the two are not complements, which is
  question 5.
- **266 members share a surname with staff at their own branch,
  1,015 with staff anywhere** -- question 6's second condition.
- **804 fines sit exactly on a hundred-pence edge**, each counted twice
  if question 8's bands close with <=.
- **49 members have two or more fines and have paid none**, which
  COUNT(paid_on) = 0 finds and SUM(paid_on IS NULL) >= 2 does not.
- **337 holds are still waiting**, and AVG forgets every one of them
  unless question 10's COALESCE gives them an end.
- **4 Sundays saw loans but no holds**, question 11's EXCEPT,
  which finds every Sunday if placed_at keeps its time.
- **4 members occupy the top three places by loans**, because two of
  them tie -- DENSE_RANK in question 15 keeps them all.

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

## 1 - Dates and windows (2)

strftime groups under a window SUM with no PARTITION for a share, and a quarter
label built from two strftimes under LAG.

1. **Each weekday's share of the loans** (Q997)

   For each day of the week -- strftime's %w, '0' for Sunday -- how many loans
   started on it and what percentage of ALL loans that is, to one decimal. The
   total is a window SUM over the grouped counts, with no PARTITION.

   *Return: weekday, loans, pct*

2. **Quarter on quarter** (Q998)

   Loans per quarter, labelled '2025Q1' and so on, with the change from the
   previous quarter -- NULL for the first. The label is strftime's year, 'Q',
   and (month + 2) / 3 joined with ||; the change is LAG over the grouped
   counts in label order.

   *Return: quarter, loans, change*

## 2 - Grain and JSON (2)

DISTINCT inside json_group_array because the join to copies multiplies the
titles, and json_group_object over a CTE grouped one level finer.

3. **Prolific authors: their titles and their copies** (Q999)

   For each author with three or more books: how many copies of their books
   exist in all, and their titles as one JSON array in alphabetical order.
   Joining copies multiplies the title rows, so the array needs DISTINCT --
   json_group_array(DISTINCT title ORDER BY title) -- and the HAVING needs
   COUNT(DISTINCT book_id).

   *Return: author_id, copies, titles*

4. **Each branch's stock as a JSON object** (Q1000)

   For each branch, ONE JSON object whose keys are the conditions and whose
   values are the copy counts -- {"damaged": 32, "good": 220, "worn": 129}. A
   CTE grouped by branch and condition, then json_group_object(condition, n)
   grouped by branch; grouping the CTE by branch_id, condition puts the keys
   in alphabetical order.

   *Return: branch_id, stock*

## 3 - EXISTS and text (2)

LIKE beside a NOT EXISTS that has to be written as a negative, and a surname
extracted on both sides of a correlated EXISTS that also matches the branch.

5. **'The' titles that Central does not hold** (Q1001)

   Books whose title begins 'The ' and of which Central (branch 1) holds NO
   copy: book_id and title. LIKE for the prefix, NOT EXISTS over copies for
   the branch.

   *Return: book_id, title*

6. **Members who share a surname with their branch's staff** (Q1002)

   Members whose surname -- the part of name after the space -- is also the
   surname of a member of staff at the member's OWN home branch: member_id and
   name. A correlated EXISTS over staff that extracts the surname on both
   sides and matches the branch.

   *Return: member_id, name*

## 4 - Recursion and plans (2)

A recursive list of numbers joined to the rowid and graded on EXPLAIN QUERY
PLAN, and recursive band edges joined to a half-open range.

7. **The first hundred loans, by their primary key** (Q1003)

   The members who hold loans 1 to 100: the loan number and member_id. A
   recursive CTE counts 1 to 100, and a join to loans looks each one up. The
   query in the editor is correct and makes SQLite scan loans for every
   number; write the join condition on the bare loan_id so each lookup is a
   rowid search. Your plan must say USING INTEGER PRIMARY KEY.

   *Return: n, member_id*

8. **Fines in bands of a hundred pence** (Q1004)

   How many fines fall in each band of 100 pence -- 0 to 99, 100 to 199, ...
   900 to 999, and 1000 on its own at the cap -- the band's lower edge and the
   count, every band present. A recursive CTE of lower edges 0, 100, ... 1000,
   and a count of fines at or above the edge and BELOW the next.

   *Return: band_from, fines*

## 5 - Aggregates and NULLs (2)

COUNT(column) = 0 in HAVING as 'none paid', and COALESCE inside AVG so the
waiting holds count.

9. **Members who have never paid a fine** (Q1005)

   Members with at least two fines, NONE of them paid: member_id and the
   number of fines. COUNT(paid_on) counts the paid ones -- the non-NULL rule
   -- so 'none paid' is COUNT(paid_on) = 0 in the HAVING, beside the count of
   all.

   *Return: member_id, fines*

10. **How long a hold takes, counting the ones still waiting** (Q1006)

    For each branch, the average days from placing a hold to its fulfilment,
    to one decimal, over the holds that were NOT cancelled -- with a hold
    still waiting counted as waiting until 2026-06-30. COALESCE(fulfilled_on,
    '2026-06-30') inside the julianday, inside the AVG.

    *Return: branch_id, avg_days*

## 6 - Set operations and dates (2)

EXCEPT where date() has to cut the time off one side, and INTERSECT where the
NULLs fall away on their own.

11. **Sundays with loans but no holds** (Q1007)

    The Sundays -- strftime('%w') = '0' -- on which loans started but no hold
    was placed: the dates. EXCEPT between the Sunday loan dates and the hold
    dates, with date() cut from placed_at on the holds side.

    *Return: day*

12. **Days with both a fine and a fulfilment** (Q1008)

    The days on which at least one fine was issued AND at least one hold was
    fulfilled: INTERSECT between the two date columns.

    *Return: day*

## 7 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger that logs
json_object(NEW...), an UPDATE with a CASE choosing the date modifier, and a
view holding DENSE_RANK.

13. **Every new hold, logged as JSON** (Q1009)

    Create `hold_log (log_id INTEGER PRIMARY KEY, payload TEXT NOT NULL)` and
    an AFTER INSERT trigger on holds that writes one row per new hold whose
    payload is a JSON object with keys hold_id, member_id and book_id taken
    from NEW. The question then inserts two holds.

    *Checked: the member_id and book_id read back from each payload with json_extract*

14. **Grace by how often a loan was renewed** (Q1010)

    Extend the due_on of every loan that is still OUT: by 7 days if it has
    never been renewed, by 3 days if renewed once, and not at all if renewed
    twice. One UPDATE whose SET uses date() with a CASE on renewals choosing
    the modifier -- '+7 days', '+3 days', '+0 days'.

    *Checked: the total loan length of the open loans at each renewal count, and of the returned loans*

15. **A leaderboard as a view** (Q1011)

    Create a view `member_rank (member_id, loans, place)` over the members who
    have borrowed: each member's loan count and their place by that count, 1
    for the most, with ties sharing a place and no numbers skipped --
    DENSE_RANK over a GROUP BY.

    *Checked: how many members are in the top three places, and the fewest loans among them*

# Python

## 1 - Counting (4)

A counter under an if, a total over range(1, n + 1), neighbours from index 1,
and a seen set that finds repeats anywhere.

1. **Count the vowels** (P266)

   Write a function `count_vowels(s)` that returns how many characters of s
   are vowels, upper or lower case. A for loop over the characters, an if that
   tests the lower-cased character against 'aeiou', and a counter.

   ```
   count_vowels("library") -> 2
   ```

   *Return: an integer.*

2. **The sum of the squares up to n** (P267)

   Write a function `sum_of_squares(n)` that returns 1*1 + 2*2 + ... + n*n,
   using a for loop over range(1, n + 1) and a running total. For n = 0 the
   answer is 0.

   ```
   sum_of_squares(3) -> 14
   ```

   *Return: an integer.*

3. **Neighbours that match** (P268)

   Write a function `count_repeats(values)` that returns how many positions
   hold the same value as the position before them. A for loop over range(1,
   len(values)), comparing values[i] with values[i - 1].

   ```
   count_repeats([1, 1, 2, 2, 2, 3]) -> 3
   ```

   *Return: an integer.*

4. **Is anything repeated?** (P269)

   Write a function `has_repeat(values)` that returns True when any value
   appears more than once, anywhere in the list. A for loop that keeps the
   values seen so far in a set, and returns True the moment the current value
   is already in it.

   ```
   has_repeat([1, 2, 3, 1]) -> True
   ```

   *Return: True or False.*

## 2 - Searching (4)

A return inside the loop for the first match, an index tracked instead of a
value, break against skip, and a running maximum that starts from None.

5. **The first value over the limit** (P270)

   Write a function `first_over(values, limit)` that returns the first value
   STRICTLY greater than limit, or None when there is none. A for loop with an
   if and a return inside it, and a return of None after the loop.

   ```
   first_over([3, 8, 12, 5], 7) -> 8
   ```

   *Return: the value, or None.*

6. **Where the smallest value is** (P271)

   Write a function `index_of_min(values)` that returns the POSITION of the
   smallest value in a non-empty list, the first such position if it appears
   more than once. A for loop over range(len(values)) that remembers the best
   position so far.

   ```
   index_of_min([5, 3, 9, 3]) -> 1
   ```

   *Return: an integer.*

7. **Add up until the first negative** (P272)

   Write a function `total_until_negative(values)` that returns the sum of the
   values BEFORE the first negative one -- all of them if none is negative. A
   for loop with a running total and a break when a negative value is met.

   ```
   total_until_negative([4, 5, -1, 10]) -> 9
   ```

   *Return: the total.*

8. **The highest so far, at every step** (P273)

   Write a function `running_max(values)` that returns a list where each
   position holds the largest value seen up to and including that position. A
   for loop with a 'best so far' variable that starts as None, and a result
   list to append to.

   ```
   running_max([3, 1, 4, 1, 5]) -> [3, 3, 4, 4, 5]
   ```

   *Return: the new list.*

## 3 - Building (4)

A while countdown whose condition decides the last value, range(1, n + 1) for a
staircase, if / elif with the most specific test first, and insert(0) to
reverse.

9. **Counting down to one** (P274)

   Write a function `countdown(n)` that returns the list n, n - 1, ..., 1 --
   empty for n of 0 or less. A while loop that appends n and then reduces it,
   running while n is above zero.

   ```
   countdown(5) -> [5, 4, 3, 2, 1]
   ```

   *Return: the list.*

10. **A staircase of stars** (P275)

    Write a function `staircase(n)` that returns a list of n strings, the
    first one star, the second two stars, and so on. A for loop over range(1,
    n + 1) appending '*' * i each time.

    ```
    staircase(3) -> ["*", "**", "***"]
    ```

    *Return: the list of strings.*

11. **Fizz and buzz, as a list** (P276)

    Write a function `fizzbuzz(n)` that returns a list for 1 to n where
    multiples of 15 become 'FizzBuzz', other multiples of 3 'Fizz', other
    multiples of 5 'Buzz', and everything else stays a number. A for loop with
    an if / elif / elif / else, testing 15 FIRST.

    ```
    fizzbuzz(5) -> [1, 2, "Fizz", 4, "Buzz"]
    ```

    *Return: the list.*

12. **The words in reverse order** (P277)

    Write a function `reverse_words(s)` that returns the words of s in the
    opposite order, joined by single spaces. A for loop over s.split() that
    builds a list by inserting each word at the FRONT -- insert(0, word) --
    then ' '.join() of the list.

    ```
    reverse_words("the glass path") -> "path glass the"
    ```

    *Return: the string.*

## 4 - Reducing (3)

Digits peeled with % and //, an average guarded against an empty list, and a
while loop that runs until n reaches 1.

13. **The digits of a number, added up** (P278)

    Write a function `digit_sum(n)` that returns the sum of the decimal digits
    of a non-negative integer, using a while loop that adds n % 10 to a total
    and then replaces n with n // 10, running while n is above zero.

    ```
    digit_sum(1234) -> 10
    ```

    *Return: an integer.*

14. **An average that copes with nothing** (P279)

    Write a function `average_or_zero(values)` that returns the mean of the
    values, or 0 for an empty list. A for loop that keeps a total and a count,
    then an if that returns 0 when the count is zero and the division
    otherwise.

    ```
    average_or_zero([2, 4, 6]) -> 4.0
    average_or_zero([]) -> 0
    ```

    *Return: the mean, or 0.*

15. **Steps to reach one** (P280)

    Write a function `collatz_steps(n)` that counts how many steps it takes to
    reach 1 from a positive integer when each step halves an even number and
    turns an odd number into 3n + 1. A while loop running while n is not 1,
    with an if / else for the two cases and a step counter that starts at 0.

    ```
    collatz_steps(6) -> 8
    ```

    *Return: an integer.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,261 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
