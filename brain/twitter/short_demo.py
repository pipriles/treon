#!/usr/bin/env python
# Hello, short demo

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# Change this as you wish
USER = 'kindafunnyvids'
BASE_URL = 'https://twitter.com/'

URL = BASE_URL + USER

def main():

	print('Opening the browser...')
	browser = webdriver.Chrome()
	
	print('Wait until the page loads...')
	browser.get(URL)

	body = browser.find_element_by_tag_name('body')
	tweets = body.find_elements_by_css_selector('.tweet')

	print('Fetching tweets:')
	for t in tweets:
		print(t.text, '\n')
		# Handle infinite scroll

if __name__ == '__main__':
	main()
	