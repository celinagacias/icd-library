#!/usr/bin/env python
# coding: utf-8


import pandas as pd
import numpy as np
import time

#Load selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def page_parser():
    """
    Obtain the codes and descriptions
    on a given page for rules
    """
    body = wd.find_element_by_class_name("body-content")
    container = body.find_element_by_tag_name("ul")
    blocks = container.find_elements_by_tag_name("li")
    content = [b.text for b in blocks if b.text not in ["ICD10Data", "Rules", ""]]
    codes = [c.split(" ")[0] for c in content]
    desc = [" ".join(c.split(" ")[1:]) for c in content]
    rule_codes = pd.DataFrame({'code': codes,
                              'desc': desc})
    rule_codes['rule'] = rule
    time.sleep(2)
    return(rule_codes)

def rule_parser(rule):
    """
    Parse the codes for all the pages 
    for a given rule
    """
    
    #Load the site with codes
    rule_url = rule_urls[rule]
    wd.get(rule_url)
    time.sleep(2)
    
    #Obtain info in current page
    rule_list = []
    codes = page_parser()
    rule_list.append(codes)

    #Loop through pages, if any
    pagination = wd.find_elements_by_class_name("pagination")
    if len(pagination) > 0:
        done_pages = ["1"]

        #Get initial set of pages
        pages = [p for p in pagination[0].find_elements_by_tag_name("li") 
                 if p.get_attribute("class") not in ['active','PagedList-skipToNext']]

        while len(pages) > 0:

            #Scroll to the next page button and click
            p = pages[0]
            pagenum = p.text
            page_button = p.find_element_by_tag_name("a")
            wd.execute_script("return arguments[0].scrollIntoView();", page_button)
            page_button.click()
            time.sleep(2)

            #Obtain the codes
            codes = page_parser()
            rule_list.append(codes)
            done_pages.append(pagenum)

            #Refresh list of page numbers
            pagination = wd.find_elements_by_class_name("pagination")
            pages = [p for p in pagination[0].find_elements_by_tag_name("li") 
                 if p.get_attribute("class") not in ['active','PagedList-skipToNext']]
            pages = [p for p in pages if p.text.strip() not in ["«",'…',"»»"] + done_pages]
    
    print("Codes for rule {} have been scraped".format(rule))
    return(pd.concat(rule_list))


#URLs to Scrape
rule_urls = {'newborn': 'https://www.icd10data.com/ICD10CM/Codes/Rules/Newborn_Codes',
            'pediatric': 'https://www.icd10data.com/ICD10CM/Codes/Rules/Pediatric_Codes',
            'adult': 'https://www.icd10data.com/ICD10CM/Codes/Rules/Adult_Codes',
            'maternity': 'https://www.icd10data.com/ICD10CM/Codes/Rules/Maternity_Codes',
            'female': 'https://www.icd10data.com/ICD10CM/Codes/Rules/Female_Diagnosis_Codes',
            'male': 'https://www.icd10data.com/ICD10CM/Codes/Rules/Male_Diagnosis_Codes',
            'questionable': 'https://www.icd10data.com/ICD10CM/Codes/Rules/Questionable_Dx_Codes'}


rules = []
wd = webdriver.Chrome('chromedriver.exe')

for rule in rule_urls.keys():
    rule_codes = rule_parser(rule)
    rules.append(rule_codes)


#Export as .csv
rules = pd.concat(rules)
rules.to_csv('icd10cm_rules.csv', index=False)


#Parse into format (Optional)
rules['sex'] = np.nan
rules['agemin'] = np.nan
rules['agemax'] = np.nan
rules['accpdx'] = np.nan

    #Set age rules
rules.loc[rules['rule'] == 'maternity', 'agemin'] = 9
rules.loc[rules['rule'] == 'maternity', 'agemax'] = 60
rules.loc[rules['rule'] == 'newborn', 'agemax'] = 0
rules.loc[rules['rule'] == 'pediatric', 'agemax'] = 17
rules.loc[rules['rule'] == 'adult', 'agemin'] = 15

    #Set sex rules
rules.loc[rules['rule'] == 'maternity', 'sex'] = 'F'
rules.loc[rules['rule'] == 'female', 'sex'] = 'F'
rules.loc[rules['rule'] == 'male', 'sex'] = 'M'

    #Set diagnosis rules
rules.loc[rules['rule'] == 'questionable', 'accpdx'] = 'F'

    #Put everything together
rules = rules[[c for c in rules.columns.values if c != 'rule']].groupby(['code','desc']).agg(lambda x: [y for y in x if str(y) != 'nan'][0] if len([y for y in x if str(y) != 'nan']) > 0 else np.nan)
rules.reset_index(inplace=True)

    #Set defaults
rules.loc[rules.accpdx.isnull(), 'accpdx'] = 'Y'
rules.loc[rules.agemin.isnull(), 'agemin'] = 0
rules.loc[rules.agemax.isnull(), 'agemax'] = 124
rules.loc[rules.sex.isnull(), 'sex'] = 'B'

rules.to_csv('icd10cm_rules_table.csv')
