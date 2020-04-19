import pandas as pd
import numpy as np
import pandas_gbq as gbq
import requests
import json

client_id = "**"
client_secret = "**"

def authenticate(
	client_id, 
	client_secret, 
	token_endpoint='https://icdaccessmanagement.who.int/connect/token',
	scope='icdapi_access',
	grant_type='client_credentials'
	):
	"""
	Set data to post
	"""

 	payload = {'client_id': client_id, 
 			   'client_secret': client_secret, 
		 	   'scope': scope, 
		 	   'grant_type': grant_type}
 	r = requests.post(token_endpoint, data=payload, verify=True).json()
 	token = r['access_token']
 	headers = {'Authorization': 'Bearer '+token,
 	'Accept': 'application/json', 
 	'Accept-Language': 'en',
 	'API-Version': 'v2'}
 	return(headers)

#Parsing helper functions
def request_json(uri):
	"""
	Obtain the JSON from a given URI
	"""
	obj = requests.get(uri, headers=headers, verify=True).json()
	return(obj)

def chapter_attributes_parser(chapter_json):
	"""
	Given the JSON of a chapter,
	parse the chapter attributes and title
	"""
	chapter_att = {'code': chapter_json['code'],
	               'title': chapter_json['title']['@value']}
	for addtl in ['inclusion','exclusion']:
	if addtl in chapter_json.keys():
	 	chapter_att[addtl] = "; ".join([e['label']['@value'] \
	 		for e in chapter_json[addtl]])
	else:
	 	chapter_att[addtl] = 'None'
	chapter_code = chapter_att['code']
	return(chapter_att, chapter_code)

def code_parser(cat_json, window_title, 
                chapter_code, cat_title):
	"""
	Parse the JSON for an ICD10 code
	and add names
	"""
	code = {'code': cat_json['code'],
	        'title': cat_json['title']['@value'],
	        'category': cat_title,
	        'window': window_title,
	        'chapter': chapter_code}
	return(code)

def window_parser(window_child, window_title, chapter_code):
	"""
	Return the parsed set of codes for a
	given window URI
	"""
	headers = authenticate()
	window_codes = []
	for cat_uri in window_child:

	#Parse the category
	cat_json = request_json(cat_uri)
	cat_title = cat_json['title']['@value']
	cat = code_parser(cat_json, window_title, chapter_code, cat_title)
	window_codes.append(cat)

	#Get all codes in the category
	if 'child' in cat_json.keys():
	 	codes = [code_parser(request_json(cat2_uri), window_title, chapter_code, cat_title) \
	 			for cat2_uri in request_json(cat_uri)['child']]
	 	window_codes += codes
	return(window_codes)

def chapter_parser(chapter_uri):
	"""
	Given the chapter URI, obtain the chapter info
	and list of codes as dataframes 
	"""
 	chapter_codes = []
 	chapt = request_json(chapter_uri)
 	chapter_att, chapter_code = chapter_parser(chapt)

  	# Parse the codes within the windows
 	for window_uri in chapt['child']:
  		window = request_json(window_uri)
    	window_title = window['title']['@value']
    	chapter_codes += window_parser(window['child'], window_title, chapter_code)

	#Convert to dataframe
	chapter_dump = json.loads(json.dumps(chapter_att))
	chapter_df = pd.DataFrame(chapter_dump, index=[0])

	code_dump = json.loads(json.dumps(chapter_codes))
	code_df = pd.DataFrame(code_dump)
	return(chapter_df, code_df)

def generate_codes():
	"""
	Loop through the chapters and obtain all
	chapter attributes and codes
	"""

	headers = authenticate(headers)
	icd10_uri = 'https://id.who.int/icd/release/10/2016'
	r10_top = requests.get(icd10_uri, headers=headers, verify=True).json()

	all_chapters = []
	all_codes = []

	#Loop through each of the chapters
	for chapter_uri in r10_top['child']:
	  try:
	    chapter_info, code_list = chapter_parser(chapter_uri)
	  except:
	    headers = authenticate(client_id, client_secret)
	    chapter_info, code_list = chapter_parser(chapter_uri)
	  all_chapters.append(chapter_info)
	  all_codes.append(code_list)

	all_chapters = pd.concat(all_chapters)
	all_codes = pd.concat(all_codes)
	return(all_chapters, all_codes)
