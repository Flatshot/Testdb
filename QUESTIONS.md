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

Thirty questions on the repair-depot schema, re-seeded again (SEED 77 -> 113) so
no answer value from the last set carries over. The previous set gave recursion
two questions and it was the tier that hurt; this one spends **six** on it,
ordered so the mechanism builds -- carry a value down, walk the chain upward,
close the hierarchy into pairs, roll a subtree up into a count, and then the
half of recursion that is not a hierarchy at all: generating rows that exist in
no table, so a report can show the bands and months where nothing happened.

The rest holds the breadth of the last set. Two questions still drill the bare
column under `GROUP BY`, now in its arithmetic form -- `SUM(h) * rate` rather
than `SUM(h * rate)` -- which is where it actually cost answers.
Generated from `exercises.py` - `check_questions.py` verifies the two agree.

| ID | Concept | Question | In GUI | Drills |
|----|---------|----------|--------|--------|
| Q162 | R1 recursive CTE | The whole chain, written out | ex 1 | Recursive CTEs |
| Q163 | R1 recursive CTE | Everyone above Nadia Kaur | ex 2 | Recursive CTEs |
| Q164 | R1 recursive CTE | Every manager, everyone under them | ex 3 | Recursive CTEs |
| Q165 | R1 recursive CTE | How many people are under you | ex 4 | Recursive CTEs |
| Q166 | R2 recursive series | Score bands, including the empty ones | ex 5 | Recursive CTEs |
| Q167 | R2 recursive series | Critical months, including the quiet ones | ex 6 | Recursive CTEs |
| Q168 | S1 set operations | Stocked in Leeds, not in Coventry | ex 7 | Set operations |
| Q169 | S1 set operations | Both kinds of contract | ex 8 | Set operations |
| Q170 | X1 subqueries/EXISTS | Machines nobody has touched | ex 9 | Subqueries & EXISTS |
| Q171 | X1 subqueries/EXISTS | Never failed an inspection | ex 10 | Subqueries & EXISTS |
| Q172 | X2 correlated subquery | Costlier than its category average | ex 11 | Subqueries & EXISTS |
| Q173 | A1 conditional aggregation | Counted and uncounted stock | ex 12 | Conditional aggregation |
| Q174 | C9 integer division | Close rate by priority | ex 13 | Conditional aggregation |
| Q175 | A1 conditional aggregation | Every status in one row | ex 14 | Conditional aggregation |
| Q176 | D1 dates & gaps | The jobs that dragged | ex 15 | Dates & gaps |
| Q177 | D2 dates & NULL | Out of warranty when it broke | ex 16 | Dates & gaps |
| Q178 | D1 dates & gaps | How long invoices take to pay | ex 17 | Dates & gaps |
| Q179 | W1 window frames | Invoiced so far this year | ex 18 | Window frames |
| Q180 | C3 PARTITION BY | Ranked inside your own depot | ex 19 | Window frames |
| Q181 | C3 PARTITION BY | Share of the category | ex 20 | Window frames |
| Q182 | W1 window frames | Against the best in the depot | ex 21 | Window frames |
| Q183 | B1 silent sampling | What the labour cost each depot | ex 22 | Silent sampling |
| Q184 | B1 silent sampling | Spend by category, after discount | ex 23 | Silent sampling |
| Q185 | J1 self-joins | Same region, same tier | ex 24 | Self-joins |
| Q186 | J1 self-joins | Same depot, same certification | ex 25 | Self-joins |
| Q187 | C2 grain | Parts and labour on one job | ex 26 | Grain |
| Q188 | C2 grain | Contracts and sites per customer | ex 27 | Grain |
| Q189 | C7 NULL | Still running, or merely undated | ex 28 | NULLs |
| Q190 | C7 NULL | Certified, uncertified, unknown | ex 29 | NULLs |
| Q191 | general | Money still owed, by region | ex 30 | General |

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
| Q072 | - | Freight per order | - | retired |
| Q073 | - | Stock per product across warehouses | - | retired |
| Q074 | - | Revenue and freight side by side | - | retired |
| Q075 | - | Units sold against units returned | - | retired |
| Q076 | - | Delivered or still in transit | - | retired |
| Q077 | - | Average days in transit | - | retired |
| Q078 | - | Value of counted stock | - | retired |
| Q079 | - | Quantities matching no reorder level | - | retired |
| Q080 | - | Pricey shipments for their carrier | - | retired |
| Q081 | - | Busier than the average warehouse | - | retired |
| Q082 | - | Categories with above-average margin | - | retired |
| Q083 | - | Shipment beside its order's freight | - | retired |
| Q084 | - | Share of a product's stock | - | retired |
| Q085 | - | First shipment of each order | - | retired |
| Q086 | - | Warehouses stocking each product | - | retired |
| Q087 | - | Dispatched versus delivered | - | retired |
| Q088 | - | Warehouse activity | - | retired |
| Q089 | - | Margin percentage | - | retired |
| Q090 | - | Freight as a share of revenue | - | retired |
| Q091 | - | Return rate by product | - | retired |
| Q092 | - | Delivery rate by carrier | - | retired |
| Q093 | - | Capacity used | - | retired |
| Q094 | - | Orders where freight bites | - | retired |
| Q095 | - | Large established warehouses | - | retired |
| Q096 | - | Carriers by freight spend | - | retired |
| Q097 | - | Why things come back | - | retired |
| Q098 | - | Loyalty programme uptake | - | retired |
| Q099 | - | Below the reorder line | - | retired |
| Q100 | - | Split orders | - | retired |
| Q101 | - | Longest outstanding deliveries | - | retired |
| Q102 | - | What a job actually cost | - | retired |
| Q103 | - | Labour's share of the bill | - | retired |
| Q104 | - | Parts count and hours together | - | retired |
| Q105 | - | Hours, and who signed the job off | - | retired |
| Q106 | - | The missing SUM | - | retired |
| Q107 | - | Do not go back to the well | - | retired |
| Q108 | - | Three children, one job | - | retired |
| Q109 | - | Contracts and callouts | - | retired |
| Q110 | - | Counting down a chain | - | retired |
| Q111 | - | Stock on hand per part | - | retired |
| Q112 | - | Invoice against actual cost | - | retired |
| Q113 | - | Technician workload | - | retired |
| Q114 | - | Depot stock and staff | - | retired |
| Q115 | - | Cost per hour on the job | - | retired |
| Q116 | - | Busiest machines | - | retired |
| Q117 | - | Each visit against the job total | - | retired |
| Q118 | - | First visit to each job | - | retired |
| Q119 | - | Running spend per depot | - | retired |
| Q120 | - | Jobs that ran long | - | retired |
| Q121 | - | Customers worth chasing | - | retired |
| Q122 | - | Carry it through the wall | - | retired |
| Q123 | - | Inspected, or not | - | retired |
| Q124 | - | Scored and unscored | - | retired |
| Q125 | - | Slow to answer | - | retired |
| Q126 | - | Never certified | - | retired |
| Q127 | - | Parts nobody has fitted | - | retired |
| Q128 | - | Average parts per job | - | retired |
| Q129 | - | Stock cover against reorder level | - | retired |
| Q130 | - | Who reports to whom | - | retired |
| Q131 | - | How long jobs stay open | - | retired |
| Q132 | S1 set operations | Parts only the urgent jobs need | - | retired |
| Q133 | S1 set operations | Two kinds of orphan | - | retired |
| Q134 | S1 set operations | Everything that happened, by month | - | retired |
| Q135 | R1 recursive CTE | How deep in the chain | - | retired |
| Q136 | R1 recursive CTE | Who is at the top of your chain | - | retired |
| Q137 | X1 subqueries/EXISTS | Nobody reports to them | - | retired |
| Q138 | X1 subqueries/EXISTS | Above your own priority's average | - | retired |
| Q139 | X1 subqueries/EXISTS | Customers with something overdue | - | retired |
| Q140 | A1 conditional aggregation | Stock policy at a glance | - | retired |
| Q141 | A1 conditional aggregation | Job status by priority, side by side | - | retired |
| Q142 | A1 conditional aggregation | Critical hours versus the rest | - | retired |
| Q143 | D1 dates & gaps | Work opened by month | - | retired |
| Q144 | D1 dates & gaps | Days between callouts | - | retired |
| Q145 | D1 dates & gaps | Slow payers | - | retired |
| Q146 | D1 dates & gaps | Month on month | - | retired |
| Q147 | W1 window frames | Quartiles of workload | - | retired |
| Q148 | W1 window frames | Three-month rolling average | - | retired |
| Q149 | W1 window frames | The latest job on each machine | - | retired |
| Q150 | W1 window frames | Top two parts in each category | - | retired |
| Q151 | B1 silent sampling | High scores per verdict | - | retired |
| Q152 | B1 silent sampling | The newest site of each customer | - | retired |
| Q153 | B1 silent sampling | Longest-serving technician per depot | - | retired |
| Q154 | J1 self-joins | Depot colleagues | - | retired |
| Q155 | J1 self-joins | Rival sites in one city | - | retired |
| Q156 | C2 grain | Parts and inspections on one job | - | retired |
| Q157 | C2 grain | Regions, customers and depots | - | retired |
| Q158 | C7 NULL | Expired, not merely unknown | - | retired |
| Q159 | C7 NULL | Response times by account tier | - | retired |
| Q160 | general | Stock value by region | - | retired |
| Q161 | general | Oldest jobs still open | - | retired |

## History

- **Q001-Q041** the original breadth-first set (2026-08-24). Retired same day.
- **Q042-Q071** first pass against `sql-concepts-review.html`, on the ordering and
  payments tables. Retired when the schema gained the fulfilment side.
- **Q072-Q101** second pass against the review, on warehouses, inventory,
  shipments and returns. Retired when the schema moved to the repair depot.
- **Q102-Q131** grain-focused set on the repair-depot schema; all 30 solved,
  then retired. Fifteen of them drilled fan-out in five disguises.
- **Q132-Q161** current set, same schema re-seeded (SEED 41 -> 77) so no answer
  value carries over. Deliberately broad rather than deep: 3 set operations,
  2 recursive CTEs, 3 subquery/EXISTS, 3 conditional aggregation, 4 dates and
  gaps, 4 window frames, 3 silent sampling, 2 self-joins, 2 grain, 2 NULLs,
  2 general.
  C8 (alias scope) still has no question: SQLite accepts a SELECT alias even in
  `WHERE`, so the engine cannot enforce the rule. It is covered as prose in
  PRACTICE.md instead.
