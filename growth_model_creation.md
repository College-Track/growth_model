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
df = pd.read_csv('data/raw/enrollment_june_2020.csv')

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
hs_assumptions = [.9, 1.07, .93, .83]
ps_assumptions = [.98, .91, .81, .93, .57, .51, .5, .5]

assumptions = hs_assumptions + ps_assumptions

assumptions

grade = ['Freshman', 'Sophomore', 'Junior', 'Senior',
         'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5', 'Year 6', "Year 7", "Year 8"]
```

```python

```

```python
assumptions_df = pd.DataFrame(list(zip(grade, assumptions)), columns=['grade', 'year_over_year_rate'])
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
projected_fy = ["FY21", "FY22", "FY23", "FY24", "FY25","FY26"]
```

```python
df = df[df['High School Class'] <= 2023]
```

```python
start_enrollment = df.pivot_table(index=['Site', 'High School Class'], values='18 Digit ID', aggfunc='count').reset_index()
```

```python
start_enrollment = start_enrollment.rename(columns={'18 Digit ID': "FY20"})
```

```python
start_enrollment = start_enrollment.reindex(columns = start_enrollment.columns.tolist() + projected_fy)

```

```python
def update_projections(site, hs_class, columns, starting_count):
    for fy in columns:
        year = int(fy.split('FY')[1])
        grade_index = determine_grade_index(hs_class, year)
        if grade_index > 11:
            continue
        
        projected_count = (assumptions_df.year_over_year_rate[grade_index] * starting_count).round(0)
        start_enrollment.loc[(start_enrollment.Site == site) & (start_enrollment['High School Class'] == hs_class), fy] = projected_count
        starting_count = projected_count
        
    
```

```python
start_enrollment.apply(lambda x: update_projections(
    x['Site'], x['High School Class'], start_enrollment.columns[3:], x['FY20']), axis=1)
```

```python
sites = list(set(df.Site))
```

```python
sites.append('Crenshaw')
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
start_enrollment = start_enrollment.round(0)
```

```python
hs_enrollment = start_enrollment.copy()
```

```python
ps_enrollment = start_enrollment.copy()
```

```python
def apply_enrollment_adjust_on_columns(row, adjust_type):
    for column in row.index:
        # if column string starts with "FY"
        if column[0:2] == "FY":
            row[column] = adjust_enrollment_count(row['High School Class'], column, adjust_type, row[column])
    return row
```

```python
def adjust_enrollment_count(hs_class, fy_year, adjust_type, current_enrollment):
    fy_int = int(fy_year.split("FY")[1])
    fy_int += 2000
    
    if adjust_type == "hs":
        # Example, hs_class is 2019 and FY is 2021. student shouldn't be counted as a HS student 
        if hs_class < fy_int:
            return np.nan
        else:
            return current_enrollment
    if adjust_type == "ps":
        # example. hs class is 2021 and FY is 2020, student shouldn't be in college yet
        if hs_class >= fy_int:
            return np.nan
        else:
            return current_enrollment

        
```

```python
hs_enrollment = hs_enrollment.apply(lambda x: apply_enrollment_adjust_on_columns(x, "hs"), axis=1)
```

```python
ps_enrollment = ps_enrollment.apply(lambda x: apply_enrollment_adjust_on_columns(x, "ps"), axis=1)
```

```python
hs_enrollment = hs_enrollment.dropna(subset=hs_enrollment.columns[2:],how='all')
```

```python
ps_enrollment = ps_enrollment.dropna(subset=hs_enrollment.columns[2:],how='all')
```

```python
def determine_year_1_estimate(current_enrollment, hs_class):
    grade_index = determine_grade_index(hs_class, 20)
    
    
    if grade_index == 4:
        return round(current_enrollment,0)
    elif grade_index >=9:
        return 0
    else:
        estimated_enrollment = current_enrollment
        while grade_index > 4:

            estimated_enrollment /= assumptions[grade_index]
            grade_index -= 1
        return round(estimated_enrollment,0)
    
```

```python
# region_grad_rate = {
#     "Nor Cal":[.3,.45,.48,.54],
#     "LA":[.21,.28,.32,.34],
#     "Other":[.29,.42,.46,.51],
# }

region_grad_rate = {
    "Nor Cal":[.3,.15,.03,.06],
    "LA":[.21,.07,.04,.02],
    "Other":[.29,.13,.04,.05],
}
```

```python
def determine_region(site):
    sites_and_regions = {"Nor Cal": ['Sacramento','Oakland','San Francisco','East Palo Alto'],
                    "LA":['Watts','Boyle Heights','Crenshaw'],
                    "NOLA":["New Orleans"],
                    "DC":['The Durant Center','Ward 8',],
                    "CO":['Aurora','Denver']}
    
    for key, items in sites_and_regions.items():
        if site in items:
            return key
```

```python
def determine_grad_fy(hs_class):
    four_year = hs_class + 4 - 2000
    five_year = hs_class + 5 - 2000
    six_year = hs_class + 6 - 2000
    all_year = hs_class + 7 - 2000

    fy_years = [four_year,five_year,six_year,all_year]
    return fy_years
```

```python
def estimate_grad_count(row, region_grad_rate):
    for column in row.index[2:]:
        column_value = row[column]
        if pd.isna(row[column]):
            continue
        else:
            first_column = column
            break
        
    start_enrollment = determine_year_1_estimate(row[first_column], row['High School Class'])
    
    region = determine_region(row['Site'])
    
    if region not in list(region_grad_rate.keys()):
        region = "Other"
    
    estimated_graduates = int(start_enrollment) * np.array(region_grad_rate[region])
    
    
    graduating_fiscal_years = determine_grad_fy(row['High School Class'])
    
    for column in row.index[2:]:
        row[column] = np.nan
    
    counter = 0 
    for i in range(len(graduating_fiscal_years)):
        if graduating_fiscal_years[i] > 26 or graduating_fiscal_years[i] < 20:
            counter += 1

            continue
        else:
            
            column_name = (f'FY{graduating_fiscal_years[i]}')
            
            row[column_name] = estimated_graduates[i]
            
#             if counter == 3 and graduating_fiscal_years[i] < 26:
                
#                 remaining_years = 26 - graduating_fiscal_years[i]
#                 for j in range(remaining_years):
#                     new_fy = graduating_fiscal_years[i] + j + 1
#                     column_name = (f'FY{new_fy}')
#                     row[column_name] = estimated_graduates[i]
                    
                
                
        counter += 1 
    return row
    
    
```

```python
graduates = ps_enrollment.copy()

```

```python
graduates = graduates.apply(lambda x: estimate_grad_count(x, region_grad_rate),axis=1 )
```

```python
graduates = graduates.dropna(subset=graduates.columns[2:],how='all')
```

```python
graduates = graduates.round(0)
```

```python
national_hs = hs_enrollment.groupby(['Site']).sum().round(0)
national_ps = ps_enrollment.groupby(['Site']).sum().round(0)
national_grads = graduates.groupby(['Site']).sum().round(0)
```

```python
def create_grand_total(df):
    df.loc["Grand Total"] = df.sum()
    return df



```

```python
national_hs.drop("High School Class", inplace=True, axis=1)
national_ps.drop("High School Class", inplace=True, axis=1)
national_grads.drop("High School Class", inplace=True, axis=1)
```

```python
total = pd.DataFrame({'Total High School': national_hs.sum(),
              "Total Post-Secondary": national_ps.sum(),
             }).transpose()
```

```python
total.loc['Total Served'] = total.sum()
```

```python
total.loc['Total Graduates'] = national_grads.sum().transpose()
```

```python
national_hs = create_grand_total(national_hs)
national_ps = create_grand_total(national_ps)
national_grads = create_grand_total(national_grads)
```

```python
site_dfs = []
site_dfs.append({"site": "Summary", "df": total})

site_dfs.append({'site': "National", "hs": national_hs, "ps": national_ps, "grads": national_grads})

for site in sites:

    _hs = hs_enrollment[hs_enrollment.Site == site].iloc[:,1:].set_index('High School Class')
    _hs = create_grand_total(_hs)
    _ps = ps_enrollment[ps_enrollment.Site == site].iloc[:,1:].set_index('High School Class')
    _ps = create_grand_total(_ps)
    _grads = graduates[graduates.Site == site].iloc[:,1:].set_index('High School Class')
    _grads = create_grand_total(_grads)
    site_dfs.append({"site": site, "hs": _hs, "ps": _ps, "grads" : _grads})

    
```

```python
def write_df_to_sheet(df, start_row, sheet_name, writer, header_format, index_format):
    df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, startcol=1, header=False, index=False)
    
    worksheet = writer.sheets[sheet_name]
    worksheet.write(start_row-1, 0, "High School Class", header_format)
    
    

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(start_row-1, col_num+1, value, header_format)


    for row_num, value in enumerate(df.index.values):
        worksheet.write(start_row + row_num, 0, value, index_format)
        
        

```

```python
writer = pd.ExcelWriter('Growth Model V6.xlsx', engine='xlsxwriter')
workbook = writer.book
workbook.formats[0].set_font_size(14)


sheet_format = workbook.add_format()

sheet_format.set_border(0)

# sheet_format = workbook.add_format({"border":"None"})

section_header = workbook.add_format(
    {'bold': True, "font_color": "white", "bg_color": "black", "font_size": 14})

chart_header = workbook.add_format({"bg_color": "#C0C0C0", "bold": True, "font_size":14})


chart_index = workbook.add_format({"bold": True, "align": "left", "font_size":14})


# table = workbook.add_format({})


for site_dict in site_dfs:

    if site_dict['site'] == "Summary":
        write_df_to_sheet(site_dict['df'], 2, site_dict['site'], writer, chart_header, chart_index)
        worksheet = writer.sheets[site_dict['site']]
        worksheet.set_column('A:A', 30, sheet_format)
        worksheet.set_column('B:H', 15, sheet_format)
        
        date = datetime.now().strftime("%m/%d/%Y")
        worksheet.write("A1", "Date Pulled:",chart_index)
        worksheet.write("B1",date ,chart_index)

    else:
        start_row_ps = len(site_dict['hs']) + 5
        start_row_grads = len(site_dict['ps']) + 5 + start_row_ps

        write_df_to_sheet(
            site_dict['hs'], 2, site_dict['site'], writer, chart_header, chart_index)

        write_df_to_sheet(site_dict['ps'], start_row_ps+1,
                          site_dict['site'], writer, chart_header, chart_index)

        write_df_to_sheet(site_dict['grads'], start_row_grads,
                          site_dict['site'], writer, chart_header, chart_index)

#         site_dict['grads'].to_excel(writer, sheet_name=site_dict['site'], startrow=start_row_grads)

        worksheet = writer.sheets[site_dict['site']]

        # Section header styling
        worksheet.merge_range(0, 0, 0, 7, 'High School', section_header)
        worksheet.merge_range(start_row_ps-1, 0, start_row_ps-1,
                              7, 'Post-Secondary', section_header)
        worksheet.merge_range(start_row_grads-1, 0,
                              start_row_grads-1, 7, 'Graduates', section_header)

        # Table header styling


#         worksheet.write('A2:A9', "200", sheet_format)

#         worksheet.set_column(,7,)

        worksheet.set_column('A:A', 30, sheet_format)
        worksheet.set_column('B:H', 15, sheet_format)
        workbook.formats[0].set_font_size(14)
```

```python
writer.save()
```

```python

```
