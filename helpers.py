from salesforce_reporting import Connection, ReportParser
import pandas as pd 
import os
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mtick
import matplotlib.pylab as pylab
from textwrap import fill



def load_report(report_id, sf):
    report_details = sf.get_report(report_id)
    parser = ReportParser(report_details)
    report = parser.records_dict()
    df = pd.DataFrame(report)

    while report_details["allData"] == False:
        existing_ids = ",".join(list(df["18 Digit ID"]))
        reportFilter = [
            {
                "value": f"{existing_ids}",
                "operator": "notEqual",
                "column": "Contact.X18_Digit_ID__c",
            }
        ]
        report_details = sf.get_report(report_id, filters=reportFilter)
        _parser = ReportParser(report_details)
        _report = _parser.records_dict()
        _df = pd.DataFrame(_report)
        df = df.append(_df, ignore_index=True)

    return df


def shorten_site_names(df):
    df.loc[:,'Site'] = df.loc[:,'Site'].str.replace('College Track ', "")
    df.loc[:,'Site'] = df.loc[:,'Site'].str.replace('at ', "")
    
    return df 

def shorten_region_names(df):
    df.loc[:,'Region'] = df.loc[:,'Region'].str.replace('College Track ', "")
    df.loc[:,'Region'] = df.loc[:,'Region'].str.replace(' Region', "")
    
    return df
