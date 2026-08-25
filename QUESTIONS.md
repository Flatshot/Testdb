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
`sql-concepts-review.html`, weighted by how often each one occurred, and built on
the fulfilment tables: warehouses, inventory, shipments and returns. `Concept`
maps to that document's numbered sections. Generated from `exercises.py` -
`check_questions.py` verifies the two agree.

| ID | Concept | Question | In GUI | Drills |
|----|---------|----------|--------|--------|
| Q072 | C2 grain | Freight per order | ex 1 | Grain |
| Q073 | C2 grain | Stock per product across warehouses | ex 2 | Grain |
| Q074 | C2 grain | Revenue and freight side by side | ex 3 | Grain |
| Q075 | C2 grain | Units sold against units returned | ex 4 | Grain |
| Q076 | C7 NULL | Delivered or still in transit | ex 5 | NULLs |
| Q077 | C7 NULL | Average days in transit | ex 6 | NULLs |
| Q078 | C7 NULL | Value of counted stock | ex 7 | NULLs |
| Q079 | C7 NULL | Quantities matching no reorder level | ex 8 | NULLs |
| Q080 | C1 aggregates in WHERE | Pricey shipments for their carrier | ex 9 | Aggregates in WHERE |
| Q081 | C1 aggregates in WHERE | Busier than the average warehouse | ex 10 | Aggregates in WHERE |
| Q082 | C1 aggregates in WHERE | Categories with above-average margin | ex 11 | Aggregates in WHERE |
| Q083 | C3 PARTITION BY | Shipment beside its order's freight | ex 12 | Window vs GROUP BY |
| Q084 | C3 PARTITION BY | Share of a product's stock | ex 13 | Window vs GROUP BY |
| Q085 | C3 PARTITION BY | First shipment of each order | ex 14 | Window vs GROUP BY |
| Q086 | C5 COUNT(*) vs COUNT(col) | Warehouses stocking each product | ex 15 | COUNT |
| Q087 | C5 COUNT(*) vs COUNT(col) | Dispatched versus delivered | ex 16 | COUNT |
| Q088 | C5 COUNT(*) vs COUNT(col) | Warehouse activity | ex 17 | COUNT |
| Q089 | C6 alias vs formula | Margin percentage | ex 18 | Alias vs formula |
| Q090 | C6 alias vs formula | Freight as a share of revenue | ex 19 | Alias vs formula |
| Q091 | C6 alias vs formula | Return rate by product | ex 20 | Alias vs formula |
| Q092 | C9 integer division | Delivery rate by carrier | ex 21 | Integer division |
| Q093 | C9 integer division | Capacity used | ex 22 | Integer division |
| Q094 | C4 CTE is a wall | Orders where freight bites | ex 23 | CTE scope |
| Q095 | general | Large established warehouses | ex 24 | General |
| Q096 | general | Carriers by freight spend | ex 25 | General |
| Q097 | general | Why things come back | ex 26 | General |
| Q098 | general | Loyalty programme uptake | ex 27 | General |
| Q099 | general | Below the reorder line | ex 28 | General |
| Q100 | general | Split orders | ex 29 | General |
| Q101 | general | Longest outstanding deliveries | ex 30 | General |

## Retired

Asked previously and since replaced. **Kept so they are never regenerated** -
they still count as asked.

| ID | Concept | Question | In GUI | Status |
|----|---------|----------|--------|--------|
| Q042 | C2 grain | Revenue per category | - | retired |
| Q043 | C2 grain | Headcount and payroll by department | - | retired |
| Q044 | C2 grain | Settled money per customer | - | retired |
| Q045 | C2 grain | Monthly orders and distinct buyers | - | retired |
| Q046 | C7 NULL | Two averages over a nullable column | - | retired |
| Q047 | C7 NULL | Keeping the outer join | - | retired |
| Q048 | C7 NULL | Employees who manage nobody | - | retired |
| Q049 | C7 NULL | Total compensation | - | retired |
| Q050 | C1 aggregates in WHERE | Above-average payments | - | retired |
| Q051 | C1 aggregates in WHERE | Busiest sales rep | - | retired |
| Q052 | C1 aggregates in WHERE | Categories rated above the overall mean | - | retired |
| Q053 | C3 PARTITION BY | Line detail beside the order total | - | retired |
| Q054 | C3 PARTITION BY | Running total per customer | - | retired |
| Q055 | C3 PARTITION BY | Previous review for the same product | - | retired |
| Q056 | C5 COUNT(*) vs COUNT(col) | Orders per customer, including none | - | retired |
| Q057 | C5 COUNT(*) vs COUNT(col) | Paid payments per method | - | retired |
| Q058 | C5 COUNT(*) vs COUNT(col) | How complete is each product's feedback | - | retired |
| Q059 | C6 alias vs formula | Gross, discount, and net | - | retired |
| Q060 | C6 alias vs formula | Conversion rate by country | - | retired |
| Q061 | C6 alias vs formula | Change in paid volume | - | retired |
| Q062 | C9 integer division | Percentage of orders shipped | - | retired |
| Q063 | C9 integer division | Mean weight per weighed product | - | retired |
| Q064 | C4 CTE is a wall | Each customer's second-biggest order | - | retired |
| Q065 | general | Settled money by method | - | retired |
| Q066 | general | Heavy items | - | retired |
| Q067 | general | Paid on the day of order | - | retired |
| Q068 | general | Most reviewed products | - | retired |
| Q069 | general | Customers with a refund | - | retired |
| Q070 | general | Hired before their manager | - | retired |
| Q071 | general | Well-reviewed categories | - | retired |
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

- **Q001-Q041** the original breadth-first set (2026-08-24). Retired same day.
- **Q042-Q071** first pass against `sql-concepts-review.html`, on the ordering and
  payments tables. Retired when the schema gained the fulfilment side.
- **Q072-Q101** current set, on warehouses, inventory, shipments and returns.
  C8 (alias scope) still has no question: SQLite accepts a SELECT alias even in
  `WHERE`, so the engine cannot enforce the rule. It is covered as prose in
  PRACTICE.md instead.

