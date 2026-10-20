# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
twelfth set on this schema and the fourth at two tools per question, with
three writable questions that each take two steps. **Fifteen Python**
functions each built around one simple for or while loop over plain
numbers or strings, with no imports.

| Stage | SQL questions |
|---|---|
| 1 - CASE and intervals | 1-2 |
| 2 - Bare columns and dates | 3-4 |
| 3 - Windows and JSON | 5-6 |
| 4 - Text, plans and ranks | 7-8 |
| 5 - HAVING and subqueries | 9-10 |
| 6 - Set operations and windows | 11-12 |
| 7 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Counting | 1-4 |
| 2 - Searching | 5-8 |
| 3 - Building | 9-13 |
| 4 - Tracking | 14-15 |

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
script -- a one-word name and a two-word one. Questions 14 and 15 are graded
on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `BEFORE INSERT ON members WHEN INSTR(NEW.name, ' ') = 0 BEGIN SELECT RAISE(ABORT, ...); END` |
| 14 | `ALTER TABLE members ADD COLUMN tier TEXT; WITH per AS (...), t AS (SELECT ..., NTILE(4) OVER (ORDER BY n DESC) ...) UPDATE members SET tier = (SELECT CASE q ... FROM t WHERE ...) WHERE member_id IN (SELECT member_id FROM t)` |
| 15 | `DELETE FROM holds WHERE <open> AND book_id IN (SELECT value FROM json_each('[587, 275]'))` |

## The query-plan stage

Question 7 cannot be graded on its rows alone, because the slow query and
the fast one return exactly the same rows. It opens with the slow query
already in the editor -- correct, and the thing to improve -- and **Check
answer** also runs `EXPLAIN QUERY PLAN` on yours: it must say SEARCH with
`idx_books_title` and must not SCAN. **Explain plan** (the button, or F6)
shows you the plan of whatever is in the editor.

## Things the data does on purpose

- **685 loans are out and 23,291 returned**; question 1 splits the first
  group by due date, and without the WHERE splits both.
- **172 titles begin 'The '**, found through the NOCASE index by a
  LIKE and by a scan under SUBSTR or LOWER.
- **137 members have exactly 15 loans**, the ones a > instead of >= drops
  from question 9's threshold.
- **The service's late rate is 17.5 per cent**, and two branches sit
  above it; in integer arithmetic every branch's rate is 0.
- **19 members of the top decile owe nothing, and 111
  owe something** -- question 11's EXCEPT against INTERSECT.
- **Member 97 has the most loans**, badge #001 in question 8 and gold in
  question 14 -- unless NTILE runs the wrong way.
- **Books 587 and 275 have 13 open holds among 33**;
  question 15 deletes the open ones only.

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

## 1 - CASE and intervals (2)

A CASE that splits the open loans by due date, where the WHERE on returned_on
decides what is being split, and a CASE that bands loan lengths with the
narrowest band first.

1. **Open loans: overdue or not yet due, per branch** (Q1012)

   For each branch, two counts over the loans of its copies that are still OUT
   on 2026-06-30: those already past their due_on, and those not yet due. A
   conditional SUM, or SUM over a CASE, on due_on -- with the WHERE that keeps
   the returned loans out.

   *Return: branch_id, overdue, not_yet_due*

2. **How long loans last** (Q1013)

   Returned loans banded by length in days -- julianday(returned_on) -
   julianday(loaned_on) -- as 'under a week' (less than 7), 'one to three
   weeks' (7 up to and including 21) and 'over three weeks', with the count of
   each. The CASE's WHENs test the narrowest band first.

   *Return: band, loans*

## 2 - Bare columns and dates (2)

MAX of a date with a bare copy_id beside it and strftime wrapped around the MAX
-- SQLite's rule, used twice.

3. **Each branch's newest copy, and the month it came** (Q1014)

   For each branch: the copy_id of its most recently acquired copy and the
   month of that acquisition as 'YYYY-MM'. MAX(acquired_on) with copy_id as a
   bare column, and strftime on the MAX for the label.

   *Return: branch_id, copy_id, acquired_month*

4. **The last copy each branch withdrew, and the weekday** (Q1015)

   For each branch: the copy it withdrew most recently and the day of the week
   of that withdrawal as strftime's %w. MAX(withdrawn_on) over the withdrawn
   copies, copy_id as a bare column, strftime on the MAX.

   *Return: branch_id, copy_id, weekday*

## 3 - Windows and JSON (2)

A running SUM whose ORDER BY makes it cumulative, packed into a JSON array per
year, and LAG partitioned by member inside json_object inside json_group_array.

5. **Each year's running total, as a JSON array** (Q1016)

   For each year, a JSON array of the cumulative loan count month by month --
   January's loans, then January plus February, and so on. A CTE of loans per
   month with the year, a running SUM OVER (PARTITION BY year ORDER BY month),
   then json_group_array of that ordered by month, grouped by year.

   *Return: year, cumulative*

6. **Two members' loan timelines, as JSON** (Q1017)

   For members 834 and 422: one JSON array each of their loans in date order,
   each loan a JSON object with keys loan_id, loaned_on and gap -- the whole
   days since that member's previous loan, 0 for the first. LAG partitioned by
   member in a CTE, COALESCE for the first row, then json_group_array of
   json_object ordered by loaned_on.

   *Return: member_id, timeline*

## 4 - Text, plans and ranks (2)

A LIKE with no leading wildcard that the NOCASE index can search, graded on
EXPLAIN QUERY PLAN with a slow starter, and printf('%03d') over a ROW_NUMBER.

7. **Titles beginning 'The', through the index** (Q1018)

   Every book whose title begins 'The ': book_id and title. The query in the
   editor is correct and scans, because it wraps title in a function.
   idx_books_title is a NOCASE index, and SQLite can turn a LIKE with no
   leading wildcard on such a column into a range search on it: write the
   condition as a LIKE on the bare column. Your plan must say SEARCH, not
   SCAN.

   *Return: book_id, title*

8. **Badges for the ten keenest readers** (Q1019)

   The ten members with the most loans, ties by lower member_id: member_id,
   loans, and a badge like '#001' -- a hash and the rank zero-padded to three
   digits by printf. ROW_NUMBER over the grouped counts, filtered to 10 in an
   outer query.

   *Return: member_id, loans, badge*

## 5 - HAVING and subqueries (2)

A HAVING that reads a recursive threshold from the outer query, and a HAVING
compared with a scalar subquery where integer division would make every rate
zero.

9. **How many members clear each threshold** (Q1020)

   For each threshold 5, 10, 15, 20 and 25: how many members have AT LEAST
   that many loans. A recursive CTE of the thresholds, and per threshold a
   count of the members whose grouped loan count reaches it -- a HAVING inside
   a correlated subquery.

   *Return: threshold, members*

10. **Branches later than the service as a whole** (Q1021)

    Branches whose copies come back late more often than the service-wide
    rate: branch_id and the branch's late rate to four decimals. The rate is
    AVG(returned_on > due_on), and the HAVING compares it with the same AVG
    over all loans as a scalar subquery. Keep the arithmetic floating-point.

    *Return: branch_id, late_rate*

## 6 - Set operations and windows (2)

NTILE in a CTE feeding an EXCEPT, and two windows ordered opposite ways stacked
by UNION ALL with a label.

11. **The top decile with a clean slate** (Q1022)

    Members in the top tenth of borrowers by loan count who owe NO unpaid
    fine. NTILE(10) over per-member counts in a CTE, tile 10 being the
    heaviest, EXCEPT the members with an unpaid fine.

    *Return: member_id*

12. **The three most and the three least borrowed** (Q1023)

    The three books with the most loans and the three with the fewest, among
    books that have been loaned at all, as six rows labelled 'top' and
    'bottom': two ranked queries over a CTE of loans per book -- ROW_NUMBER
    descending with book_id as tie-break, and ascending likewise -- stacked
    with UNION ALL.

    *Return: label, book_id, loans*

## 7 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger whose WHEN is a string test,
ALTER TABLE then an UPDATE from an NTILE CTE through a CASE, and a DELETE whose
IN list comes from json_each.

13. **Members need a surname** (Q1024)

    Write a BEFORE INSERT trigger on members that refuses -- RAISE(ABORT, ...)
    -- a name with no space in it, since the surname questions all split on
    the space: INSTR(NEW.name, ' ') = 0 is the test. The question then inserts
    'Cher' and 'Ada Lovelace', both at branch 1.

    *Checked: the names of any members added*

14. **Reader tiers** (Q1025)

    Add a column `tier TEXT` to members, then set it for every member who has
    borrowed: 'gold' for the quarter with the most loans, then 'silver',
    'bronze' and 'basic'. A CTE of loans per member with NTILE(4) ordered by
    loans DESCENDING, and an UPDATE that reads the tile through a CASE.
    Members who never borrowed stay NULL.

    *Checked: how many members hold each tier, NULL included*

15. **Cancel the queues for two withdrawn titles** (Q1026)

    Books 587 and 275 are being withdrawn: delete every OPEN hold on them --
    fulfilled_on and cancelled_on both NULL -- leaving their closed holds as
    history. Take the two ids from the JSON list '[587, 275]' with json_each
    inside the DELETE's WHERE.

    *Checked: how many holds remain for those two books, and how many of them are open*

# Python

## 1 - Counting (4)

A strict > under an if, != between neighbours, n % i == 0 up to and including n,
and a mean computed before the loop.

1. **Words longer than a limit** (P281)

   Write a function `long_words(words, limit)` that returns how many words
   have MORE than limit characters. A for loop over the words, an if on
   len(word) > limit, and a counter.

   ```
   long_words(["pen", "paper", "ink", "notebook"], 3) -> 2
   ```

   *Return: an integer.*

2. **How often the value changes** (P282)

   Write a function `count_changes(values)` that returns how many times the
   value at a position differs from the value at the position before it. A for
   loop over range(1, len(values)), comparing values[i] with values[i - 1]
   with !=.

   ```
   count_changes([1, 1, 2, 2, 3, 3]) -> 2
   ```

   *Return: an integer.*

3. **How many numbers divide n** (P283)

   Write a function `count_divisors(n)` that returns how many whole numbers
   from 1 to n divide n exactly. A for loop over range(1, n + 1) and an if on
   n % i == 0.

   ```
   count_divisors(12) -> 6
   ```

   *Return: an integer.*

4. **Values above the average** (P284)

   Write a function `count_above_average(values)` that returns how many values
   in a non-empty list are STRICTLY above the list's mean. Work the mean out
   first with sum() and len(), then a for loop with an if and a counter.

   ```
   count_above_average([1, 2, 3, 10]) -> 1
   ```

   *Return: an integer.*

## 2 - Searching (4)

s[i] against s[-1 - i], a seen set that returns the value, a return at the first
match rather than the last, and a running total tested with >=.

5. **Is it a palindrome? By loop** (P285)

   Write a function `is_palindrome(s)` that returns True when s reads the same
   backwards, using a for loop over range(len(s) // 2) that compares s[i] with
   s[-1 - i] and returns False at the first mismatch, then True after the
   loop. Do not use s[::-1] for this one.

   ```
   is_palindrome("noon") -> True
   ```

   *Return: True or False.*

6. **The first value that repeats** (P286)

   Write a function `first_repeat(values)` that returns the first value whose
   second appearance comes earliest, or None when nothing repeats. A for loop
   with a seen set, returning the value the moment it is already in the set.

   ```
   first_repeat([3, 1, 4, 1, 5, 3]) -> 1
   ```

   *Return: the value, or None.*

7. **Where a value first appears** (P287)

   Write a function `position_of(target, values)` that returns the index of
   the FIRST occurrence of target, or -1 if it is absent. A for loop over
   range(len(values)) that returns the index as soon as values[i] equals
   target.

   ```
   position_of(7, [3, 7, 9, 7]) -> 1
   ```

   *Return: an integer.*

8. **How many items until the total reaches a target** (P288)

   Write a function `items_to_reach(values, target)` that returns how many
   items from the front are needed before their running total is AT LEAST
   target, or -1 if the whole list never gets there. A for loop over
   enumerate(values, start=1) adding to a total and returning the count the
   moment the total reaches target.

   ```
   items_to_reach([3, 4, 5, 6], 10) -> 3
   ```

   *Return: an integer.*

## 3 - Building (5)

A while over multiples with a strict limit, items() into strings built with *,
capitalize() in a transforming loop, a balance appended after each step, and a
string built with += under a 'not in'.

9. **The multiples below a limit** (P289)

   Write a function `multiples_below(k, limit)` that returns the list of
   positive multiples of k that are strictly LESS than limit, in order. A
   while loop with a running multiple that starts at k and grows by k each
   time.

   ```
   multiples_below(3, 10) -> [3, 6, 9]
   ```

   *Return: the list.*

10. **A bar chart in stars** (P290)

    Write a function `bar_lines(counts)` that returns a list of strings, one
    per key in the dictionary's order, each of the form 'key: ***' with as
    many stars as the value. A for loop over counts.items() appending a string
    built with '*' * value.

    ```
    bar_lines({"good": 3, "worn": 1}) -> ["good: ***", "worn: *"]
    ```

    *Return: the list of strings.*

11. **Each word with a capital** (P291)

    Write a function `capitalised(words)` that returns a new list with each
    word's first letter upper case and the rest lower case. A for loop that
    appends word.capitalize() to a result list.

    ```
    capitalised(["aisha", "kwame"]) -> ["Aisha", "Kwame"]
    ```

    *Return: the new list.*

12. **A balance after each change** (P292)

    Write a function `running_balance(changes)` that returns a list holding
    the balance after each change, starting from zero. A for loop with a
    running total that is appended after every addition.

    ```
    running_balance([100, -30, 50]) -> [100, 70, 120]
    ```

    *Return: the new list.*

13. **A word without its vowels** (P293)

    Write a function `without_vowels(s)` that returns s with every vowel
    removed, upper or lower case. A for loop over the characters that adds
    each NON-vowel to a result string, testing ch.lower() against 'aeiou'.

    ```
    without_vowels("library") -> "lbrry"
    ```

    *Return: the new string.*

## 4 - Tracking (2)

A run length that resets to 1 when the value changes, and n * 10 + d to rebuild
a number from its digits.

14. **The longest run of equal values** (P294)

    Write a function `longest_run(values)` that returns the length of the
    longest stretch of equal values sitting next to each other, 0 for an empty
    list. A for loop over range(1, len(values)) with a current run length that
    grows when values[i] equals values[i - 1] and resets to 1 when it does
    not, and a best so far.

    ```
    longest_run([1, 1, 2, 2, 2, 3]) -> 3
    ```

    *Return: an integer.*

15. **Digits back into a number** (P295)

    Write a function `digits_to_number(digits)` that turns a list of single
    digits into the integer they spell, 0 for an empty list. A for loop that
    keeps a number n, replacing it with n * 10 + digit at each step.

    ```
    digits_to_number([1, 2, 3, 4]) -> 1234
    ```

    *Return: an integer.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,291 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
