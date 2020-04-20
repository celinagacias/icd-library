import pandas as pd
import numpy as np
import time

#Load selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
wd = webdriver.Chrome('chromedriver.exe')

#Load the main website
def scrape_icd9cm(url="http://www.icd9data.com/2012/Volume3/default.htm"):
  """
  Obtain the icd-9-cm codes from icd9data.com
  with rests in between clicks
  """

  #Load main page with list of code windows
  icd9_main = wd.get("http://www.icd9data.com/2012/Volume3/default.htm")
  codelist = wd.find_element_by_class_name("codeList")
  code_windows = codelist.find_elements_by_tag_name("li")
  num_windows = len(code_windows)

  codes_all = []

  for win_num in range(0, num_windows):
      codelist = wd.find_element_by_class_name("codeList")
      code_windows = codelist.find_elements_by_tag_name("li")
      window = code_windows[win_num]
      
      window_name = window.text
      window.find_element_by_class_name("identifier").click()
      time.sleep(1)
      
      #Get the list of code blocks
      blocks = wd.find_element_by_class_name("codeList")
      block_links = blocks.find_elements_by_class_name("identifier")
      num_blocks = len(block_links)
      
      #Get the codes within the block
      for num_block in range(0, num_blocks):
          blocks = wd.find_element_by_class_name("codeList")
          block_links = blocks.find_elements_by_class_name("identifier")
          block = block_links[num_block]
          block.click()
          time.sleep(1)
          
          codes = [a.text for a in wd.find_elements_by_class_name("codeLink")]
          descs = [a.text for a in wd.find_elements_by_class_name("threeDigitCodeListDescription")]
          
          #Parse the codes into a dataframe
          codes_df = pd.DataFrame({'code': codes, 'desc': descs})
          codes_df['code'] = codes_df.code.apply(lambda x: x.replace("2012 ICD-9-CM Procedure Code ", ""))
          codes_df['desc'] = codes_df.desc.apply(lambda x: x.split("\n"))
          codes_df[['desc', 'remark']] = pd.DataFrame(codes_df['desc'].values.tolist())
          codes_df['window'] = window_name
          codes_all.append(codes_df)
          
          wd.back()
          time.sleep(1)
      
      wd.back()
      time.sleep(1)

    #Put all the codes together
    icd9cm = pd.concat(codes_all)
    return(icd9cm)