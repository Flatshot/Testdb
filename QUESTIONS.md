# Question ledger

Every practice question that has been asked, so new ones don't repeat old ones.
**Check this file before authoring any new question.** Add a row for each new
question and give it the next free `Q` id.

## What counts as a duplicate

A new question is a **duplicate** if it targets the same SQL concept against the
same entity and produces the same shape of answer. Changing only a constant is a
duplicate, not a new question:

- top 2 per category -> top 3 per category
- average price above $75 -> above $100
- orders in March -> orders in April

A new question is an acceptable **variation** if it changes at least one of:

- **the entity** - top products by revenue -> top *customers* by revenue
- **the mechanism** - correlated subquery -> window function
- **the combination** - joins two concepts that have not been combined before

Similar questions are fine and useful. Re-asks are not.

## Live set

Thirty questions aimed at the nine recurring mistakes in
`sql-concepts-review.html`, weighted by how often each one occurred. `Concept`
maps to that document's numbered sections. Generated from `exercises.py` -
`check_questions.py` verifies the two agree.

| ID | Concept | Question | In GUI | Drills |
|----|---------|----------|--------|--------|
| Q042 | C2 grain | Revenue per category | ex 1 | Grain |
| Q043 | C2 grain | Headcount and payroll by department | ex 2 | Grain |
| Q044 | C2 grain | Settled money per customer | ex 3 | Grain |
| Q045 | C2 grain | Monthly orders and distinct buyers | ex 4 | Grain |
| Q046 | C7 NULL | Two averages over a nullable column | ex 5 | NULLs |
| Q047 | C7 NULL | Keeping the outer join | ex 6 | NULLs |
| Q048 | C7 NULL | Employees who manage nobody | ex 7 | NULLs |
| Q049 | C7 NULL | Total compensation | ex 8 | NULLs |
| Q050 | C1 aggregates in WHERE | Above-average payments | ex 9 | Aggregates in WHERE |
| Q051 | C1 aggregates in WHERE | Busiest sales rep | ex 10 | Aggregates in WHERE |
| Q052 | C1 aggregates in WHERE | Categories rated above the overall mean | ex 11 | Aggregates in WHERE |
| Q053 | C3 PARTITION BY | Line detail beside the order total | ex 12 | Window vs GROUP BY |
| Q054 | C3 PARTITION BY | Running total per customer | ex 13 | Window vs GROUP BY |
| Q055 | C3 PARTITION BY | Previous review for the same product | ex 14 | Window vs GROUP BY |
| Q056 | C5 COUNT(*) vs COUNT(col) | Orders per customer, including none | ex 15 | COUNT |
| Q057 | C5 COUNT(*) vs COUNT(col) | Paid payments per method | ex 16 | COUNT |
| Q058 | C5 COUNT(*) vs COUNT(col) | How complete is each product's feedback | ex 17 | COUNT |
| Q059 | C6 alias vs formula | Gross, discount, and net | ex 18 | Alias vs formula |
| Q060 | C6 alias vs formula | Conversion rate by country | ex 19 | Alias vs formula |
| Q061 | C6 alias vs formula | Change in paid volume | ex 20 | Alias vs formula |
| Q062 | C9 integer division | Percentage of orders shipped | ex 21 | Integer division |
| Q063 | C9 integer division | Mean weight per weighed product | ex 22 | Integer division |
| Q064 | C4 CTE is a wall | Each customer's second-biggest order | ex 23 | CTE scope |
| Q065 | general | Settled money by method | ex 24 | General |
| Q066 | general | Heavy items | ex 25 | General |
| Q067 | general | Paid on the day of order | ex 26 | General |
| Q068 | general | Most reviewed products | ex 27 | General |
| Q069 | general | Customers with a refund | ex 28 | General |
| Q070 | general | Hired before their manager | ex 29 | General |
| Q071 | general | Well-reviewed categories | ex 30 | General |

## Retired

Asked previously, removed from the GUI and PRACTICE.md when the set was
refocused on the nine weak concepts. **Kept so they are never regenerated** -
they still count as asked.

| ID | Concept | Question | In GUI | Status |
|----|---------|----------|--------|--------|
| Q001 | - | Products above a price threshold | - | retired |
| Q002 | - | Customers in a set of countries | - | retired |
| Q003 | - | Discontinued or out-of-stock products | - | retired |
| Q004 | - | Most recently hired employees | - | retired |
| Q005 | - | Product name substring search | - | retired |
| Q006 | - | Product with its category and supplier | - | retired |
| Q007 | - | Orders in a date window, with customer and rep | - | retired |
| Q008 | - | Employee with manager, CEO included | - | retired |
| Q009 | - | Customers who never ordered | - | retired |
| Q010 | - | Products never ordered | - | retired |
| Q011 | - | Product count per category | - | retired |
| Q012 | - | Salary avg/min/max per department | - | retired |
| Q013 | - | Top 10 customers by shipped revenue | - | retired |
| Q014 | - | Customers above an order-count threshold | - | retired |
| Q015 | - | Categories above an average-price threshold | - | retired |
| Q016 | - | Per-supplier product and discontinued counts | - | retired |
| Q017 | - | Orders with no ship date | - | retired |
| Q018 | - | Average rating from commented reviews only | - | retired |
| Q019 | - | `COUNT(*)` vs `COUNT(column)` | - | retired |
| Q020 | - | Manager name with NULL substituted | - | retired |
| Q021 | - | Products above their own category average | - | retired |
| Q022 | - | Single highest-value shipped order | - | retired |
| Q023 | - | Customers above average lifetime spend | - | retired |
| Q024 | - | Most expensive product per category | - | retired |
| Q025 | - | Orders containing a given category | - | retired |
| Q026 | - | Products ranked by revenue | - | retired |
| Q027 | - | Running cumulative monthly revenue | - | retired |
| Q028 | - | Order value vs that customer's average | - | retired |
| Q029 | - | Top N products per category | - | retired |
| Q030 | - | Month-over-month revenue change | - | retired |
| Q031 | - | Days between a customer's consecutive orders | - | retired |
| Q032 | - | Orders per month for a year | - | retired |
| Q033 | - | Average days from order to shipment, per rep | - | retired |
| Q034 | - | Employees past a tenure threshold | - | retired |
| Q035 | - | Customers ordering soon after signup | - | retired |
| Q036 | - | Customer countries absent from supplier countries | - | retired |
| Q037 | - | Low-rated products that still sell well | - | retired |
| Q038 | - | Top rep by revenue in each quarter | - | retired |
| Q039 | - | Per-customer first/last order, count, spend | - | retired |
| Q040 | - | 5-star reviewers who never bought elsewhere in that category | - | retired |
| Q041 | - | Bottom 3 products per supplier by revenue | - | retired |

## History

- **Q001-Q041** seeded from the original breadth-first question set (2026-08-24),
  retired the same day.
- **Q042-Q071** authored against `sql-concepts-review.html`, targeting the nine
  recurring mistakes. C8 (alias scope) has no question: SQLite accepts a SELECT
  alias even in `WHERE`, so the engine cannot enforce the rule. It is covered as
  prose in PRACTICE.md instead.

