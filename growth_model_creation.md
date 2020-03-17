---
jupyter:
  jupytext:
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

```python
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np
import helpers



import seaborn as sns 
import matplotlib.pyplot as plt
sns.set(font_scale=1.5)
sns.set_style("white")

sns.set_context('talk')

sns.set_palette("pastel")

```

```python
df = pd.read_csv('data/raw/enrollment.csv')

```

```python
# Flagging sites for 60 vs 75 enrollment target


def determine_enrollment_target(site):
    enroll_target_60_sites = ['East Palo Alto', 'New Orleans',
                              'Aurora', 'Sacramento', 'Denver', 'Watts', 'The Durant Center', "Ward 8", "Crenshaw"]
    enroll_target_75_sites = ['San Francisco', 'Oakland', 'Boyle Heights']
    
    if site in enroll_target_60_sites:
        return "Enrollment Target: 60"
    elif site in enroll_target_75_sites:
        return "Enrollment Target: 75"
    else:
        return 'Error'
```

```python
df = helpers.shorten_site_names(df)

# df['enrollment_target'] = df.apply(lambda x: determine_enrollment_target(x['Site']),axis=1)

```

```python
hs_assumptions = [.9,1.07,.93,.83]
ps_assumptions = [.98,.91,.81,.93,.57,.51]

assumptions = hs_assumptions + ps_assumptions

assumptions

grade=['Freshman', 'Sophomore', 'Junior', 'Senior', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5', 'Year 6']
```

```python
assumptions_df = pd.DataFrame(list(zip(year, assumptions)), columns=['grade', 'year_over_year_rate'])
```

```python
assumptions_df
```

```python
def determine_grade_index(hs_class, current_year):
    if current_year < 2000:
        current_year += 2000
    index = current_year - hs_class
    return index + 3


```

```python
projected_fy = ["FY 21", "FY 22", "FY 23", "FY 24", "FY 25","FY 26"]
```

```python
df = df[df['High School Class'] <= 2023]
```

```python
start_enrollment = df.pivot_table(index=['Site', 'High School Class'], values='18 Digit ID', aggfunc='count').reset_index()
```

```python
start_enrollment
```

```python
start_enrollment = start_enrollment.rename(columns={'18 Digit ID': "FY 20"})
```

```python
start_enrollment = start_enrollment.reindex(columns = start_enrollment.columns.tolist() + projected_fy)

```

```python
def update_projections(site, hs_class, columns, starting_count):
    for fy in columns:
        year = int(fy.split(' ')[1])
        grade_index = determine_grade_index(hs_class, year)
        if grade_index > 9:
            continue
        
        projected_count = (assumptions_df.year_over_year_rate[grade_index] * starting_count).round(0)
        start_enrollment.loc[(start_enrollment.Site == site) & (start_enrollment['High School Class'] == hs_class), fy] = projected_count
        starting_count = projected_count
        
        
    
    
    
    
    
    
```

```python
start_enrollment.apply(lambda x: update_projections(
    x['Site'], x['High School Class'], start_enrollment.columns[3:], x['FY 20']), axis=1)
```

```python
sites = list(set(df.Site))
```

```python
sites.append('Crenshaw')
```

```python
sites
```

```python
for site in sites:
    target = determine_enrollment_target(site)
    if target == 'Enrollment Target: 75':
        start_value = 75
    elif target == 'Enrollment Target: 60':
        start_value = 60
    
    hs_class = 2024

    while hs_class  <= 2029:
        to_append =[site, hs_class]
        skip_years = 6 - (2029-hs_class)
        to_append.extend([np.nan] * skip_years)
        
        fy_index = 0
        count = start_value
        while fy_index < 6 and (len(to_append) <=8):

            count *= assumptions_df.year_over_year_rate[fy_index]
            to_append.append(count)

            fy_index += 1
            
        hs_class += 1 
        df_len = len(start_enrollment)
        start_enrollment.loc[df_len] = to_append

        

    
    
    
    
    
    
```

```python
start_enrollment.head()
```

```python
total = start_enrollment.groupby(['Site']).sum().round(0)
```

```python
total.loc['Grand Total'] = total.sum()

```

```python
total = total.drop('High School Class',axis=1)
```

```python
site_dfs = {}
site_dfs['National'] = total
for site in sites:
    _df = start_enrollment[start_enrollment.Site == site].round(0)
    _df = _df.iloc[:,1:]
    _df = _df.set_index('High School Class')

    
    site_dfs[site] = _df

```

```python
writer = pd.ExcelWriter('Growth Model V6.xlsx', engine='xlsxwriter')

for site, df in site_dfs.items():
    df.to_excel(writer, sheet_name=site)
    
    

```

```python
writer.save()

```

```python

```
