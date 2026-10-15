# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
ninth set on this schema and a step up: every question combines TWO tools
the earlier sets taught separately, and the three writable questions each
take two steps. **Fifteen Python** functions of two or three tools each,
with every tool named in the prompt.

| Stage | SQL questions |
|---|---|
| 1 - Windows over CTEs | 1-3 |
| 2 - EXISTS, CASE and HAVING | 4-6 |
| 3 - Recursion meets intervals | 7-8 |
| 4 - JSON in aggregates | 9-10 |
| 5 - Text with aggregation | 11-12 |
| 6 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Strings | 1-5 |
| 2 - Numbers and dates | 6-8 |
| 3 - Lists | 9-13 |
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

**Driver statements.** Question 13 runs two inserts of its own *after* your
script -- a copy that is out and one that is not -- and question 15 runs an
UPDATE against your view. Question 14 is graded on what your script leaves
behind.

| # | Construct |
|---|---|
| 13 | `BEFORE INSERT ON loans WHEN EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = NEW.copy_id AND l.returned_on IS NULL)` |
| 14 | `WITH ranked AS (SELECT ..., ROW_NUMBER() OVER (...) ...) UPDATE loans SET ... WHERE loan_id IN (SELECT ... WHERE rn <= 5)` |
| 15 | `CREATE VIEW member_contact ...; CREATE TRIGGER ... INSTEAD OF UPDATE OF area ON member_contact BEGIN UPDATE members ... END` |

## Things the data does on purpose

- **108 copies have never been loaned**, the count question 4's SUM
  of an EXISTS reaches and a join to loans cannot.
- **719 members owe a fine, and every one of them has borrowed** --
  so question 5's CASE must test 'debtor' before 'borrower'.
- **127 books are at three or more branches but not Central;
  256 if Central's copies are filtered out first** -- question
  6's HAVING against a WHERE.
- **The heaviest borrower has 237 loans**, which is why question
  2's top quartile runs from 17 into the hundreds.
- **685 loans are still out at the end of the data**, the figure question
  7's June 2026 row shows only when COALESCE supplies the open end.
- **24 author surnames are shared**, and two authors are both
  called Priya Achebe -- question 12 groups by the surname, not the name.
- **Copy 4 is out and copy 1 is on the shelf after 14 loans**, the
  two question 13's trigger must tell apart.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Each question here combines two or three tools, and
the prompt names every one of them.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Windows over CTEs (3)

A CTE does the grouping, a window ranks or tiles the grouped rows, and the final
SELECT filters on the result: DENSE_RANK partitioned by year, NTILE into
quartiles, LAG then LIMIT 1.

1. **Each month's rank within its year** (Q967)

   For each month of the data: its loans, and its rank within ITS YEAR by
   loans, 1 for the year's busiest month. A CTE of loans per month that also
   carries the year, then DENSE_RANK partitioned by that year.

   *Return: month, loans, rank_in_year*

2. **Borrowers in quartiles** (Q968)

   Split the borrowers -- members with at least one loan -- into four equal
   groups by loan count, quartile 1 the LIGHTEST readers: for each quartile,
   the loans its members made in all, and the smallest and largest loan count
   in it. A CTE of loans per member, NTILE(4) over it, then a GROUP BY the
   tile.

   *Return: quartile, loans, min_loans, max_loans*

3. **The biggest jump in a day** (Q969)

   The 2026 day whose loan count rose most over the previous day: the day, its
   loans and the rise. A CTE of loans per day over ALL the data, a second with
   LAG for the change, then the largest change among 2026's days -- ORDER BY
   and LIMIT 1, ties to the earlier day.

   *Return: day, loans, rise*

## 2 - EXISTS, CASE and HAVING (3)

SUM of an EXISTS to count copies rather than loans, a CASE whose WHENs are
EXISTS tests in the right order, and two HAVING conditions where a WHERE would
hide the thing being excluded.

4. **Copies that have never gone out** (Q970)

   For each branch: its copies, how many of them have been loaned at least
   once, and how many never. The 'at least once' is an EXISTS per copy, summed
   -- a loan join would count loans, not copies.

   *Return: branch_id, copies, loaned_ever, never*

5. **Debtor, borrower or lapsed** (Q971)

   Put every member in one class and count each: 'debtor' if they have an
   UNPAID fine; otherwise 'borrower' if they have any loan; otherwise
   'lapsed'. A CASE whose WHENs are EXISTS tests, in that order.

   *Return: class, members*

6. **Spread out, but not at Central** (Q972)

   Books with copies at three or more DIFFERENT branches but no copy at
   Central (branch 1): book_id and the number of branches. Both conditions are
   about the book's whole set of copies, so both are HAVING -- a WHERE
   branch_id <> 1 would hide Central's copies rather than exclude the book.

   *Return: book_id, branches*

## 3 - Recursion meets intervals (2)

A recursive calendar of month ends and one of days, each with a correlated
interval test that supplies the open end.

7. **Loans open at each month's end** (Q973)

   For each month from 2025-01 to 2026-06, how many loans were OUT on the last
   day of the month: started on or before it, and not returned by it -- NULL
   returned_on means still out. A recursive CTE of month starts, date(first,
   '+1 month', '-1 day') for the last day, and the interval test with
   COALESCE.

   *Return: month_start, open_at_end*

8. **Old Town's copies out, day by day** (Q974)

   For every day of June 2026, how many of branch 6's copies were out on loan
   that day -- loaned on or before the day and not back before it. A recursive
   CTE of days, and per day a count over loans joined to copies, with the open
   end supplied.

   *Return: day, copies_out*

## 4 - JSON in aggregates (2)

json_object inside json_group_array over a grouped CTE, and a ranked CTE
filtered to its top three and packed into an array.

9. **Each genre's stock by condition, as JSON** (Q975)

   For each genre, ONE JSON array of objects, one object per condition in
   alphabetical order, each with keys condition and copies: a CTE counting
   copies per genre and condition, then json_group_array of a json_object,
   with ORDER BY condition inside the json_group_array.

   *Return: genre, stock*

10. **The three most borrowed titles per genre, as a list** (Q976)

    For each genre, a JSON array of its three most borrowed titles, most
    borrowed first -- ties by lower book_id. A CTE that counts loans per book
    and numbers the books within their genre by ROW_NUMBER, then
    json_group_array of the titles numbered 3 or less, ordered by that number.

    *Return: genre, top3*

## 5 - Text with aggregation (2)

GROUP_CONCAT DISTINCT over an extracted surname, and GROUP BY an extracted
surname with a HAVING on the group.

11. **The surnames at each branch, once each** (Q977)

    For each branch, the DISTINCT surnames of its staff -- the part of name
    after the space -- joined into one comma-separated string in alphabetical
    order. GROUP_CONCAT(DISTINCT ... ORDER BY ...) over a SUBSTR; two
    colleagues who share a surname contribute it once.

    *Return: branch_id, surnames*

12. **Authors who share a surname** (Q978)

    Surnames held by MORE THAN ONE author: the surname, how many authors have
    it, and their full names joined with ', ' in alphabetical order. The
    surname is a SUBSTR from INSTR; group by that expression and filter the
    groups in HAVING.

    *Return: surname, authors, names*

## 6 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger whose WHEN is an interval
EXISTS, a ROW_NUMBER CTE feeding an UPDATE, and a view made writable by an
INSTEAD OF trigger.

13. **One loan at a time per copy** (Q979)

    Write a BEFORE INSERT trigger on loans that refuses -- RAISE(ABORT, ...)
    -- a loan of a copy that is ALREADY OUT: a loan of the same copy with
    returned_on NULL exists. The question then lends copy 4, which is out, and
    copy 1, which is on the shelf.

    *Checked: which of the two loans exist*

14. **Grace for the five most overdue** (Q980)

    The five loans that are furthest past due on 2026-06-30 -- still out,
    earliest due_on first, ties by lower loan_id -- get one more renewal: set
    renewals to 2 and push due_on fourteen days on. A CTE with ROW_NUMBER
    picks them, and the UPDATE's WHERE is an IN over the CTE.

    *Checked: the renewals and due_on of the five*

15. **A view you can write to** (Q981)

    Create a view `member_contact (member_id, name, area)` over members, with
    area being postcode_area -- then make it UPDATABLE: an INSTEAD OF UPDATE
    OF area trigger on the view that writes NEW.area into
    members.postcode_area for the row whose member_id is OLD.member_id. The
    question then runs UPDATE member_contact SET area = 'LS1' WHERE member_id
    = 3.

    *Checked: member 3's postcode_area*

# Python

## 1 - Strings (5)

split/join/title to tidy a name, split/comprehension/join/upper for initials,
Counter and most_common after lower(), alignment specs in one f-string, and
lstrip/float/round where int() would truncate.

1. **A name tidied up** (P236)

   Write a function `tidy_name(s)` that returns the name with extra spaces
   removed -- one space between words, none at the ends -- and each word
   capitalised. Tools: split() with no argument to break on any whitespace, "
   ".join() to put the words back, and title() for the capitals.

   ```
   tidy_name("  aisha   ekwueme ") -> "Aisha Ekwueme"
   ```

   *Return: the new string.*

2. **Initials from a full name** (P237)

   Write a function `initials(name)` that returns the first letter of each
   word, upper case, run together. Tools: split() to get the words, a
   generator or list comprehension taking w[0] from each, "".join() to combine
   them, and upper().

   ```
   initials("aisha ekwueme") -> "AE"
   ```

   *Return: the string.*

3. **The two commonest words** (P238)

   Write a function `top_two_words(text)` that returns a list of the two most
   frequent words as (word, count) tuples, commonest first, counting words
   regardless of case and reporting them in lower case. Tools: lower(),
   split(), collections.Counter and its most_common(2). Remember the import.

   ```
   top_two_words("the cat and the dog and the bird") -> [("the", 3), ("and", 2)]
   ```

   *Return: the list of tuples.*

4. **A line of a price list** (P239)

   Write a function `price_line(label, pence)` that returns the label padded
   on the right to 18 characters followed by the amount in pounds, right-
   aligned in 8 characters with two decimals. Tools: an f-string with the :<18
   spec for the label and the :>8.2f spec for pence / 100.

   ```
   price_line("Fine", 220) -> "Fine                  2.20"
   ```

   *Return: the string.*

5. **Pounds in text to pence** (P240)

   Write a function `pence_from_text(s)` that turns an amount written like
   '£12.40' into whole pence. Tools: lstrip('£') to drop the sign, float() to
   read the number, multiply by 100, and round() -- NOT int() -- to get back
   to a whole number.

   ```
   pence_from_text("£12.40") -> 1240
   ```

   *Return: an integer.*

## 2 - Numbers and dates (3)

sum/len/round with a decimal count, fromisoformat then strftime, and date
subtraction with abs.

6. **An average to one decimal** (P241)

   Write a function `average(values)` that returns the mean of a non-empty
   list rounded to one decimal. Tools: sum(), len() and round() with a second
   argument.

   ```
   average([1, 2]) -> 1.5
   ```

   *Return: a float.*

7. **What day of the week a date falls on** (P242)

   Write a function `weekday_name(date_str)` that returns the full English
   weekday name of a 'YYYY-MM-DD' date. Tools: datetime.date.fromisoformat()
   to parse it, then strftime('%A') for the name. Remember the import.

   ```
   weekday_name("2026-06-30") -> "Tuesday"
   ```

   *Return: the string.*

8. **Days between two dates, either way round** (P243)

   Write a function `days_between(a, b)` that returns the number of days
   between two 'YYYY-MM-DD' dates as a non-negative integer, whichever is
   earlier. Tools: date.fromisoformat() on each, subtraction of the two dates
   giving a timedelta whose .days is the count, and abs(). Remember the
   import.

   ```
   days_between("2026-06-30", "2026-06-01") -> 29
   ```

   *Return: an integer.*

## 3 - Lists (5)

min and max with key=len, strip/int in a set comprehension then sorted, a lambda
tuple key, dict.fromkeys for an ordered dedupe, and range with a step feeding
slices.

9. **The shortest and the longest** (P244)

   Write a function `shortest_and_longest(words)` that returns a tuple of the
   shortest word and the longest word in a non-empty list, the first of each
   when lengths tie. Tools: min() and max(), both with key=len, packed into a
   tuple.

   ```
   shortest_and_longest(["pen", "paper", "ink"]) -> ("pen", "paper")
   ```

   *Return: the tuple.*

10. **Ids typed by hand, cleaned up** (P245)

    Write a function `clean_ids(strings)` that turns a list of id strings with
    stray spaces and leading zeros into a sorted list of distinct integers.
    Tools: strip() and int() on each string inside a SET comprehension, then
    sorted() over the set.

    ```
    clean_ids([" 12", "7 ", "12", "003"]) -> [3, 7, 12]
    ```

    *Return: the list.*

11. **Shortest first, then alphabetical** (P246)

    Write a function `by_length_then_alpha(words)` that returns the words
    sorted by length, and alphabetically among words of the same length.
    Tools: sorted() with key=lambda w: (len(w), w) -- a tuple key, compared
    item by item.

    ```
    by_length_then_alpha(["bb", "aa", "c"]) -> ["c", "aa", "bb"]
    ```

    *Return: the new list.*

12. **Duplicates dropped, order kept** (P247)

    Write a function `dedupe(values)` that returns the values with repeats
    removed, keeping the FIRST occurrence of each and the original order.
    Tools: dict.fromkeys() -- a dict keeps insertion order and cannot repeat a
    key -- and list() over it.

    ```
    dedupe(["b", "a", "b", "c", "a"]) -> ["b", "a", "c"]
    ```

    *Return: the new list.*

13. **A list cut into chunks** (P248)

    Write a function `chunks(values, n)` that returns a list of lists, each
    holding the next n values, the last one shorter if the count does not
    divide. Tools: range() from 0 to len(values) with a step of n, a slice
    values[i:i + n] for each start, inside a list comprehension.

    ```
    chunks([1, 2, 3, 4, 5], 2) -> [[1, 2], [3, 4], [5]]
    ```

    *Return: the list of lists.*

## 4 - Dictionaries (2)

keys() | keys() with get(k, 0) in a comprehension, and set(values()) with a
nested comprehension to group keys by value.

14. **Two tallies added together** (P249)

    Write a function `merge_counts(a, b)` that returns a new dict with every
    key from either tally and the SUM of its counts from both. Tools: a.keys()
    | b.keys() for the set of all keys, get(k, 0) on each dict, and a dict
    comprehension over the keys.

    ```
    merge_counts({"a": 1, "b": 2}, {"b": 3, "c": 4}) -> {"a": 1, "b": 5, "c": 4}
    ```

    *Return: the new dictionary.*

15. **Grouped by value** (P250)

    Write a function `keys_by_value(d)` that returns a dict mapping each
    distinct VALUE of d to the sorted list of the keys that have it. Tools:
    set(d.values()) for the distinct values, a dict comprehension over them,
    and inside it sorted() of a comprehension picking the keys k where d[k]
    equals the value.

    ```
    keys_by_value({"a": 1, "b": 2, "c": 1}) -> {1: ["a", "c"], 2: ["b"]}
    ```

    *Return: the new dictionary.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,201 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
