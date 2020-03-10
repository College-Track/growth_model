---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.2'
      jupytext_version: 1.3.0
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

# FY 20 Growth Model Updates

Goal: Evaluate historical data from the past four fiscal years (FY16 -FY19) to determine more accurate averages for the following metrics:

* Year to year high school retention rate
    * i.e. The percent of students who continue on from their Junior to Sophomore year.
* Year to year college retntion rate
    * i.e. The percent of students who continue on from their four year to fifth year.
      * Note, this report will treat graduates and inactive students as the same. For example, 100 students are enrolled in their 4th year of college. At the start of their fifth year, 50 students have graduated, and 20 have dropped out (became inactive). The retention rate for 4th -> 5th year will be 30%.
* Updated college graduation rates by high school class

```python
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np


import seaborn as sns
import matplotlib.pyplot as plt

sns.set_style("white")
```


```python
%matplotlib inline
```

```python
today = datetime.today()
in_file = Path.cwd() / "data" / "processed" / "processed_data.pkl"
in_file2 = Path.cwd() / "data" / "processed" / "processed_data_file2.pkl"
in_file3 = Path.cwd() / "data" / "processed" / "processed_data_file3.pkl"

active_students = Path.cwd() / "data" / "processed" / "active_students.pkl"

report_dir = Path.cwd() / "reports"
report_file = report_dir / "Excel_Analysis_{today:%b-%d-%Y}.xlsx"
```

```python
df = pd.read_pickle(in_file)

df2 = pd.read_pickle(in_file2)

df3 = pd.read_pickle(in_file3)

df_active_students = pd.read_pickle(active_students)
```


```python
total_enrollent_df = df_active_students.groupby(
    ["Site", "Global Academic Year", "enrollment_target"], as_index=False
).sum()
```

```python
total_enrollent_df = total_enrollent_df.pivot_table(
    index=["enrollment_target", "Site"], values="active_student", aggfunc="mean"
)
```

```python
total_enrollent_df = total_enrollent_df.reset_index().sort_values("active_student")
```

## High School Data

<!-- #region -->
### Chart 1. Average Total High School Enrollment
This shows the average total enrollment at each site, broken out by each site's enrollment target.

Using the prior logic, a site would meet their enrollment target if they retained 100% of their freshman, and sophomore students, 95% of their juniors, and 88% of their seniors. This would result in the following total numbers:

* 75 Student Enrollment Target: 287
* 60 Student Enrollment Target: 230


As we can see in the following chart, only San Francisco and New Orleans averaged hitting their full enrollment target in the past four years.

Note, The Durant Center only has one cohort of students, which did exceed their cohort target.
<!-- #endregion -->

```python
fig, ax = plt.subplots(figsize=(12, 5))


g = sns.barplot(
    data=total_enrollent_df,
    hue="enrollment_target",
    x="Site",
    y="active_student",
    ax=ax,
)


g.set_xticklabels(g.get_xticklabels(), rotation=45)
g.set_title("Average Total High School Enrollment")


for p in g.patches:
    g.annotate(
        format(p.get_height(), ".0f"),
        (p.get_x() + p.get_width() / 2.0, p.get_height()),
        ha="center",
        va="center",
        xytext=(0, 10),
        textcoords="offset points",
    )

sns.despine()
```

### Chart 2. Average High School Enrollment By Grade Level

This chart shows the average enrollment by each grade level, broken out by the enrollment target for sites.

Key notes:

* The general enrollment pattern is almost identical regardless of a site's cohort target. This means we can make more general enrollment projections.
* Sites tend to increase their enrollment from Freshman to Sophomore year, with a small drop off from Sophomore to Junior year, but then a major (17%) decline from Junior to Senior year.

```python
by_grade_df = df_active_students.groupby(
    ["Site", "Grade (AT)", "Global Academic Year", "enrollment_target"], as_index=False
).sum()

# removing grades with less than 5 students as this could skew the results

by_grade_df = by_grade_df[by_grade_df.active_student > 5]
```


```python
grade_order = ["9th Grade", "10th Grade", "11th Grade", "12th Grade"]

by_grade_df_table = by_grade_df.pivot_table(
    index=["enrollment_target", "Grade (AT)"], values="active_student", aggfunc="mean"
)

by_grade_df_table["pct_change"] = by_grade_df_table["active_student"].pct_change()

by_grade_df_table = by_grade_df_table.reindex(grade_order, level="Grade (AT)")
```

```python
by_grade_df_table = by_grade_df_table.reset_index()
```

```python
fig, ax = plt.subplots(figsize=(12, 5))

g = sns.barplot(
    data=by_grade_df_table,
    hue="enrollment_target",
    x="Grade (AT)",
    y="active_student",
    ax=ax,
)


for p in g.patches:
    g.annotate(
        format(p.get_height(), ".0f"),
        (p.get_x() + p.get_width() / 2.0, p.get_height()),
        ha="center",
        va="center",
        xytext=(0, 10),
        textcoords="offset points",
    )
```


## College Data


### Chart 3. Average College Enrollment By Region and College Year

These charts display the average college enrollment for the sites contained in each CT region. More mature regions, NOLA and Nor Cal, clearly have a similar trend in college numbers compared to younger regions.

```python
ps_year_count = df3.pivot_table(
    index=["enrollment_target", "Region", "Site", "High School Class", "Grade (AT)"],
    columns="active_student",
    values="18 Digit ID",
    aggfunc="count",
)
```

```python
ps_year_count = ps_year_count.sort_values(
    by=["enrollment_target", "Site", "High School Class"]
)
```

```python
ps_year_count_grouped = ps_year_count.groupby(["Region", "Grade (AT)"]).mean()
# ps_year_count_grouped['change'] = ps_year_count_grouped[True].pct_change()*100
ps_year_count_grouped["change"] = (
    ps_year_count_grouped.groupby("Region")[True].pct_change().round(2) * 100
)
```


```python
ps_year_count_grouped = ps_year_count_grouped.reset_index()
```

```python
sns.catplot(
    data=ps_year_count_grouped, x="Grade (AT)", y=True, col="Region", kind="bar"
)
```

### Chart 4. Cohort Graduation Rates

```python
def create_rate_table(df, groupings, level, columns):
    _table = (
        df.groupby(groupings)
        .agg({i: "value_counts" for i in df.columns[columns]})
        .groupby(level=0)
        .transform(lambda x: x)
    )
    _table = _table.groupby(level=list(range(level))).transform(lambda x: x / x.sum())

    _table = _table.drop(index=[False, "NA"], level=level)
    _table = _table.droplevel(level)
    return _table
```

```python
grad_rates_class = create_rate_table(df2, ["High School Class"], 1, list(range(4, 8)))

grad_rates_class.round(2)
```

```python
grad_rates_region = create_rate_table(df2, ["Region"], 1, list(range(4, 8)))
grad_rates_region.round(2)
```

## Recommendations / Decision Points

```html
<script src="https://cdn.rawgit.com/parente/4c3e6936d0d7a46fd071/raw/65b816fb9bdd3c28b4ddf3af602bfd6015486383/code_toggle.js"></script>
<style>
# Uncomment before publishing
# div.prompt {display:none}
</style>
```

```python

```
