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

## Growth Model

A project to update the retention assumptions in the growth model

This notebook contains basic statistical analysis and visualization of the data.

### Data Sources
- summary : Processed file from notebook 1-Data_Prep

### Changes
- 02-05-2020 : Started project

```python
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

```


```python
%matplotlib inline
```

### File Locations

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

### Perform Data Analysis


#### HS Retention (File 1)

<!-- #region heading_collapsed=true -->
##### Average Total Enrollment
<!-- #endregion -->

```python hidden=true
total_enrollent_df = df_active_students.groupby(
    ["Site", "Global Academic Year", "enrollment_target"], as_index=False
).sum()
```

```python hidden=true
total_enrollent_df.pivot_table(
    index=["enrollment_target", "Site"], values="active_student", aggfunc="mean"
)
```

<!-- #region heading_collapsed=true -->
##### Average Enrollment By Grade
<!-- #endregion -->

```python hidden=true
by_grade_df = df_active_students.groupby(
    ["Site", "Grade (AT)", "Global Academic Year", "enrollment_target"], as_index=False
).sum()

# removing grades with less than 5 students as this could skew the results

by_grade_df = by_grade_df[by_grade_df.active_student > 5]


```

```python hidden=true
grade_order = ["9th Grade", "10th Grade", "11th Grade", "12th Grade"]

by_grade_df_table = by_grade_df.pivot_table(
    index=["enrollment_target","Grade (AT)"], values="active_student", aggfunc="mean"
)

by_grade_df_table = by_grade_df_table.reindex(grade_order, level='Grade (AT)')

by_grade_df_table["pct_change"] = by_grade_df_table[
    "active_student"
].pct_change()

by_grade_df_table
```

<!-- #region heading_collapsed=true -->
#### Annual College Drop out Rate (By College Year) (File 3)
<!-- #endregion -->

```python hidden=true
ps_year_count = df3.pivot_table(
    index=["enrollment_target", "Region", "Site", "High School Class", "Grade (AT)"],
    columns="active_student",
    values="18 Digit ID",
    aggfunc="count",
)
```

```python hidden=true
ps_year_count = ps_year_count.sort_values(
    by=["enrollment_target", "Site", "High School Class"]
)
```

```python hidden=true
ps_year_count_grouped = ps_year_count.groupby(["Region", "Grade (AT)"]).mean()
# ps_year_count_grouped['change'] = ps_year_count_grouped[True].pct_change()*100
ps_year_count_grouped["change"] = (
    ps_year_count_grouped.groupby("Region")[True].pct_change().round(2) * 100
)
ps_year_count_grouped
```

```python hidden=true
ps_year_count_grouped.groupby("Grade (AT)")["change"].describe()
```

#### College Cohort Graduation Rates (File 2)


##### Graduation Rate By Class and By Region

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
# For grad rates by class grouped by region
grad_rates_region_class = create_rate_table(
    df2, ["Region", "High School Class"], 2, list(range(4, 8))
)
grad_rates_region_class
```

##### Graduation Rate By Class

```python
grad_rates_class = create_rate_table(df2, ["High School Class"], 1, list(range(4, 8)))

grad_rates_class
```

##### Graduation Rate By Region

```python
grad_rates_region = create_rate_table(df2, ["Region"], 1, list(range(4, 8)))
grad_rates_region
```

##### All Time Graduation Rate

```python
# All time grad rate - no groupings
grad_rates_all_time = df2[df2.columns[4:8]].apply(pd.Series.value_counts)

grad_rates_all_time = grad_rates_all_time.apply(lambda x: x / x.sum())
grad_rates_all_time = grad_rates_all_time.drop(index=[False, "NA"])

grad_rates_all_time
```

### Save Excel file into reports directory

Save an Excel file with intermediate results into the report directory

```python
writer = pd.ExcelWriter(report_file, engine="xlsxwriter")
```

```python
df.to_excel(writer, sheet_name="Report")
```

```python
writer.save()
```
