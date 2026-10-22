# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
fourteenth set on this schema, two tools per question, with the tiers named
by task -- late returns, the branches compared, authors and titles, members
over time -- and three writable questions that each take two steps.
**Fifteen Python** functions each built around one simple loop over plain
numbers or strings, with no imports.

| Stage | SQL questions |
|---|---|
| 1 - Late returns | 1-3 |
| 2 - The branches compared | 4-6 |
| 3 - Authors and titles | 7-9 |
| 4 - Members over time | 10-12 |
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

**Driver statements.** Question 13 runs two inserts of its own *after* your
script -- a fine on a loan still out and one on a loan returned -- and
question 15 runs an INSERT against your view. Question 14 is graded on what
your script leaves behind.

| # | Construct |
|---|---|
| 13 | `BEFORE INSERT ON fines WHEN EXISTS (SELECT 1 FROM loans l WHERE l.loan_id = NEW.loan_id AND l.returned_on IS NULL) BEGIN SELECT RAISE(ABORT, ...); END` |
| 14 | `WITH q AS (SELECT hold_id, ROW_NUMBER() OVER (PARTITION BY book_id ORDER BY placed_at) rn FROM holds WHERE <open>) UPDATE holds SET cancelled_on = ... WHERE hold_id IN (SELECT hold_id FROM q WHERE rn > 3)` |
| 15 | `CREATE VIEW quick_join ...; CREATE TRIGGER ... INSTEAD OF INSERT ON quick_join BEGIN INSERT INTO members (...) VALUES (NEW.name, '1990-01-01', '2026-07-01', NEW.home_branch_id); END` |

## Things the data does on purpose

- **Member 97 has been 756 days late in total, and so has member
  1245** -- a tie at the top of question 2, which is why it fixes the
  tie-break; without the clamp their early returns cancel the late ones.
- **Every pair of branches shares at least 1,025 readers**, because
  members borrow across the whole service -- question 5's fifteen pairs.
- **4 authors tie on a 43-year span behind the two on 44**, so
  question 7's tie-break decides which three make the top five.
- **'The' or 'the' appears in 300 titles**, the top of question 8's
  word count once case is folded; counted as typed they are two words.
- **129 author-and-first-word pairs repeat**, question 9's groups;
  grouping by the word alone gives thirty-three.
- **40 of Northgate's members are dormant, 40 of them
  because they never borrowed** -- the rows question 11's LEFT JOIN keeps.
- **40 open holds sit beyond position 3 in their queue**, the ones
  question 14 cancels; the longest queue is seven deep before and three
  after.

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

## 1 - Late returns (3)

AVG of a comparison grouped by the return month under LAG, a clamped SUM ranked
with a tie-break, and a CASE over a date difference reached through a join.

1. **The late rate, month by month** (Q1042)

   For each month in which loans were RETURNED -- strftime of returned_on --
   the percentage of that month's returns that were late, to one decimal, and
   the change from the previous month in percentage points, NULL for the
   first. AVG of the comparison for the rate, LAG over it for the change.

   *Return: month, pct_late, change*

2. **The ten worst offenders** (Q1043)

   The ten members with the most days late in TOTAL over their returned loans,
   ties by lower member_id: member_id, their total days late as a whole
   number, and how many of their loans were late. Days late per loan is
   MAX(julianday(returned_on) - julianday(due_on), 0), summed; a late count is
   SUM of the comparison; ORDER BY and LIMIT.

   *Return: member_id, days_late, late_loans*

3. **What a late return costs, by how late** (Q1044)

   Fines grouped by how late the loan came back -- '1 to 7' days, '8 to 30',
   'over 30' -- with how many fines in each band and the average fine in whole
   pence. The days late come from the loan the fine hangs off,
   julianday(returned_on) minus julianday(due_on); the band is a CASE; the
   average is ROUND(AVG(amount_pence)).

   *Return: band, fines, avg_fine*

## 2 - The branches compared (3)

Loans per copy with COUNT(DISTINCT) in the denominator and a window rank over
it, a self-join of branches with a correlated count holding two EXISTS, and a
conditional MAX that picks one name out of a group.

4. **Loans per copy, and who works their stock hardest** (Q1045)

   For each branch: loans per copy to two decimals -- all loans of its copies
   over all its copies, a LEFT JOIN so copies never loaned count in the
   denominator -- and the branch's place by that ratio, 1 for the highest,
   with DENSE_RANK.

   *Return: branch_id, loans_per_copy, place*

5. **Readers two branches share** (Q1046)

   For every PAIR of branches, each pair once with the lower id first, how
   many members have borrowed a copy held at both. A self-join of branches,
   and a correlated count of members with two EXISTS tests -- one per branch
   -- through loans and copies.

   *Return: branch_a, branch_b, shared_readers*

6. **Each branch's staff, wage bill and manager** (Q1047)

   For each branch: how many staff, the total salary, and the manager's name
   -- NULL for the branch with no manager. The name comes from a conditional
   aggregate: MAX(CASE WHEN role = 'manager' THEN name END), which is the one
   manager's name or NULL.

   *Return: branch_id, staff, salary_bill, manager*

## 3 - Authors and titles (3)

MAX minus MIN with a tie-break that decides the top five, every title split into
words by recursion and counted with COUNT(DISTINCT), and GROUP BY an author and
a computed first word together.

7. **The longest writing careers** (Q1048)

   The five authors whose books span the most years -- latest published_year
   minus earliest -- ties by lower author_id: author_id, the span, and how
   many books. GROUP BY author with MAX minus MIN, ORDER BY and LIMIT.

   *Return: author_id, span_years, books*

8. **The commonest words in the titles** (Q1049)

   The ten words that appear in the most titles, ignoring case, with how many
   titles each appears in -- ties by the lower-cased word. A recursive CTE
   that splits every title into words (append a trailing space to each title
   and peel one word per step with SUBSTR and INSTR), then GROUP BY
   LOWER(word) with COUNT(DISTINCT book_id).

   *Return: word, titles*

9. **An author who starts titles the same way** (Q1050)

   Author-and-first-word pairs where the author has MORE THAN ONE book
   beginning with that word: author_id, the word, how many books. The first
   word is SUBSTR up to the space; GROUP BY both the author and the word,
   HAVING COUNT(*) > 1.

   *Return: author_id, first_word, books*

## 4 - Members over time (3)

A running SUM beside an AVG of an EXISTS, a LEFT JOIN MAX inside a CTE banded by
a CASE that tests NULL first, and a window SUM partitioned by branch.

10. **Each year's cohort, and how many of them borrow** (Q1051)

    For each year members joined: how many joined, the cumulative membership
    by the end of that year, and the percentage of that year's joiners who
    have ever borrowed, to one decimal. A window SUM over the grouped counts,
    and AVG of an EXISTS over loans for the percentage.

    *Return: join_year, joined, cumulative, pct_borrowers*

11. **Northgate's members: active, cooling or dormant** (Q1052)

    Branch 2's members in three bands by their most recent loan as of
    2026-06-30: 'active' within the last 90 days, 'cooling' within 365,
    'dormant' otherwise -- INCLUDING members who have never borrowed. A CTE
    per member with MAX(loaned_on) through a LEFT JOIN, then a CASE that tests
    the NULL first.

    *Return: band, members*

12. **Membership growth, branch by branch** (Q1053)

    For each branch and each year members joined it: how many joined that
    year, and the branch's cumulative membership by then. A window SUM
    partitioned by branch and ordered by year, over the grouped counts.

    *Return: branch_id, join_year, joined, cumulative*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger whose WHEN is an EXISTS on
NEW.loan_id, a ROW_NUMBER CTE feeding an UPDATE, and a view with an INSTEAD OF
INSERT trigger.

13. **No fine on a loan that is still out** (Q1054)

    Write a BEFORE INSERT trigger on fines that refuses -- RAISE(ABORT, ...)
    -- a fine whose loan has not been returned: the loan's returned_on is
    NULL. The WHEN is an EXISTS over loans correlated on NEW.loan_id. The
    question then fines loan 53, which is out, and loan 1, which came back.

    *Checked: the loan_ids of any fines added*

14. **No queue longer than three** (Q1055)

    Cancel, with cancelled_on = '2026-07-01', every OPEN hold that is beyond
    position 3 in its book's queue -- the fourth and later by placed_at. A CTE
    that numbers the open holds with ROW_NUMBER partitioned by book, and an
    UPDATE whose WHERE is an IN over the hold_ids numbered above 3.

    *Checked: how many holds are still open, and the longest remaining queue*

15. **A quick way to sign someone up** (Q1056)

    Create a view `quick_join (name, home_branch_id)` over members, and an
    INSTEAD OF INSERT trigger on it that inserts into members with NEW.name
    and NEW.home_branch_id, born_on '1990-01-01' and joined_on '2026-07-01'.
    The question then runs INSERT INTO quick_join (name, home_branch_id)
    VALUES ('Ada Lovelace', 1).

    *Checked: the name, branch and joined_on of any member added*

# Python

## 1 - Counting (4)

n += 1 against n = 1, an if with no else, lo <= v <= hi against the strict form,
and endswith() against in.

1. **How many spaces** (P311)

   Write a function `count_spaces(s)` that returns how many space characters s
   contains. A for loop over the characters, an if on ch == " ", and a
   counter.

   ```
   count_spaces("the glass path") -> 2
   ```

   *Return: an integer.*

2. **The sum of the positive values** (P312)

   Write a function `sum_positive(values)` that returns the total of the
   values above zero only. A for loop with an if on v > 0 and a running total.

   ```
   sum_positive([3, -1, 4, -1, 5]) -> 12
   ```

   *Return: the total.*

3. **Values inside a range** (P313)

   Write a function `count_between(values, lo, hi)` that returns how many
   values lie between lo and hi INCLUSIVE. A for loop with a chained
   comparison lo <= v <= hi under an if, and a counter.

   ```
   count_between([1, 5, 10, 15, 20], 5, 15) -> 3
   ```

   *Return: an integer.*

4. **Words that end a certain way** (P314)

   Write a function `count_ending(words, suffix)` that returns how many words
   end with the suffix, case-sensitively. A for loop with an if on
   w.endswith(suffix) and a counter.

   ```
   count_ending(["Cookbook", "Notebook", "Map", "book"], "book") -> 3
   ```

   *Return: an integer.*

## 2 - Searching (4)

A best LENGTH from 0, the index from enumerate rather than the value, 'sorted'
disproved by a strictly smaller neighbour, and a smallest by hand from
values[0].

5. **The length of the longest word** (P315)

   Write a function `longest_length(words)` that returns the length of the
   longest word, 0 for an empty list. A for loop with a best so far that
   starts at 0 and is replaced when len(w) is bigger. Do not use max() for
   this one.

   ```
   longest_length(["pen", "paper", "ink"]) -> 5
   ```

   *Return: an integer.*

6. **Where the first value over the limit is** (P316)

   Write a function `first_index_over(values, limit)` that returns the
   POSITION of the first value strictly greater than limit, or -1 if there is
   none. A for loop over enumerate(values) that returns the index at the first
   match.

   ```
   first_index_over([3, 8, 12, 5], 7) -> 1
   ```

   *Return: an integer.*

7. **Is the list in order?** (P317)

   Write a function `is_sorted(values)` that returns True when each value is
   at least as big as the one before it -- and True for an empty or one-item
   list. A for loop over range(1, len(values)) that returns False at the first
   value smaller than its predecessor, then True after the loop.

   ```
   is_sorted([3, 1, 2]) -> False
   ```

   *Return: True or False.*

8. **The smallest value, by hand** (P318)

   Write a function `smallest(values)` that returns the smallest value in a
   non-empty list WITHOUT using min(). Start a best at values[0], then a for
   loop that replaces it whenever a value is smaller.

   ```
   smallest([5, 1, 7]) -> 1
   ```

   *Return: the value.*

## 3 - Building (4)

ch + out to reverse, i % 2 on the index rather than the value, range(1, n + 1)
for triangle numbers, and a filtering loop under 'not'.

9. **A string reversed, by loop** (P319)

   Write a function `reversed_text(s)` that returns s backwards, using a for
   loop over the characters that builds the result by putting each character
   in FRONT of what has been built so far: out = ch + out. Do not use s[::-1]
   for this one.

   ```
   reversed_text("leeds") -> "sdeel"
   ```

   *Return: the new string.*

10. **The items at even positions** (P320)

    Write a function `even_positions(values)` that returns a list of the items
    at positions 0, 2, 4, ... A for loop over enumerate(values) with an if on
    i % 2 == 0 and an append. Do not use a slice for this one.

    ```
    even_positions(["a", "b", "c", "d", "e"]) -> ["a", "c", "e"]
    ```

    *Return: the new list.*

11. **The first n triangle numbers** (P321)

    Write a function `triangle_numbers(n)` that returns the first n triangle
    numbers 1, 3, 6, 10, ... -- each the sum of the whole numbers up to its
    position. A for loop over range(1, n + 1) with a running total that is
    appended each time.

    ```
    triangle_numbers(5) -> [1, 3, 6, 10, 15]
    ```

    *Return: the list.*

12. **A string without its digits** (P322)

    Write a function `without_digits(s)` that returns s with every digit
    removed. A for loop over the characters that adds each NON-digit to a
    result string, using ch.isdigit() under a 'not'.

    ```
    without_digits("LS15") -> "LS"
    ```

    *Return: the new string.*

## 4 - Reducing (3)

A seen set that counts only new values, a check BEFORE the add against a limit,
and a product that starts at 1.

13. **How many different values, by loop** (P323)

    Write a function `distinct_count(values)` that returns how many different
    values the list holds, WITHOUT using set() on the whole list at once: a
    for loop that keeps a set of values seen so far and adds one to a counter
    only when the value is new.

    ```
    distinct_count(["LS1", "LS1", "BD3"]) -> 2
    ```

    *Return: an integer.*

14. **Add up while it still fits** (P324)

    Write a function `sum_within(values, limit)` that adds up values from the
    front for as long as the running total stays at or below limit, and
    returns the total at the point it would have gone over. A for loop with a
    running total and a break when total + v would exceed limit.

    ```
    sum_within([4, 5, 3, 9], 10) -> 9
    ```

    *Return: the total.*

15. **A power, by repeated multiplication** (P325)

    Write a function `power(base, exp)` that returns base to the power exp for
    a non-negative whole exp, WITHOUT using **: a result that starts at 1 and
    a for loop over range(exp) that multiplies it by base each time.

    ```
    power(2, 10) -> 1024
    ```

    *Return: an integer.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,351 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
