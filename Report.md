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

<!-- #region -->
# FY20 Growth Model Updates

Goal: Evaluate historical data from the past four fiscal years (FY16 -FY19) to determine more accurate averages for the following metrics: 

* **Year to year high school retention rate**
    * i.e. The percent of students who continue on from their Junior to Sophomore year. 


* **Year to year college retention rate**
    * i.e. The percent of students who continue on from their four year to fifth year.
      * Note, this report will treat graduates and inactive students as the same. For example, 100 students are enrolled in their 4th year of college. At the start of their fifth year, 50 students have graduated, and 20 have dropped out (became inactive). The retention rate for 4th -> 5th year will be 30%.


* **Updated college graduation rates by high school class**

___ 
*General Notes* 

* Due to limitations in Salesforce's historical data structures, most of these data points were arrived at via proxy methods to determine if a student was active. For example high school students were considered active if they attended more than 5 classes in an academic year. This will result in numbers that might be slightly off from other historical data, but when possible we verified the numbers were as similar as possible. 


* Likewise, these numbers might overestimate the count of students at a site due to these proxies compared to how Finance or OP just pulls data at a predetermined point in time. If Finance pulled a roster report in March, some of the students included in his analysis would likely have been removed. Moving forward the database is structured to make this type of reporting easier, but that wasn't possible using historical data.
<!-- #endregion -->

```python
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np


import seaborn as sns 
import matplotlib.pyplot as plt
sns.set(font_scale=1.5)
sns.set_style("white")

sns.set_context('talk')

sns.set_palette("pastel")

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

<!-- #region hide_input=false -->
## Key Data and Decision Point
<!-- #endregion -->

```python hide_input=false
average_rates = [54/60,59/60,54/60,45/60, 44/60, .69, .55, .51,.29,.14]
```

```python
growth_model_assumptions = [1, 1, .85, .75, .75, .73, .67, .57, .43, .3]
```

```python
rate_comparison = pd.DataFrame(np.array([growth_model_assumptions, average_rates]),
             columns=['Freshman', 'Sophomore', 'Junior', 'Senior', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5', 'Year 6'], index=['Growth Model Assumptions', 'Historical Averages'])
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
total_enrollent_df= total_enrollent_df.reset_index().sort_values('active_student')
```

### Table 1. Growth Model Assumptions vs Historical Averages

The previous version of the growth model actually had reasonably accurate assumptions for high school enrollment by grade. The only major area it was off was Freshman recruitment rarely hit the total target, but Sophomore year backfill usually returned sites to near capacity. 

The model was much more inaccurate when it came to college. Using historical data, the number of students dropping between Year 2 and Year 3 was much higher than originally estimated, as was the number of students either graduating or dropping after Year 4. 

* Note, the table below shows percentages of the original cohort target. For example, if a site had a target of 100 students, by Year 3, 67 students would be enrolled using the previous assumptions, or 55 students would still be enrolled using the historical averages

```python
rate_comparison.round(2).style.format('{:.0%}')
```

### Table 2. Projections vs Actuals

This table show the projected student count based entirely on the models assumptions compared to the actuals for the past four fiscal years.

Using the historical averages, the student count projections is roughly 20-50 students off per year. 

Using the old growth model assumptions, the student count projections is off by around 300 students per year.

```python
enrollment_target_and_actuals = {'Enrollment Target: 75':[71, 75],
                                 'Enrollment Target: 60':[54,60]
    
}
```

```python
sites = df[['Site', 'enrollment_target']].drop_duplicates()
site_start_year = {'Oakland': 'full',
                   'East Palo Alto': 'full',
                   'Denver': 16, 
                   'San Francisco': 'full',
                   'Sacramento': 15,
                   'Aurora': 12,
                   'Watts': 16,
                   'Boyle Heights':13,
                   'The Durant Center':19,
                   'New Orleans': 11
                  }


```

```python
def determine_total_enrollment_site(site, fy, target_type):
    start_year = site_start_year[site]
    target = sites[sites['Site'] == site]['enrollment_target'].values[0]
    if target_type == 'historical':
        target_actual = enrollment_target_and_actuals[target][0]
        target_index = 1
    elif target_type == 'growth_model':
        target_actual = enrollment_target_and_actuals[target][1]
        target_index = 0
    
    if start_year == 'full':
        return sum(target_actual * rate_comparison.iloc[1])

    else:
        start_year_index = fy - start_year
        if start_year_index >= 0:
            return sum(target_actual * rate_comparison.iloc[target_index,:(1+start_year_index)])
        else: 
            return 0


    
    
```

```python
predictions = {
    'fy 16': [0,0, 2267],
    'fy 17': [0,0, 2431],
    'fy 18': [0,0, 2698],
    'fy 19': [0,0, 3003],
}
```

```python
for key in historical_predictions.keys():
    fy = int(key.split(" ")[1])
    for site in sites['Site']:
        predictions[key][0] += (determine_total_enrollment_site(site,fy,'historical'))
        predictions[key][1] += (determine_total_enrollment_site(site,fy,'growth_model'))
    
```

```python
projections_vs_actuals = pd.DataFrame(predictions, index=['Historical Averages', "Old Growth Model", "Actuals"]).astype(int)
```

```python
projections_vs_actuals.columns = ['FY16', 'FY17', 'FY18', 'FY19']
```

```python
projections_vs_actuals
```

```python
for site in sites['Site']:
    fy16.append(determine_total_enrollment_site(site, 16))
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
total_enrollent_df.at[5, 'Site'] = 'PGC'
total_enrollent_df.at[2, 'Site'] = 'EPA'
```

```python
fig, ax = plt.subplots(figsize=(12, 5))


g = sns.barplot(data=total_enrollent_df, hue='enrollment_target',
                x='Site', y='active_student', ax=ax)


g.set_xticklabels(g.get_xticklabels(), rotation=35)
g.set_title('Average Total High School Enrollment')

g.set_xlabel('Site')
g.set_ylabel('Number of Students')

ax.legend(loc='best', frameon=False)

for p in g.patches:
    g.annotate(format(p.get_height(), '.0f'), (p.get_x() + p.get_width() / 2., p.get_height()),
               ha='center', va='center', xytext=(0, 10), textcoords='offset points')

sns.despine()
```

### Chart 2. Average High School Enrollment By Grade Level

This chart shows the average enrollment by each grade level, broken out by the enrollment target for sites.

Key notes:

* The general enrollment pattern is almost identical regardless of a site's cohort target. This means we can make more general enrollment projections. 
* Sites tend to increase their enrollment from Freshman to Sophomore year, with a small drop off from Sophomore to Junior year, but then a major (16%) decline from Junior to Senior year. 

```python
by_grade_df = df_active_students.groupby(
    ["Site", "Grade (AT)", "Global Academic Year", "enrollment_target"], as_index=False
).sum()

# removing grades with less than 5 students as this could skew the results

by_grade_df = by_grade_df[by_grade_df.active_student > 5]


```

```python
def determine_percent_of_capacity(enrollment_target, active_student):
    if enrollment_target == 'Enrollment Target: 60':
        return active_student / 60 
    elif enrollment_target == 'Enrollment Target: 75':
        return active_student / 75
```

```python
by_grade_df['enrollment_percentage'] = by_grade_df.apply(
    lambda x: determine_percent_of_capacity(x['enrollment_target'], x['active_student']), axis=1)
```

```python
grade_order = ["9th Grade", "10th Grade", "11th Grade", "12th Grade"]

by_grade_df_table = by_grade_df.pivot_table(
    index=["enrollment_target","Grade (AT)"], values="active_student", aggfunc="mean"
)

by_grade_df_table["pct_change"] = by_grade_df_table[
    "active_student"
].pct_change()

by_grade_df_table =  by_grade_df_table.reindex(grade_order, level='Grade (AT)')
```

```python
by_grade_df_table = by_grade_df_table.reset_index()
```

```python
by_grade_df_table['enrollment_percentage'] = by_grade_df_table.apply(
    lambda x: determine_percent_of_capacity(x['enrollment_target'], x['active_student']), axis=1)
```

```python
fig, ax = plt.subplots(figsize=(14, 6))

g = sns.barplot(data=by_grade_df_table, hue='enrollment_target',
                x='Grade (AT)', y='enrollment_percentage', ax=ax)

g.set_xlabel('Grade')
g.set_ylabel('% of Students')
ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0., frameon=False)


ax.set_yticklabels(['{:,.0%}'.format(x) for x in ax.get_yticks()])


sns.despine()

for p in g.patches:
    g.annotate(format(p.get_height(), '.0%'), (p.get_x() + p.get_width() / 2., p.get_height()),
               ha='center', va='center', xytext=(0, 10), textcoords='offset points')
```

## College Data


### Chart 3. Average College Enrollment By Region and College Year
 
These charts display the average college enrollment for the sites contained in each CT region. More mature regions, NOLA and Nor Cal, clearly have a similar trend in college numbers compared to younger regions. 

Note, each bar represents the percent of enrolled students from the original freshman class - thus the first bar for each region will be 100%. 

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
ps_year_count_grouped['Percent of Freshman Cohort'] = ps_year_count_grouped.groupby('Region')[True].apply(lambda x: x.div(x.iloc[0]).subtract(1).add(1))

```

```python
ps_year_count_grouped.loc[ps_year_count_grouped['Percent of Freshman Cohort'] == 0, 'Percent of Freshman Cohort'] = 1
```

```python

g = sns.catplot(data=ps_year_count_grouped, x='Grade (AT)',
            y='Percent of Freshman Cohort', col='Region', kind='bar', height=10, aspect=.75);
for ax in g.axes.flat:
    ax.set_title(ax.get_title(), fontsize='large')
#     ax.set_ylabel("Percent of Freshman Cohort",fontsize=22)
    ax.set_xlabel("",fontsize=22)
    ax.tick_params(labelsize=22)

        
    for p in ax.patches:
        ax.annotate(format(p.get_height(), '.0%'), (p.get_x() + p.get_width() / 2., p.get_height()),
               ha='center', va='center', xytext=(0, 10), textcoords='offset points')
        ax.set_yticklabels(['{:,.0%}'.format(x) for x in ax.get_yticks()])


    
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
              ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(26)
    

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

grad_rates_class.round(2).style.format('{:.0%}')
```

```python
grad_rates_region = create_rate_table(df2, ["Region"], 1, list(range(4, 8)))
grad_rates_region.round(2).style.format('{:.0%}')
```

```python
# Year 2 Calculation
pre_year_rate = .75
previous_year = 60*pre_year_rate

this_year_rate = .085
# previous_year * (1-this_year_rate) / 60
```

```python
# Year 3 Calculation
pre_year_rate = .69
previous_year = 60*pre_year_rate

this_year_rate = .1925
# previous_year * (1-this_year_rate) / 60

```

```python
# Year 3 Calculation
pre_year_rate = .55
previous_year = 60*pre_year_rate

this_year_rate = .07
# previous_year * (1-this_year_rate) / 60

```

```python
# Year 5 Calculation
pre_year_rate = .51
previous_year = 60*pre_year_rate

this_year_rate = .43
# previous_year * (1-this_year_rate) / 60

```

```python
# Year 6 Calculation
pre_year_rate = .29
previous_year = 60*pre_year_rate

this_year_rate = .49
# previous_year * (1-this_year_rate) / 60

```

```html
<script src="https://cdn.rawgit.com/parente/4c3e6936d0d7a46fd071/raw/65b816fb9bdd3c28b4ddf3af602bfd6015486383/code_toggle.js"></script>

```

```html

<style>
div.prompt {display:none}


h1, .h1 {
    font-size: 33px;
    font-family: "Trebuchet MS";
    font-size: 2.5em !important;
    color: #2a7bbd;
}

h2, .h2 {
    font-size: 10px;
    font-family: "Trebuchet MS";
    color: #2a7bbd; 
    
}


h3, .h3 {
    font-size: 10px;
    font-family: "Trebuchet MS";
    color: #5d6063; 
    
}

.rendered_html table {

    font-size: 14px;
}

.output_png {
  display: flex;
  justify-content: center;
}

table {
    display: inline-block
}

</style>
```
