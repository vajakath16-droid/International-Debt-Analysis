
from sqlalchemy import create_engine, text
import pandas as pd

df=pd.read_csv(r"g:\My Drive\Colab Notebooks\cleaned_international_debt.csv")

if 'debt_value' in df.columns:
    df.drop(columns=['debt_value'],inplace=True)

engine = create_engine("postgresql+psycopg2://postgres:Vajakath16@localhost:5432/debt_db")

with engine.connect() as conn:
    print("Connected successfully:", conn.execute(text("SELECT version();")).fetchone())

create_tables_sql = """
DROP TABLE IF EXISTS debt_data;
DROP TABLE IF EXISTS countries;
DROP TABLE IF EXISTS indicators;

CREATE TABLE countries (
    country_id   SERIAL PRIMARY KEY,
    country_name VARCHAR(150) NOT NULL,
    country_code VARCHAR(10)
);

CREATE TABLE indicators (
    indicator_id   SERIAL PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE debt_data (
    debt_id      SERIAL PRIMARY KEY,
    country_id   INTEGER NOT NULL REFERENCES countries(country_id),
    indicator_id INTEGER NOT NULL REFERENCES indicators(indicator_id),
    year         INTEGER NOT NULL,
    debt_value   NUMERIC
);
"""

with engine.begin() as conn:
    conn.execute(text(create_tables_sql))

print("Tables created: countries, indicators, debt_data")

# Identify indicator columns Country Name, Country Code, Year)
indicator_cols = [c for c in df.columns if c not in ['Country Name', 'Country Code', 'Year']]


countries_stage = (
    df[['Country Name', 'Country Code']]
    .drop_duplicates()
    .rename(columns={'Country Name': 'country_name', 'Country Code': 'country_code'})
    .reset_index(drop=True)
)


indicators_stage = pd.DataFrame({'indicator_name': indicator_cols})


fact_stage = df.melt(
    id_vars=['Country Name', 'Country Code', 'Year'],
    value_vars=indicator_cols,
    var_name='indicator_name',
    value_name='debt_value'
).rename(columns={'Country Name': 'country_name', 'Country Code': 'country_code', 'Year': 'year'})

print("Countries:", countries_stage.shape)
print("Indicators:", indicators_stage.shape)
print("Fact rows (before FK mapping):", fact_stage.shape)

# Insert  tables SERIAL columns auto-generate the primary keys)
countries_stage.to_sql('countries', engine, if_exists='append', index=False)
indicators_stage.to_sql('indicators', engine, if_exists='append', index=False)

#  primary keys (country_id / indicator_id)
countries_lookup = pd.read_sql('SELECT * FROM countries', engine)
indicators_lookup = pd.read_sql('SELECT * FROM indicators', engine)

# Map  table's text columns to the new foreign keys
fact_ready = (
    fact_stage
    .merge(countries_lookup, on=['country_name', 'country_code'], how='left')
    .merge(indicators_lookup, on='indicator_name', how='left')
    [['country_id', 'indicator_id', 'year', 'debt_value']]
)

fact_ready.to_sql('debt_data', engine, if_exists='append', index=False)

print("Rows inserted into debt_data:", len(fact_ready))

verify_sql = """
SELECT
    c.country_name,
    i.indicator_name,
    d.year,
    d.debt_value
FROM debt_data d
JOIN countries  c ON d.country_id = c.country_id
JOIN indicators i ON d.indicator_id = i.indicator_id
LIMIT 10;
"""
pd.read_sql(text(verify_sql), engine)

# Basic Quries
sql = """
SELECT DISTINCT country_name
FROM countries
ORDER BY country_name;
"""
pd.read_sql(text(sql), engine)

#2
sql = """
SELECT COUNT(*) AS total_countries
FROM countries;
"""
pd.read_sql(text(sql), engine)

#3
sql = """
SELECT COUNT(*) AS total_countries
FROM countries;
"""
pd.read_sql(text(sql), engine)

#4
sql = """
SELECT c.country_name, i.indicator_name, d.year, d.debt_value
FROM debt_data d
JOIN countries  c ON d.country_id = c.country_id
JOIN indicators i ON d.indicator_id = i.indicator_id
LIMIT 10;
"""
pd.read_sql(text(sql), engine)

#5
sql = """
SELECT c.country_name, i.indicator_name, d.year, d.debt_value
FROM debt_data d
JOIN countries  c ON d.country_id = c.country_id
JOIN indicators i ON d.indicator_id = i.indicator_id
LIMIT 10;
"""
pd.read_sql(text(sql), engine)

#6
sql = """
SELECT DISTINCT indicator_name
FROM indicators
ORDER BY indicator_name;
"""
pd.read_sql(text(sql), engine)

#7
sql = """
SELECT c.country_name, COUNT(*) AS record_count
FROM debt_data d
JOIN countries c ON d.country_id = c.country_id
GROUP BY c.country_name
ORDER BY record_count DESC;
"""
pd.read_sql(text(sql), engine)

#8
sql = """
SELECT c.country_name, i.indicator_name, d.year, d.debt_value
FROM debt_data d
JOIN countries  c ON d.country_id = c.country_id
JOIN indicators i ON d.indicator_id = i.indicator_id
WHERE d.debt_value > 1000000000
ORDER BY d.debt_value DESC;
"""
pd.read_sql(text(sql), engine)

#9
sql = """
SELECT
    MIN(debt_value) AS min_debt,
    MAX(debt_value) AS max_debt,
    AVG(debt_value) AS avg_debt
FROM debt_data;
"""
pd.read_sql(text(sql), engine)

# 10
sql = """
SELECT COUNT(*) AS total_records
FROM debt_data;
"""
pd.read_sql(text(sql), engine)

#intermediate Quries

sql = """
SELECT c.country_name, SUM(d.debt_value) AS total_debt
FROM debt_data d
JOIN countries c ON d.country_id = c.country_id
GROUP BY c.country_name
ORDER BY total_debt DESC;
"""
pd.read_sql(text(sql), engine)

#2
sql = """
SELECT c.country_name, SUM(d.debt_value) AS total_debt
FROM debt_data d
JOIN countries c ON d.country_id = c.country_id
GROUP BY c.country_name
ORDER BY total_debt DESC
LIMIT 10;
"""
pd.read_sql(text(sql), engine)

#3
sql = """
SELECT c.country_name, AVG(d.debt_value) AS avg_debt
FROM debt_data d
JOIN countries c ON d.country_id = c.country_id
GROUP BY c.country_name
ORDER BY avg_debt DESC;
"""
pd.read_sql(text(sql), engine)

#4
sql = """
SELECT i.indicator_name, SUM(d.debt_value) AS total_debt
FROM debt_data d
JOIN indicators i ON d.indicator_id = i.indicator_id
GROUP BY i.indicator_name
ORDER BY total_debt DESC;
"""
pd.read_sql(text(sql), engine)

#5
sql = """
SELECT i.indicator_name, SUM(d.debt_value) AS total_debt
FROM debt_data d
JOIN indicators i ON d.indicator_id = i.indicator_id
GROUP BY i.indicator_name
ORDER BY total_debt DESC
LIMIT 1;
"""
pd.read_sql(text(sql), engine)

#6
sql = """
SELECT c.country_name, SUM(d.debt_value) AS total_debt
FROM debt_data d
JOIN countries c ON d.country_id = c.country_id
GROUP BY c.country_name
ORDER BY total_debt ASC
LIMIT 1;
"""
pd.read_sql(text(sql), engine)

#7
sql = """
SELECT c.country_name, i.indicator_name, SUM(d.debt_value) AS total_debt
FROM debt_data d
JOIN countries  c ON d.country_id = c.country_id
JOIN indicators i ON d.indicator_id = i.indicator_id
GROUP BY c.country_name, i.indicator_name
ORDER BY total_debt DESC;
"""
pd.read_sql(text(sql), engine)

#8
sql = """
SELECT c.country_name, COUNT(DISTINCT d.indicator_id) AS indicator_count
FROM debt_data d
JOIN countries c ON d.country_id = c.country_id
GROUP BY c.country_name
ORDER BY indicator_count DESC;
"""
pd.read_sql(text(sql), engine)

#9
sql = """
WITH country_totals AS (
    SELECT country_id, SUM(debt_value) AS total_debt
    FROM debt_data
    GROUP BY country_id
)
SELECT c.country_name, ct.total_debt
FROM country_totals ct
JOIN countries c ON ct.country_id = c.country_id
WHERE ct.total_debt > (SELECT AVG(total_debt) FROM country_totals)
ORDER BY ct.total_debt DESC;
"""
pd.read_sql(text(sql), engine)

#10
sql = """
SELECT
    c.country_name,
    SUM(d.debt_value) AS total_debt,
    RANK() OVER (ORDER BY SUM(d.debt_value) DESC) AS debt_rank
FROM debt_data d
JOIN countries c ON d.country_id = c.country_id
GROUP BY c.country_name
ORDER BY debt_rank;
"""
pd.read_sql(text(sql), engine)

#Advanced Quries
sql = """
SELECT i.indicator_name, SUM(d.debt_value) AS total_debt
FROM debt_data d
JOIN indicators i ON d.indicator_id = i.indicator_id
GROUP BY i.indicator_name
ORDER BY total_debt DESC
LIMIT 5;
"""
pd.read_sql(text(sql), engine)

#2
sql = """
WITH country_totals AS (
    SELECT country_id, SUM(debt_value) AS total_debt
    FROM debt_data
    GROUP BY country_id
),
global_total AS (
    SELECT SUM(debt_value) AS grand_total FROM debt_data
)
SELECT
    c.country_name,
    ct.total_debt,
    ROUND((ct.total_debt / g.grand_total) * 100, 2) AS pct_of_global_debt
FROM country_totals ct
JOIN countries c ON ct.country_id = c.country_id
CROSS JOIN global_total g
ORDER BY pct_of_global_debt DESC;
"""
pd.read_sql(text(sql), engine)

#3
sql = """
WITH country_indicator_totals AS (
    SELECT
        d.indicator_id,
        d.country_id,
        SUM(d.debt_value) AS total_debt
    FROM debt_data d
    GROUP BY d.indicator_id, d.country_id
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY indicator_id ORDER BY total_debt DESC) AS rn
    FROM country_indicator_totals
)
SELECT i.indicator_name, c.country_name, r.total_debt, r.rn AS rank_within_indicator
FROM ranked r
JOIN indicators i ON r.indicator_id = i.indicator_id
JOIN countries  c ON r.country_id = c.country_id
WHERE r.rn <= 3
ORDER BY i.indicator_name, r.rn;
"""
pd.read_sql(text(sql), engine)

#4
sql = """
SELECT
    c.country_name,
    MAX(d.debt_value) - MIN(d.debt_value) AS debt_range
FROM debt_data d
JOIN countries c ON d.country_id = c.country_id
GROUP BY c.country_name
ORDER BY debt_range DESC;
"""
pd.read_sql(text(sql), engine)

#5
sql = """
DROP VIEW IF EXISTS top10_countries;

CREATE VIEW top10_countries AS
SELECT c.country_name, SUM(d.debt_value) AS total_debt
FROM debt_data d
JOIN countries c ON d.country_id = c.country_id
GROUP BY c.country_name
ORDER BY total_debt DESC
LIMIT 10;

SELECT * FROM top10_countries;
"""
pd.read_sql(text(sql), engine)

#6
sql = """
WITH country_totals AS (
    SELECT c.country_name, SUM(d.debt_value) AS total_debt
    FROM debt_data d
    JOIN countries c ON d.country_id = c.country_id
    GROUP BY c.country_name
)
SELECT
    country_name,
    total_debt,
    CASE
        WHEN total_debt >= (SELECT PERCENTILE_CONT(0.66) WITHIN GROUP (ORDER BY total_debt) FROM country_totals) THEN 'High Debt'
        WHEN total_debt >= (SELECT PERCENTILE_CONT(0.33) WITHIN GROUP (ORDER BY total_debt) FROM country_totals) THEN 'Medium Debt'
        ELSE 'Low Debt'
    END AS debt_category
FROM country_totals
ORDER BY total_debt DESC;
"""
pd.read_sql(text(sql), engine)

#7
sql = """
WITH yearly_totals AS (
    SELECT c.country_name, d.year, SUM(d.debt_value) AS yearly_debt
    FROM debt_data d
    JOIN countries c ON d.country_id = c.country_id
    GROUP BY c.country_name, d.year
)
SELECT
    country_name,
    year,
    yearly_debt,
    SUM(yearly_debt) OVER (PARTITION BY country_name ORDER BY year) AS cumulative_debt
FROM yearly_totals
ORDER BY country_name, year;
"""
pd.read_sql(text(sql), engine)

#8
sql = """
WITH indicator_avg AS (
    SELECT indicator_id, AVG(debt_value) AS avg_debt
    FROM debt_data
    GROUP BY indicator_id
),
overall_avg AS (
    SELECT AVG(debt_value) AS overall FROM debt_data
)
SELECT i.indicator_name, ia.avg_debt
FROM indicator_avg ia
JOIN indicators i ON ia.indicator_id = i.indicator_id
CROSS JOIN overall_avg o
WHERE ia.avg_debt > o.overall
ORDER BY ia.avg_debt DESC;
"""
pd.read_sql(text(sql), engine)

#9
sql = """
WITH country_totals AS (
    SELECT country_id, SUM(debt_value) AS total_debt
    FROM debt_data
    GROUP BY country_id
),
global_total AS (
    SELECT SUM(debt_value) AS grand_total FROM debt_data
)
SELECT
    c.country_name,
    ct.total_debt,
    ROUND((ct.total_debt / g.grand_total) * 100, 2) AS pct_of_global_debt
FROM country_totals ct
JOIN countries c ON ct.country_id = c.country_id
CROSS JOIN global_total g
WHERE (ct.total_debt / g.grand_total) * 100 > 5
ORDER BY pct_of_global_debt DESC;
"""
pd.read_sql(text(sql), engine)

#10
sql = """
WITH country_indicator_totals AS (
    SELECT d.country_id, d.indicator_id, SUM(d.debt_value) AS total_debt
    FROM debt_data d
    GROUP BY d.country_id, d.indicator_id
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY country_id ORDER BY total_debt DESC) AS rn
    FROM country_indicator_totals
)
SELECT c.country_name, i.indicator_name, r.total_debt
FROM ranked r
JOIN countries  c ON r.country_id = c.country_id
JOIN indicators i ON r.indicator_id = i.indicator_id
WHERE r.rn = 1
ORDER BY c.country_name;
"""
pd.read_sql(text(sql), engine)

 # Data Visualization
import plotly.express as px

top10_pd = pd.read_sql(text("SELECT country_name, SUM(debt_value) AS total_debt FROM debt_data d JOIN countries c ON d.country_id=c.country_id GROUP BY country_name ORDER BY total_debt DESC LIMIT 10"), engine)

fig = px.bar(
    top10_pd,
    x='total_debt', y='country_name',
    orientation='h',
    title='Top 10 Countries by Total External Debt (Interactive)',
    labels={'total_debt': 'Total Debt (US$)', 'country_name': 'Country'}
)
fig.update_layout(yaxis={'categoryorder': 'total ascending'})
fig.show()

trend_pd = pd.read_sql(text("""
    SELECT d.year, i.indicator_name, SUM(d.debt_value) AS total_debt
    FROM debt_data d
    JOIN indicators i ON d.indicator_id = i.indicator_id
    GROUP BY d.year, i.indicator_name
    ORDER BY d.year
"""), engine)

fig2 = px.line(
    trend_pd, x='year', y='total_debt', color='indicator_name',
    title='Debt Trend Over Time by Indicator'
)
fig2.show()

