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

### Data Sources
- File 1 Retention Rate for High School: https://ctgraduates.lightning.force.com/lightning/r/Report/00O1M000007QxBMUA0/view
- File 2 College Grad By Class:  https://ctgraduates.lightning.force.com/lightning/r/Report/00O1M000007QxISUA0/view
- File 3 PS Drop Out:  https://ctgraduates.lightning.force.com/lightning/r/Report/00O1M000007QxUdUAK/view

### Changes
- 02-05-2020 : Started project

```python
# General Setup 
%load_ext dotenv
%dotenv
from salesforce_reporting import Connection, ReportParser
import pandas as pd
from pathlib import Path
from datetime import datetime
import helpers
import os

SF_PASS = os.environ.get("SF_PASS")
SF_TOKEN = os.environ.get("SF_TOKEN")
SF_USERNAME = os.environ.get("SF_USERNAME")

sf = Connection(username=SF_USERNAME, password=SF_PASS, security_token=SF_TOKEN)
```

### File Locations

```python
today = datetime.today()
in_file1 = Path.cwd() / "data" / "raw" / "sf_output_file1.csv"
in_file2 = Path.cwd() / "data" / "raw" / "sf_output_file2.csv"
in_file3 = Path.cwd() / "data" / "raw" / "sf_output_file3.csv"

summary_file = Path.cwd() / "data" / "processed" / "processed_data.pkl"
summary_file2 = Path.cwd() / "data" / "processed" / "processed_data_file2.pkl"
summary_file3 = Path.cwd() / "data" / "processed" / "processed_data_file3.pkl"

active_students = Path.cwd() / "data" / "processed" / "active_students.pkl"
```

### Load Report From Salesforce

```python
# File 1 - Manually loading
# report_id_file1 = "00O1M000007QxBMUA0"
# sf_df = helpers.load_report(report_id_file1, sf)

# File 2 and 3 (As needed)
report_id_file2 = "00O1M000007QxISUA0"
# report_id_file3 = "00O1M000007QxUdUAK"
sf_df2 = helpers.load_report(report_id_file2, sf)
# sf_df3 = helpers.load_report(report_id_file3, sf)
```

#### Save report as CSV

```python
# File 1
# sf_df.to_csv(in_file1, index=False)


# File 2 and 3 (As needed)
sf_df2.to_csv(in_file2, index=False)
# sf_df3.to_csv(in_file3, index=False)

```

### Load DF from saved CSV
* Start here if CSV already exist 

```python
# Data Frame for File 1 - if using more than one file, rename df to df_file1
df = pd.read_csv(in_file1)
df_file2 = pd.read_csv(in_file2)


df_file3 = pd.read_csv(in_file3)
```

### Data Manipulation


#### All Data Frames

```python
# Flagging sites for 60 vs 75 enrollment target


def determine_enrollment_target(site):
    enroll_target_60_sites = ['East Palo Alto', 'New Orleans',
                              'Aurora', 'Sacramento', 'Denver', 'Watts', 'The Durant Center']
    enroll_target_75_sites = ['San Francisco', 'Oakland', 'Boyle Heights']
    
    if site in enroll_target_60_sites:
        return "Enrollment Target: 60"
    elif site in enroll_target_75_sites:
        return "Enrollment Target: 75"
    else:
        return 'Error'
```

```python
# Shortening Site and Region names

df = helpers.shorten_site_names(df)
df = helpers.shorten_region_names(df)
df['enrollment_target'] = df.apply(lambda x: determine_enrollment_target(x['Site']),axis=1)

df_file2 = helpers.shorten_site_names(df_file2)
df_file2 = helpers.shorten_region_names(df_file2)

df_file3 = helpers.shorten_site_names(df_file3)
df_file3 = helpers.shorten_region_names(df_file3)


df_file3['enrollment_target'] = df_file3.apply(lambda x: determine_enrollment_target(x['Site']),axis=1)
```

<!-- #region heading_collapsed=true -->
#### HS Data Frame (File 1)
<!-- #endregion -->

```python hidden=true
# Shortening global academic term names

df.loc[:,"Global Academic Term"] = df.loc[:,"Global Academic Term"].str.replace(" \(Semester\)", "")
```

```python hidden=true
# Determining if a hs counts as active based on if they attended more sessions than the threshold
df['student_counts'] = df.apply(lambda x: True if x['Attended Sessions'] > 5 else False, axis=1)
```

```python hidden=true
df["active_student"] = df.groupby(
    ["Global Academic Year", "18 Digit ID"]
).student_counts.transform(lambda group: group.any())
```

```python hidden=true
df_active_students = df[df.active_student == True]
```

```python hidden=true
df_active_students = df_active_students.groupby(
    ["Global Academic Year", "18 Digit ID"], group_keys=False
).apply(lambda x: x.iloc[0])
df_active_students = df_active_students.drop(
    columns=["Global Academic Year", "18 Digit ID"]
)
df_active_students = df_active_students.reset_index()
```

<!-- #region heading_collapsed=true -->
#### File 2 Cohort Graduation Rate
<!-- #endregion -->

```python hidden=true
# function to determine if a student has been removed from HS enough be evaluated for the year

def determine_grad_year_eligibility(years_removed, existing_value, required_years_removed):
    if years_removed < required_years_removed:
        return "NA"
    else:
        return existing_value
    
```

```python hidden=true
df_file2['Graduated: 4-Year Degree <=5 years'] = df_file2.apply(
    lambda x: determine_grad_year_eligibility(x['Indicator: Years Since HS Graduation'],
                                              x['Graduated: 4-Year Degree <=5 years'],5), axis=1)

df_file2['Graduated: 4-Year Degree <=6 years'] = df_file2.apply(
    lambda x: determine_grad_year_eligibility(x['Indicator: Years Since HS Graduation'],
                                              x['Graduated: 4-Year Degree <=6 years'],6), axis=1)


df_file2['Graduated: 4-Year Degree'] = df_file2.apply(
    lambda x: determine_grad_year_eligibility(x['Indicator: Years Since HS Graduation'],
                                              x['Graduated: 4-Year Degree'],6), axis=1)
```

```python hidden=true
df_file2['Graduated: 4-Year Degree <=5 years'].value_counts()
```

```python hidden=true
df_file2['Graduated: 4-Year Degree <=6 years'].value_counts()
```

```python hidden=true
df_file2['Graduated: 4-Year Degree'].value_counts()
```

#### PS Yearly Drop Out Data Frame (File 3)

```python
# if downloading from Salesforce CSV have to convert 1 and 0 to True False for FY indicators

df_file3['FY17 Student Served'] = df_file3['FY17 Student Served'].astype(bool)
df_file3['FY18 Student Served'] = df_file3['FY18 Student Served'].astype(bool)
df_file3['FY19 Student Served'] = df_file3['FY19 Student Served'].astype(bool)
```

```python
df_file3 = df_file3.drop_duplicates()
```

```python
# Adjusting FYxx student served to only be true if they were served in a PS capacity. 

def determine_ps_fy_served(hs_class, fy, current_status):
    if hs_class >= int(str(20) + str(fy)):
            return False
    else:
        return current_status

```

```python
df_file3['FY17 Student Served'] = df_file3.apply(lambda x: determine_ps_fy_served(x['High School Class'], 17, x['FY17 Student Served']), axis=1)
df_file3['FY18 Student Served'] = df_file3.apply(lambda x: determine_ps_fy_served(x['High School Class'], 18, x['FY18 Student Served']), axis=1)
df_file3['FY19 Student Served'] = df_file3.apply(lambda x: determine_ps_fy_served(x['High School Class'], 19, x['FY19 Student Served']), axis=1)
```

```python
# Creating a proxy for FY16, FY15, and FY14 served. If a student was a sophmore, junior, or senior in FY17
# and marked as served in FY17 then they will be marked as served in their preceeding years. Assumes that if a student 
# was active they will were always active.

def determine_fy_proxy(hs_class, fy17):
    if fy17 == False:
        return [False] * 5
    elif hs_class == 2015:
        return [True] + [False] * 4
    elif hs_class == 2014: 
        return [True] * 2 + [False] * 3
    elif hs_class == 2013:
        return [True] * 3 + [False] * 2
    elif hs_class == 2012:
        return [True] * 4 + [False] * 1
    elif hs_class == 2011:
        return [True] * 5
    else:
        return [False] * 5 
    

```

```python
df_file3['fy16_proxy'], df_file3['fy15_proxy'], df_file3['fy14_proxy'], df_file3['fy13_proxy'], df_file3['fy12_proxy'] = zip(*df_file3.apply(
    lambda x: determine_fy_proxy(x['High School Class'], x['FY17 Student Served']), axis=1))
```

```python
fy_dict_list = [{},{},{},{},{},{},{},{}]

for i in range(8):
    for j in range(6):
        year = (2005 + i + (j + 1))
        year_string = "Year " + str(6 - j)
        fy_dict_list[i][year] = year_string

```

```python
def determine_fy_active_status(fy_index, fy_status, hs_class, grade, fy_dict_list):
    if fy_status == True:
        try:
            if fy_dict_list[fy_index][hs_class] == grade:
                return True
        except:
            pass
            
    else:
        return None
    
    
def determine_year_active_status(hs_class,fy12, fy13,fy14, fy15, fy16, fy17, fy18, fy19, grade, fy_dict_list):
    # Check FY12
    if determine_fy_active_status(0, fy12, hs_class, grade, fy_dict_list) == True:
        return "Unknown"
    
    # Check FY13
    if determine_fy_active_status(1, fy13, hs_class, grade, fy_dict_list) == True:
        return "Unknown"
    
    # Check FY14
    if determine_fy_active_status(2, fy14, hs_class, grade, fy_dict_list) == True:
        return "Unknown"
    
    # Check FY15
    if determine_fy_active_status(3, fy15, hs_class, grade, fy_dict_list) == True:
        return "Unknown"
    
    # Check FY16
    if determine_fy_active_status(4, fy16, hs_class, grade, fy_dict_list) == True:
        return True

    # Check FY17
    if determine_fy_active_status(5, fy17, hs_class, grade, fy_dict_list) == True:
        return True
    
    # Check FY18
    if determine_fy_active_status(6, fy18, hs_class, grade, fy_dict_list) == True:
        return True

    # Check FY19    
    if determine_fy_active_status(7, fy19, hs_class, grade, fy_dict_list) == True:
        return True
    else:
        return False
    
    
```

```python
df_file3 = df_file3[df_file3['High School Class'] >= 2011]
```

```python
df_file3['active_student'] = df_file3.apply(lambda x: determine_year_active_status(
    x['High School Class'],x['fy12_proxy'],x['fy13_proxy'],x['fy14_proxy'],x['fy15_proxy'], x['fy16_proxy'], x['FY17 Student Served'],
    x['FY18 Student Served'], x['FY19 Student Served'], x['Grade (AT)'],
    fy_dict_list), axis=1)
```

### Save output file into processed directory

Save a file in the processed directory that is cleaned properly. It will be read in and used later for further analysis.

```python
# Save File 1 Data Frame (Or master df)
df.to_pickle(summary_file)

df_file2.to_pickle(summary_file2)

df_file3.to_pickle(summary_file3)

df_active_students.to_pickle(active_students)

```
