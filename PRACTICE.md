# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
tenth set on this schema and the second at two tools per question, paired
differently, with three writable questions that each take two steps.
**Fifteen Python**: tiny functions of one or two lines, each about ONE tool
named in the question's title, with the import line stated wherever one is
needed.

| Stage | SQL questions |
|---|---|
| 1 - Plans and CASE | 1-2 |
| 2 - JSON and dates | 3-4 |
| 3 - Bare columns and open ends | 5-6 |
| 4 - Set operations and text | 7-8 |
| 5 - Windows and NULLs | 9-10 |
| 6 - Recursion and text | 11-12 |
| 7 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Strings | 1-4 |
| 2 - Numbers | 5-9 |
| 3 - Lists | 10-13 |
| 4 - Sets and dictionaries | 14-15 |

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
script -- a renewal of an overdue loan and of one not yet due. Questions 14
and 15 are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `BEFORE UPDATE OF renewals ON loans WHEN NEW.renewals > OLD.renewals AND OLD.due_on < '2026-06-30'` |
| 14 | `CREATE TABLE branch_hours ...; INSERT ... SELECT ... FROM branches; INSERT ... ON CONFLICT (branch_id) DO UPDATE SET hours = excluded.hours` |
| 15 | `DELETE FROM holds WHERE hold_id IN (SELECT hold_id FROM (... ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY placed_at DESC) ... WHERE closed) WHERE rn > 1)` |

## The query-plan stage

Questions 1 and 2 cannot be graded on their rows alone, because the slow
query and the fast one return exactly the same rows. Each opens with the
slow query already in the editor -- correct, and the thing to improve --
and **Check answer** also runs `EXPLAIN QUERY PLAN` on yours: 1 must say
SEARCH with `idx_loans_due`, 2 must say COVERING INDEX `idx_loans_copy`.
**Explain plan** (the button, or F6) shows you the plan of whatever is in the
editor.

## Things the data does on purpose

- **1,349 loans fall due in May 2026**, found by a range on due_on in a
  few steps or by strftime in 24,000; **copy 1 has 14 loans**, all of
  which the covering index knows about without opening the table.
- **108 copies have never been loaned**, the pool question 5's MAX
  picks from once NOT EXISTS has narrowed it.
- **56 members have an open hold at Northgate, out of 225 who
  ever held there** -- question 6's WHERE against no WHERE.
- **14 first words are shared by fiction and poetry**, and
  **8 member surnames belong to no staff member** -- while every
  staff surname belongs to some member, so question 8 reversed is empty.
- **1,380 fines are unpaid**, the total question 9's running sum reaches
  in its last row.
- **Loan 4107 is out and was due 20 June; loan 156 is due 17 July** -- the
  two renewals question 13's trigger must tell apart, and a test on
  NEW.due_on lets the first one through.
- **300 members have more than one closed hold**, the duplicates
  question 15 thins while leaving the 337 open holds alone.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Each question here is one or two lines about one tool,
named in its title, and says which import line to write when one is needed.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Plans and CASE (2)

Two questions graded on EXPLAIN QUERY PLAN with a slow query already in the
editor: a date RANGE on the bare column so the index is searched, and a query
that mentions only indexed columns so the index covers it. A CASE rides on top
of each.

1. **Due in May, found by the index** (Q982)

   Every loan due in May 2026, with a status: 'out' if returned_on is NULL,
   else 'returned'. The query in the editor is correct but wraps due_on in
   strftime, which reads all 24,000 loans. Rewrite the WHERE as a RANGE on the
   bare column so idx_loans_due can be searched. Your plan must mention
   idx_loans_due with SEARCH, not SCAN.

   *Return: loan_id, status*

2. **Copy 1's loans, weekday or weekend, from the index alone** (Q983)

   For copy 1, each loan's loaned_on and whether it was a 'weekend' (strftime
   %w of '0' or '6') or a 'weekday'. The index idx_loans_copy holds copy_id
   and loaned_on, so a query that touches only those columns can be answered
   from the index without opening the table: your plan must say COVERING INDEX
   idx_loans_copy with SEARCH. The query in the editor is correct and scans.

   *Return: loaned_on, day_type*

## 2 - JSON and dates (2)

json_group_array with DISTINCT and ORDER BY over strftime years, and json_each
over a list of dates with a correlated count beside each.

3. **The years each branch withdrew stock, as JSON** (Q984)

   For each branch that has withdrawn copies, a JSON array of the DISTINCT
   years in which it withdrew them, ascending: strftime for the year of
   withdrawn_on, json_group_array with DISTINCT and an ORDER BY inside its
   parentheses, over the withdrawn copies only.

   *Return: branch_id, years*

4. **Three dates to check, from a JSON list** (Q985)

   Given the JSON list '["2026-01-15", "2026-03-01", "2026-06-30"]': for each
   date, how many loans were DUE that day, and the day of the week as
   strftime's %w gives it. json_each turns the list into rows with a `value`
   column.

   *Return: day, due, weekday*

## 3 - Bare columns and open ends (2)

SQLite's bare-column rule beside a single MAX or MIN, with the WHERE -- NOT
EXISTS, or the two-NULL test -- narrowing the rows BEFORE the aggregate picks
one.

5. **The newest copy nobody has borrowed, per branch** (Q986)

   For each branch: among its copies that have NEVER been loaned, the most
   recently acquired one -- copy_id and acquired_on. NOT EXISTS against loans
   picks the never-loaned copies; MAX(acquired_on) with copy_id as a bare
   column picks the newest.

   *Return: branch_id, copy_id, acquired_on*

6. **Each member's oldest open hold at Northgate** (Q987)

   For each member with an OPEN hold at branch 2 -- fulfilled_on and
   cancelled_on both NULL -- their earliest such hold: member_id, the book,
   and when it was placed. MIN(placed_at) with book_id as a bare column, over
   the open holds only.

   *Return: member_id, book_id, placed_at*

## 4 - Set operations and text (2)

INTERSECT and EXCEPT over computed SUBSTRs, where the order of the two SELECTs
is the question.

7. **First words that fiction and poetry share** (Q988)

   The first words of titles that occur in BOTH fiction and poetry: SUBSTR up
   to the space in each genre's titles, and INTERSECT between the two.

   *Return: first_word*

8. **Member surnames no staff member has** (Q989)

   Surnames -- the part of name after the space -- that some MEMBER has and no
   member of STAFF has, each once: EXCEPT between the two tables' extracted
   surnames.

   *Return: surname*

## 5 - Windows and NULLs (2)

A conditional SUM through a CASE with no ELSE under a running window SUM, and
COALESCE over LAG for the first row.

9. **Unpaid fines mounting up, month by month** (Q990)

   For each month fines were issued: how many of that month's fines are still
   unpaid, and the running total in pence of unpaid fines issued up to and
   including that month. The unpaid amount is a conditional SUM -- a CASE with
   no ELSE, which SUM skips as NULL -- and the running total is a window SUM
   over it.

   *Return: month, unpaid, running_unpaid_pence*

10. **The gaps between one member's loans** (Q991)

    Member 834's loans in date order: loan_id, loaned_on, and the whole number
    of days since their PREVIOUS loan -- 0, not NULL, for the first. LAG gives
    the previous date, julianday the difference, and COALESCE turns the first
    row's NULL into 0.

    *Return: loan_id, loaned_on, gap_days*

## 6 - Recursion and text (2)

A comma list split into rows by SUBSTR and INSTR in a recursive CTE, and quarter
starts stepped by '+3 months' and labelled by printf.

11. **A comma list turned into rows** (Q992)

    Split the text 'fiction,poetry,travel' into one row per genre with a
    recursive CTE -- each step takes the part before the first comma and
    carries the rest forward -- and count the books in each. Append a trailing
    comma to the text first so the last item ends like the others.

    *Return: genre, books*

12. **Six quarters, labelled** (Q993)

    Loans per quarter from 2025Q1 to 2026Q2, labelled like '2025Q1': a
    recursive CTE of quarter starts stepping '+3 months', printf to build the
    label from strftime's year and (month + 2) / 3, and a count of the loans
    from each start up to but not including the next.

    *Return: quarter, loans*

## 7 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A BEFORE UPDATE trigger that reads OLD,
a seeded table then an UPSERT, and a DELETE numbered over the closed holds only.

13. **No renewal once a loan is overdue** (Q994)

    Write a BEFORE UPDATE OF renewals trigger on loans that refuses --
    RAISE(ABORT, ...) -- to raise renewals on a loan whose due_on BEFORE the
    update, OLD.due_on, is earlier than '2026-06-30'. The question then renews
    loan 4107, due 20 June, and loan 156, due 17 July, each by one renewal and
    fourteen days.

    *Checked: the renewals and due_on of both loans*

14. **Opening hours, with one branch different** (Q995)

    Create `branch_hours (branch_id INTEGER PRIMARY KEY, hours TEXT NOT NULL)`
    and fill it for EVERY branch from branches with the JSON '{"sat":
    "09:00-13:00"}' -- INSERT ... SELECT. Then record that Old Town (branch 6)
    opens '10:00-16:00' on Saturdays with an INSERT ... ON CONFLICT
    (branch_id) DO UPDATE, so the same statement would work whether or not the
    row existed.

    *Checked: each branch's Saturday hours, read with json_extract*

15. **One closed hold per member, the latest kept** (Q996)

    Thin the history: for each member, keep only their most recent CLOSED hold
    -- fulfilled or cancelled -- by placed_at, and delete their other closed
    holds. Open holds are not touched. ROW_NUMBER partitioned by member over
    the closed holds, newest first, in a subquery that picks the hold_ids to
    delete.

    *Checked: holds remaining, open holds remaining, and how many members still have more than one closed hold*

# Python

## 1 - Strings (4)

startswith() with a tuple against 'or', islower() against == lower(), chr()
against str(), and find() with a start position.

1. **startswith(tuple): a Leeds or Bradford postcode?** (P251)

   Write a function `is_local(area)` that returns True when the postcode area
   begins with 'LS' or 'BD', using startswith() with a TUPLE of prefixes. No
   import is needed.

   ```
   is_local("BD3") -> True
   is_local("WF1") -> False
   ```

   *Return: True or False.*

2. **islower(): no capitals anywhere** (P252)

   Write a function `all_lower(s)` that returns True when every letter in s is
   lower case and there is at least one letter, using islower(). No import is
   needed.

   ```
   all_lower("ls15") -> True
   all_lower("123") -> False
   ```

   *Return: True or False.*

3. **chr(): the character with a given code** (P253)

   Write a function `letter_from_code(n)` that returns the single character
   whose Unicode code is n, using chr(). No import is needed.

   ```
   letter_from_code(65) -> "A"
   ```

   *Return: a one-character string.*

4. **find(sub, start): the second space** (P254)

   Write a function `second_space(s)` that returns the position of the SECOND
   space in s, or -1 when there is no second space, using find() twice -- the
   second call with a start position just after the first space. No import is
   needed.

   ```
   second_space("a b c") -> 3
   ```

   *Return: an integer.*

## 2 - Numbers (5)

math.factorial(), math.lcm() against a * b, statistics.fmean() against median(),
math.trunc() against floor(), and oct() against hex() -- each import line given
in the prompt.

5. **math.factorial(): n times everything below it** (P255)

   Write a function `factorial(n)` that returns n! -- the product of the whole
   numbers from 1 to n, and 1 for n = 0 -- using math.factorial(). Write
   `import math` as the first line.

   ```
   factorial(5) -> 120
   ```

   *Return: an integer.*

6. **math.lcm(): the smallest shared multiple** (P256)

   Write a function `shared_multiple(a, b)` that returns the smallest positive
   number both a and b divide into, using math.lcm(). Write `import math` as
   the first line.

   ```
   shared_multiple(4, 6) -> 12
   ```

   *Return: an integer.*

7. **statistics.fmean(): the mean, always a float** (P257)

   Write a function `mean_of(values)` that returns the arithmetic mean of a
   non-empty list as a float, using statistics.fmean(). Write `import
   statistics` as the first line.

   ```
   mean_of([1, 2, 3, 4]) -> 2.5
   ```

   *Return: a float.*

8. **math.trunc(): drop the fraction, towards zero** (P258)

   Write a function `whole_part(x)` that returns the integer part of x with
   the fraction simply cut off, so -2.7 becomes -2, using math.trunc(). Write
   `import math` as the first line.

   ```
   whole_part(-2.7) -> -2
   ```

   *Return: an integer.*

9. **oct(): a number in base eight** (P259)

   Write a function `as_octal(n)` that returns the octal form of a non-
   negative integer as a string WITH the 0o prefix, using oct(). No import is
   needed.

   ```
   as_octal(8) -> "0o10"
   ```

   *Return: the string.*

## 3 - Lists (4)

itertools.pairwise() against zip(v, v), heapq.nsmallest() against sorted()[-3:],
max(default=), and itertools.chain(*lists).

10. **itertools.pairwise(): each item with the next** (P260)

    Write a function `neighbours(values)` that returns a list of tuples
    pairing each item with the one after it, using list() over
    itertools.pairwise(). Write `import itertools` as the first line.

    ```
    neighbours([1, 2, 3, 4]) -> [(1, 2), (2, 3), (3, 4)]
    ```

    *Return: the list of tuples.*

11. **heapq.nsmallest(): the three lowest** (P261)

    Write a function `bottom_three(values)` that returns the three smallest
    values, smallest first -- fewer when the list is shorter -- using
    heapq.nsmallest(). Write `import heapq` as the first line.

    ```
    bottom_three([5, 1, 9, 3, 7]) -> [1, 3, 5]
    ```

    *Return: the list.*

12. **max(default=): the largest, or None** (P262)

    Write a function `highest(values)` that returns the largest value in the
    list, or None when the list is empty, using max() with its default=
    argument. No import is needed.

    ```
    highest([4, 2, 9]) -> 9
    highest([]) -> None
    ```

    *Return: the largest value, or None.*

13. **itertools.chain(): several lists as one** (P263)

    Write a function `flattened(lists)` that returns one list holding the
    items of every inner list in order, using list() over
    itertools.chain(*lists) -- the star unpacks the outer list into chain's
    arguments. Write `import itertools` as the first line.

    ```
    flattened([[1, 2], [3], [4, 5]]) -> [1, 2, 3, 4, 5]
    ```

    *Return: the new list.*

## 4 - Sets and dictionaries (2)

popitem() takes the last pair, and >= on sets the right way round.

14. **popitem(): the last pair, taken out** (P264)

    Write a function `last_added(d)` that removes and returns the most
    recently inserted (key, value) pair of a non-empty dictionary as a tuple,
    using popitem(). No import is needed.

    ```
    last_added({"a": 1, "b": 2, "c": 3}) -> ("c", 3)
    ```

    *Return: the tuple.*

15. **>= on sets: does the stock cover the order?** (P265)

    Write a function `covers(stock, wanted)` that returns True when every
    wanted item is in stock, using set() on each and the >= operator --
    superset. No import is needed.

    ```
    covers(["ink", "pen", "paper"], ["pen", "ink"]) -> True
    ```

    *Return: True or False.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,231 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
