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

Thirty questions on the college schema, re-seeded and **scaled up**
(SEED 293 -> 329): 4,000 students, 774 sections, 67,000 enrolments, 7,800
payments. Same tables, two orders of magnitude more rows.

The scale is the point. At 550 rows every query returns instantly however it is
written, so there is nothing to learn about cost. At 67,000 a scan takes 10ms
where an index seek takes 0.8ms, and a blocked index on a join costs 150x.

Same easy-to-hard ramp as the last two sets, with a **new final stage on query
efficiency**. Those six are graded on their EXPLAIN QUERY PLAN as well as their
rows -- the slow form and the fast form return identical answers, so the plan is
the only thing that can tell them apart. A correct result reached by scanning
67,000 rows is marked wrong, with the plan shown. Press F6 in the GUI to see the
plan and timing for anything you write.

| ID | Concept | Question | In GUI | Stage |
|----|---------|----------|--------|-------|
| Q342 | A2 COUNT and AVG | Funding recorded, and not | ex 1 | 1 - Warm-up |
| Q343 | A3 WHERE vs HAVING | Which enrolment statuses were common in 2026 | ex 2 | 1 - Warm-up |
| Q344 | general | Sections by size | ex 3 | 1 - Warm-up |
| Q345 | A2 COUNT and AVG | Average mark, where there is one | ex 4 | 1 - Warm-up |
| Q346 | J2 outer joins | Every course, scheduled or not | ex 5 | 2 - First joins |
| Q347 | J2 outer joins | Unstaffed sections per term | ex 6 | 2 - First joins |
| Q348 | J1 self-joins | Courses that sit alongside each other | ex 7 | 2 - First joins |
| Q349 | J2 outer joins | Courses nobody has scheduled | ex 8 | 2 - First joins |
| Q350 | E1 EXISTS | Instructors who mentor nobody | ex 9 | 2 - First joins |
| Q351 | R1 recursive CTE | Everyone under Margaret Ashworth | ex 10 | 3 - Recursion |
| Q352 | R1 recursive CTE | What Audit and Assurance needs | ex 11 | 3 - Recursion |
| Q353 | R1 recursive CTE | What is blocked by Programming Foundations | ex 12 | 3 - Recursion |
| Q354 | R1 recursive CTE | A full study plan for Machine Learning | ex 13 | 3 - Recursion |
| Q355 | D1 dates & gaps | How long each term runs | ex 14 | 4 - Dates, sets and pivots |
| Q356 | D1 dates & gaps | Enrolments by month | ex 15 | 4 - Dates, sets and pivots |
| Q357 | S1 set operations | Billed in a month nobody enrolled | ex 16 | 4 - Dates, sets and pivots |
| Q358 | S1 set operations | Required reading on a first-year course | ex 17 | 4 - Dates, sets and pivots |
| Q359 | A1 conditional aggregation | Enrolment status by term | ex 18 | 4 - Dates, sets and pivots |
| Q360 | W3 window vs GROUP BY | Term on term | ex 19 | 5 - Window functions |
| Q361 | W1 window frames | Enrolments so far | ex 20 | 5 - Window functions |
| Q362 | W3 window vs GROUP BY | Share of the enrolments by faculty | ex 21 | 5 - Window functions |
| Q363 | W2 window ranking | The two biggest courses in each faculty | ex 22 | 5 - Window functions |
| Q364 | E2 correlated subqueries | Paid above their own department's average | ex 23 | 6 - Grain and correlation |
| Q365 | C2 grain | Enrolments and assessments per term | ex 24 | 6 - Grain and correlation |
| Q366 | X1 index vs expression | A year of enrolments, without scanning the table | ex 25 | 7 - Query efficiency |
| Q367 | X1 index vs expression | Names beginning with Sofia | ex 26 | 7 - Query efficiency |
| Q368 | X2 sorts and temp b-trees | Ten earliest enrolments, without sorting 67,000 rows | ex 27 | 7 - Query efficiency |
| Q369 | X3 composite index order | Withdrawals, using the composite index | ex 28 | 7 - Query efficiency |
| Q370 | X2 sorts and temp b-trees | Enrolments per day, without a temporary sort | ex 29 | 7 - Query efficiency |
| Q371 | X4 join strategy | What blocking an index does to a join | ex 30 | 7 - Query efficiency |

## Retired

Asked previously and since replaced. **Kept so they are never regenerated** -
they still count as asked.

| ID | Concept | Question | In GUI | Status |
|----|---------|----------|--------|--------|
| Q042 | C2 grain | Revenue per category | - | retired |
| Q162 | R1 recursive CTE | The whole chain, written out | - | retired |
| Q163 | R1 recursive CTE | Everyone above Nadia Kaur | - | retired |
| Q164 | R1 recursive CTE | Every manager, everyone under them | - | retired |
| Q165 | R1 recursive CTE | How many people are under you | - | retired |
| Q166 | R2 recursive series | Score bands, including the empty ones | - | retired |
| Q167 | R2 recursive series | Critical months, including the quiet ones | - | retired |
| Q168 | S1 set operations | Stocked in Leeds, not in Coventry | - | retired |
| Q169 | S1 set operations | Both kinds of contract | - | retired |
| Q170 | X1 subqueries/EXISTS | Machines nobody has touched | - | retired |
| Q171 | X1 subqueries/EXISTS | Never failed an inspection | - | retired |
| Q172 | X2 correlated subquery | Costlier than its category average | - | retired |
| Q173 | A1 conditional aggregation | Counted and uncounted stock | - | retired |
| Q174 | C9 integer division | Close rate by priority | - | retired |
| Q175 | A1 conditional aggregation | Every status in one row | - | retired |
| Q176 | D1 dates & gaps | The jobs that dragged | - | retired |
| Q177 | D2 dates & NULL | Out of warranty when it broke | - | retired |
| Q178 | D1 dates & gaps | How long invoices take to pay | - | retired |
| Q179 | W1 window frames | Invoiced so far this year | - | retired |
| Q180 | C3 PARTITION BY | Ranked inside your own depot | - | retired |
| Q181 | C3 PARTITION BY | Share of the category | - | retired |
| Q182 | W1 window frames | Against the best in the depot | - | retired |
| Q183 | B1 silent sampling | What the labour cost each depot | - | retired |
| Q184 | B1 silent sampling | Spend by category, after discount | - | retired |
| Q185 | J1 self-joins | Same region, same tier | - | retired |
| Q186 | J1 self-joins | Same depot, same certification | - | retired |
| Q187 | C2 grain | Parts and labour on one job | - | retired |
| Q188 | C2 grain | Contracts and sites per customer | - | retired |
| Q189 | C7 NULL | Still running, or merely undated | - | retired |
| Q190 | C7 NULL | Certified, uncertified, unknown | - | retired |
| Q191 | general | Money still owed, by region | - | retired |
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
| Q192 | R1 recursive CTE | Which branch of the company | - | retired |
| Q193 | R1 recursive CTE | How deep does your tree go | - | retired |
| Q194 | R1 recursive CTE | What the people above you cost | - | retired |
| Q195 | R2 recursive series | Jobs and invoices, month by month | - | retired |
| Q196 | R2 recursive series | One row per month a contract ran | - | retired |
| Q197 | R2 recursive series | Every depot, every month | - | retired |
| Q198 | C2 grain | Machines and contracts per customer | - | retired |
| Q199 | C2 grain | Average hours a job takes, by priority | - | retired |
| Q200 | C2 grain | How many customers has each technician served | - | retired |
| Q201 | A1 conditional aggregation | Billed against collected, by region | - | retired |
| Q202 | A1 conditional aggregation | What the discount cost, by category | - | retired |
| Q203 | C7 NULL | Parts below reorder level, all parts listed | - | retired |
| Q204 | C7 NULL | Average response time by tier | - | retired |
| Q205 | X1 subqueries/EXISTS | Customers who have paid everything | - | retired |
| Q206 | X2 correlated subquery | Longer than that technician usually takes | - | retired |
| Q207 | C3 PARTITION BY | The first invoice each customer got | - | retired |
| Q208 | W1 window frames | Smoothed either side | - | retired |
| Q209 | C3 PARTITION BY | How long until the machine came back | - | retired |
| Q210 | W1 window frames | The most-fitted part in each category | - | retired |
| Q211 | D1 dates & gaps | How long before anyone turned up | - | retired |
| Q212 | D1 dates & gaps | The longest quiet spell | - | retired |
| Q213 | D1 dates & gaps | By quarter, not by month | - | retired |
| Q214 | S1 set operations | Under contract, never called out | - | retired |
| Q215 | S1 set operations | Running low on the expensive ones | - | retired |
| Q216 | S1 set operations | Everything that happened to machine 38 | - | retired |
| Q217 | B1 silent sampling | Average line value by category | - | retired |
| Q218 | B1 silent sampling | What the stock on hand is worth | - | retired |
| Q219 | J1 self-joins | Parts fitted on the same job | - | retired |
| Q220 | J1 self-joins | Hired around the same time | - | retired |
| Q221 | general | Depot scorecard | - | retired |
| Q222 | W1 window frames | Invoicing, month by month and so far | - | retired |
| Q223 | W1 window frames | Month on month | - | retired |
| Q224 | W2 window ranking | The latest job on each machine | - | retired |
| Q225 | W2 window ranking | Busiest at each depot, ties and all | - | retired |
| Q226 | W1 window frames | Three-month rolling average | - | retired |
| Q227 | W2 window ranking | Quartiles of workload | - | retired |
| Q228 | W3 window vs GROUP BY | Share of the invoiced total | - | retired |
| Q229 | W3 window vs GROUP BY | How long until the machine is seen again | - | retired |
| Q230 | W3 window vs GROUP BY | Each entry against its technician's average | - | retired |
| Q231 | A2 COUNT and AVG | Certified and not | - | retired |
| Q232 | A3 WHERE vs HAVING | Which priorities were busy in 2026 | - | retired |
| Q233 | A1 conditional aggregation | Invoice status by priority | - | retired |
| Q234 | A2 COUNT and AVG | Average score, where there is one | - | retired |
| Q235 | J2 outer joins | Every part, used or not | - | retired |
| Q236 | J2 outer joins | Critical jobs per technician | - | retired |
| Q237 | J1 self-joins | Hired the same year, same depot | - | retired |
| Q238 | J2 outer joins | Machines nobody has touched | - | retired |
| Q239 | E1 EXISTS | Customers still under warranty somewhere | - | retired |
| Q240 | E1 EXISTS | Never on a critical job | - | retired |
| Q241 | E2 correlated subqueries | Dear for its own category | - | retired |
| Q242 | C7 NULL | Ended, running, or open-ended | - | retired |
| Q243 | C7 NULL | Everyone who is not level 5 | - | retired |
| Q244 | D1 dates & gaps | The five slowest jobs to close | - | retired |
| Q245 | D1 dates & gaps | Which day of the week is busiest | - | retired |
| Q246 | D1 dates & gaps | Inspections by month, across two years | - | retired |
| Q247 | S1 set operations | Invoiced in a month nothing opened | - | retired |
| Q248 | S1 set operations | Low on stock and needed for critical work | - | retired |
| Q249 | C2 grain | Parts and labour on the critical jobs | - | retired |
| Q250 | C2 grain | Spend by part category | - | retired |
| Q251 | general | Machines by age band | - | retired |
| Q252 | R1 recursive CTE | Everything Machine Learning depends on | - | retired |
| Q253 | R1 recursive CTE | How deep does the chain go | - | retired |
| Q254 | R2 recursive series | Every month, including the quiet ones | - | retired |
| Q255 | R1 recursive CTE | How far below the top | - | retired |
| Q256 | W2 window ranking | Top of each programme, ties and all | - | retired |
| Q257 | W3 window vs GROUP BY | Term on term | - | retired |
| Q258 | W1 window frames | Billed so far | - | retired |
| Q259 | W3 window vs GROUP BY | Share of the enrolments by faculty | - | retired |
| Q260 | J2 outer joins | Every course, scheduled or not | - | retired |
| Q261 | J2 outer joins | Withdrawals per section | - | retired |
| Q262 | J1 self-joins | Classmates on the same programme | - | retired |
| Q263 | J2 outer joins | Textbooks nobody assigns | - | retired |
| Q264 | A2 COUNT and AVG | Graded and not | - | retired |
| Q265 | A3 WHERE vs HAVING | Which programmes were busy in 2026 | - | retired |
| Q266 | A1 conditional aggregation | Enrolment status by delivery mode | - | retired |
| Q267 | A2 COUNT and AVG | Average mark, where there is one | - | retired |
| Q268 | E1 EXISTS | Students who have reached level 4 | - | retired |
| Q269 | E1 EXISTS | Never taught online | - | retired |
| Q270 | E2 correlated subqueries | Dear for its own publisher | - | retired |
| Q271 | D1 dates & gaps | The five slowest payments to settle | - | retired |
| Q272 | D1 dates & gaps | Enrolled before the term began | - | retired |
| Q273 | D1 dates & gaps | Assessment deadlines by month | - | retired |
| Q274 | C7 NULL | Settled, outstanding, or waived | - | retired |
| Q275 | C7 NULL | Everyone not funding themselves | - | retired |
| Q276 | S1 set operations | Billed in a month nobody enrolled | - | retired |
| Q277 | S1 set operations | Required reading on a first-year course | - | retired |
| Q278 | C2 grain | Students and assessments on each section | - | retired |
| Q279 | C2 grain | What the library spent by publisher | - | retired |
| Q280 | general | Courses by credit band | - | retired |
| Q281 | C2 grain | How many departments does each campus actually run | - | retired |
| Q282 | A2 COUNT and AVG | Funding recorded, and not | - | retired |
| Q283 | A3 WHERE vs HAVING | Which payment statuses were common in 2025 | - | retired |
| Q284 | general | Textbooks by price band | - | retired |
| Q285 | C7 NULL | Settled, waived, or still owing | - | retired |
| Q286 | C7 NULL | Everyone not funding themselves | - | retired |
| Q287 | A2 COUNT and AVG | Average page count, where it is known | - | retired |
| Q288 | J2 outer joins | Every course, scheduled or not | - | retired |
| Q289 | J2 outer joins | Online teaching per instructor | - | retired |
| Q290 | J1 self-joins | Courses that sit alongside each other | - | retired |
| Q291 | J2 outer joins | Textbooks nobody assigns | - | retired |
| Q292 | E1 EXISTS | Students who have reached level 4 | - | retired |
| Q293 | E1 EXISTS | Never taught online | - | retired |
| Q294 | R1 recursive CTE | Anil Chaudhary's line of mentors | - | retired |
| Q295 | R1 recursive CTE | What Interaction Design needs, all the way down | - | retired |
| Q296 | R1 recursive CTE | What is blocked by Visual Communication | - | retired |
| Q297 | R1 recursive CTE | What Machine Learning needs, all the way down | - | retired |
| Q298 | D1 dates & gaps | The five slowest payments to settle | - | retired |
| Q299 | D1 dates & gaps | Assessment deadlines by month | - | retired |
| Q300 | D1 dates & gaps | Enrolled before the term began | - | retired |
| Q301 | S1 set operations | Billed in a month nobody enrolled | - | retired |
| Q302 | S1 set operations | Required reading on a first-year course | - | retired |
| Q303 | A1 conditional aggregation | Enrolment status by term | - | retired |
| Q304 | W3 window vs GROUP BY | Term on term | - | retired |
| Q305 | W1 window frames | Billed so far | - | retired |
| Q306 | W3 window vs GROUP BY | Share of the enrolments by faculty | - | retired |
| Q307 | W2 window ranking | The most recent run of each course | - | retired |
| Q308 | W2 window ranking | Top of each programme, ties and all | - | retired |
| Q309 | E2 correlated subqueries | Bigger than its own department's average | - | retired |
| Q310 | C2 grain | Students and assessments on each section | - | retired |
| Q311 | C2 grain | What the library holds, by faculty | - | retired |
| Q312 | A2 COUNT and AVG | Staffed and unstaffed | - | retired |
| Q313 | A3 WHERE vs HAVING | Which assessment kinds cluster in 2026 | - | retired |
| Q314 | general | Instructors by pay band | - | retired |
| Q315 | C7 NULL | Graded, dropped, or still going | - | retired |
| Q316 | C7 NULL | Everyone not on the top pay grade | - | retired |
| Q317 | A2 COUNT and AVG | Average copies held, where it is known | - | retired |
| Q318 | J2 outer joins | Every student, enrolled or not | - | retired |
| Q319 | J2 outer joins | Level-4 courses per department | - | retired |
| Q320 | J1 self-joins | Room clashes | - | retired |
| Q321 | J2 outer joins | Students who never enrolled | - | retired |
| Q322 | E1 EXISTS | Courses with an unstaffed section | - | retired |
| Q323 | E1 EXISTS | Instructors who mentor nobody | - | retired |
| Q324 | R1 recursive CTE | Everyone under Margaret Ashworth | - | retired |
| Q325 | R1 recursive CTE | What Audit and Assurance needs | - | retired |
| Q326 | R1 recursive CTE | What is blocked by Computer Systems | - | retired |
| Q327 | R1 recursive CTE | A full study plan for Machine Learning | - | retired |
| Q328 | D1 dates & gaps | How long each term runs | - | retired |
| Q329 | D1 dates & gaps | Enrolments by month | - | retired |
| Q330 | D1 dates & gaps | Deadlines after the term ends | - | retired |
| Q331 | S1 set operations | First-year reading that never reappears | - | retired |
| Q332 | S1 set operations | Students who have both finished and dropped | - | retired |
| Q333 | A1 conditional aggregation | Assessment kinds by term | - | retired |
| Q334 | W3 window vs GROUP BY | Month on month | - | retired |
| Q335 | W1 window frames | Enrolments so far | - | retired |
| Q336 | W3 window vs GROUP BY | Share of the billing by status | - | retired |
| Q337 | W2 window ranking | Each student's first enrolment | - | retired |
| Q338 | W2 window ranking | Top of each campus, ties and all | - | retired |
| Q339 | E2 correlated subqueries | Paid above their own department's average | - | retired |
| Q340 | C2 grain | Enrolments and payments per student | - | retired |
| Q341 | C2 grain | Sections whose marking does not add up | - | retired |

## History

- **Q001-Q041** the original breadth-first set (2026-08-24). Retired same day.
- **Q042-Q071** first pass against `sql-concepts-review.html`, on the ordering and
  payments tables. Retired when the schema gained the fulfilment side.
- **Q072-Q101** second pass against the review, on warehouses, inventory,
  shipments and returns. Retired when the schema moved to the repair depot.
- **Q102-Q131** grain-focused set on the repair-depot schema; all 30 solved,
  then retired. Fifteen of them drilled fan-out in five disguises.
- **Q132-Q161** breadth set, same schema re-seeded (SEED 41 -> 77) so no answer
  value carries over. Deliberately broad rather than deep: 3 set operations,
  2 recursive CTEs, 3 subquery/EXISTS, 3 conditional aggregation, 4 dates and
  gaps, 4 window frames, 3 silent sampling, 2 self-joins, 2 grain, 2 NULLs,
  2 general.
  C8 (alias scope) still has no question: SQLite accepts a SELECT alias even in
  `WHERE`, so the engine cannot enforce the rule. It is covered as prose in
  PRACTICE.md instead.
- **Q162-Q191** breadth set on the repair-depot schema re-seeded (SEED 77 ->
  113). Retired after all 30 were solved.
- **Q192-Q221** set built from observed mistakes, re-seeded again (SEED 113 ->
  149). Six recursion questions varying the anchor. Retired after all 30 were
  solved.
- **Q222-Q251** current set, re-seeded (SEED 149 -> 185). Deliberately easier
  and recursion-free, weighted toward window functions: 9 window, 4
  aggregation, 4 joins, 3 subqueries/EXISTS, 3 dates, 2 set operations, 2
  NULLs, 2 grain, 1 general.
- **Q252-Q281** current set, on a NEW schema: the repair depot is replaced by a
  further-education college (13 tables, SEED 221). Same difficulty as the last
  set, even coverage: 4 recursion, 4 window, 4 joins, 4 aggregation, 3
  subqueries/EXISTS, 3 dates, 2 set operations, 2 NULLs, 2 grain, 2 general.
  Recursion runs over a course-prerequisite GRAPH rather than an org chart.
- **Q282-Q311** current set, college schema re-seeded (SEED 221 -> 257).
  Graded easy to hard rather than grouped by concept, with the four recursion
  questions placed mid-set and kept to the simplest possible shape. Stages: 6
  warm-up, 6 first joins, 4 recursion, 6 dates/sets/pivots, 5 window, 3 grain
  and correlation.
- **Q312-Q341** current set, college schema re-seeded (SEED 257 -> 293). Same
  easy-to-hard ramp and difficulty as Q282-Q311; every question reaches its
  concept through a different table or relationship, and the four recursion
  questions are four different shapes rather than one shape from four starting
  points.
- **Q342-Q371** current set, college schema re-seeded and scaled (SEED 293 ->
  329; enrolments 550 -> 67,000). Adds a seventh stage on query efficiency,
  graded on EXPLAIN QUERY PLAN rather than on rows, plus an F6 "Explain plan"
  button in the GUI and two new indexes the questions hit or miss.
