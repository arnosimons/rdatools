# -*- coding: utf-8 -*-
"""
functions.py

Written by Arno Simons

Released under GNU General Public License, version 3.0

Copyright (c) 2016-2017 Arno Simons

This file is part of RDAtools.

RDAtools is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RDAtools is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with RDAtools.  If not, see <http://www.gnu.org/licenses/>.

"""


import re
import textract
import textacy
import collections
import itertools
import ftfy
import warnings
from rdatools.constants import *
from rdatools.constants import _YEAR
import networkx as nx

### deal with unicode shit somehow (sonst muckt text = unicode(textract.process(path)) in read_text() rum)
import sys
reload(sys)
sys.setdefaultencoding(u'utf-8')


def sliding_window(seq, n=2):
	return zip(*(collections.deque(itertools.islice(it, i), 0) or it
        for i, it in enumerate(itertools.tee(seq, n))))

# def co_words(list_of_word_lists, width=4,  directed=False, stops=[]):
# 	G = nx.DiGraph() if directed else nx.Graph()
# 	for wl in list_of_word_lists:
# 		for w in sliding_window(wl,width):
# 			print w
# 			for i in w:
# 				print i, type(i)
# 			for i in range(1,width):
# 				if not G.has_edge(w[0].lower(), w[i].lower()):
# 					G.add_edge(w[0].lower(), w[i].lower(), w = float(1) / float(i))
# 				else:
# 					G.edge[w[0].lower()][w[i].lower()]['w'] += float(1) / float(i)
# 	return (e for e in G.edges(data=True) if e[0] not in stops and e[1] not in stops)

def clean_string(string):
	return ' '.join(string.split()).lower()

def clean_attr(attr,ignore_forbidden=False):
	if any(k in attr.iterkeys() for k in FORBIDDENKEYS) and not ignore_forbidden:
		raise KeyError(u"Forbidden attribute keys: {}".format(FORBIDDENKEYS))
	return {unicode(k): 
		(clean_string(unicode(v)) 
			if not k == u'zot_key' 
			and not k == u'name' 
			else unicode(v) # leave zot_keys the way they are (except empty, see below)
			if not k == u'name' else u', '.join(unpack_name(unicode(v)))  # remove wiredly spaced commas
		) 
		for k,v in attr.iteritems()
		if clean_string(unicode(v)) # only keep non-empty kv pairs
		}

def check_attr_format(attr):
	def attr_format_error(k,v):
		raise ValueError(u"{}: {}\n"
			"-> Check documentation for correct formating\n".format(k,repr(v)))
	if attr[u'kind'] == u'actor':
		for k,v in attr.iteritems():
			if k == u'name' and not RE_VALID_NAME.match(v):
				attr_format_error(u'name',v)
			elif k == u'lastname' and not RE_VALID_LASTNAME.match(v):
				attr_format_error(u'lastname',v)
			elif k == u'firstname' and not RE_VALID_FIRSTNAME.match(v):
				attr_format_error(u'firstname',v)
			elif k == u'label' and not RE_VALID_A_LABEL.match(v):
				attr_format_error(u'Actor label',label)
	elif attr[u'kind'] == u'utterance':
		for k,v in attr.iteritems():
			if k == u'label' and not RE_VALID_U_LABEL.match(v):
				attr_format_error(u'Utterance label',label)
			# elif k == u'title' and not RE_VALID_TITLE.match(v):
			# 	attr_format_error(u'title',v)
			elif k == u'date' and not RE_VALID_DATE.match(v):
				if v in [u'forthcoming',u'in press']:
					attr[u'date'] = u'0000'
				else:
					print attr[u'title']
					attr_format_error(u'date',v)

def get_year(date):
	year = re.findall(_YEAR,date)
	if len(year) > 1:
		warnings.warn(u'More than one year found in "{}"'.format(date))
	return year[0] if year else u'0000'

def unpack_name(name):
	return [clean_string(string) for string in name.split(u',')]

def make_u_label(date, title):
	year = get_year(date)
	title = u'_'.join(title[:15].split())
	return u'_'.join([year, title])

def str_length_similarity(s1, s2):
	'''
	returns similarity of string length from 0 to 1
	'''
	if len(s1) == len(s2):
		return 1
	else:
		L = (len(s1), len(s2))
		shorter, longer = min(L), max(L)
		return float(shorter)/float(longer)


# def levenshtein(s1, s2):
# 	"""
# 	returns the Levenshtein distance for two given string 
# 	(source: https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python)
# 	"""
# 	if len(s1) < len(s2):
# 		return levenshtein(s2, s1)
# 	if len(s2) == 0:
# 		return len(s1)
# 	previous_row = range(len(s2) + 1)
# 	for i, c1 in enumerate(s1):
# 		current_row = [i + 1]
# 		for j, c2 in enumerate(s2):
# 			insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
# 			deletions = current_row[j] + 1       # than s2
# 			substitutions = previous_row[j] + (c1 != c2)
# 			current_row.append(min(insertions, deletions, substitutions))
# 		previous_row = current_row
# 	return previous_row[-1]

def adjacency(links, focus):
	""" 
	Return a list of adjacent items from a list of links.
	"""
	d = collections.defaultdict(list)
	unique_links = []
	unique_links_weight = dict()
	unique_links_connector = dict()
	outlist = []
	if False in [isinstance(i, (tuple)) for i in links]:
		links = [tuple(r) for r in links]
	for k, v in set(links):
		if focus == u'target':
			d[k].append(v)
		elif focus == u'source':
			d[v].append(k)
	for i in d:
		for adjacency_link in itertools.combinations(sorted(d[i]),2):
			if adjacency_link not in unique_links:
				unique_links.append(adjacency_link)
				unique_links_weight[str(adjacency_link)] = 1
				unique_links_connector[str(adjacency_link)] = [i]
			else:
				unique_links_weight[str(adjacency_link)] += 1
				unique_links_connector[str(adjacency_link)].append(i)
	for link in unique_links:
		outlist.append(
			# (unicode(link[0]), unicode(link[1]), 
			(link[0], link[1], 
				{u'weight':unicode(unique_links_weight[str(link)]), 
				u'conncectors':{i:c for i,c in enumerate(
				unique_links_connector[str(link)])}
				}
			))
	return outlist

def read_text(path, read_method=u'textacy'):
	if read_method == u'textacy':
		text = unicode(textract.process(path)) # http://textract.readthedocs.io/en/latest/python_package.html
	elif read_method == u'slate':
		with open(path) as f:
			text = unicode(slate.PDF(f))
	return text

def clean_text(text, run_test=False, special=False,
				fix_unicode=False, transliterate=False, no_linebreaks=False, 
				no_accents=False, no_contractions=False, no_urls=False, 
				no_emails=False, no_phone_numbers=False, no_citations=False, 
				no_doi=False, no_date=False, no_currency_symbols=False, 
				no_numbers=False, no_punct=False, lowercase=False, 
				no_lonelychars=False):
	""" Cleans text, building on textacy preprocess functionality
	"""
	if run_test:
		print u'\n\n RAW:\n{}\n{}\n\n{}\n'.format(
			u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	# Basic stuff
	if special:
		text = re.sub(r'\xc2\xa0', u'', text)
		text = re.sub(r'\t|\u', u'', text)
	if fix_unicode is True:
		text = ftfy.fix_text(text, normalization=u'NFC')
		""" 'NFC' combines characters and diacritics written using separate code points,
        e.g. converting "e" plus an acute accent modifier into "é"; unicode
        can be converted to NFC form without any change in its meaning!
        if 'NFKC', additional normalizations are applied that can change
        the meanings of characters, e.g. ellipsis characters will be replaced
        with three periods. 
        (source: http://textacy.readthedocs.io/en/latest/_modules/textacy/preprocess.html#fix_bad_unicode)
		"""
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'fix_unicode', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_linebreaks is True:
		text=RE_LINEBREAKS.sub(' ',text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_linebreaks', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if transliterate is True:
		text = textacy.preprocess.transliterate_unicode(text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'transliterate', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_accents is True: # Redundant if transliterate: http://textacy.readthedocs.io/en/latest/api_reference.html#module-textacy.preprocess
		text = textacy.preprocess.remove_accents(text, method='unicode')
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_accents', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_contractions is True:
		text = textacy.preprocess.unpack_contractions(text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_contractions', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	# Replace urls, emails, citations, etc.
	if no_doi:
		text=RE_DOI.sub('*DOI*', text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_doi', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_urls is True:
		text = textacy.preprocess.replace_urls(text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_urls', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_emails is True:
		text = textacy.preprocess.replace_emails(text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_emails', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_phone_numbers is True:
		text = textacy.preprocess.replace_phone_numbers(text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_phone_numbers', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	# if no_doi:
	# 	text=RE_DOI.sub('*DOI*', text)
	# 	if run_test:
	# 		print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(u'no_doi', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_citations is True:
		text=RE_INTEXT_CITATION_CANDIDATE.sub('*CITATION*',text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_citations', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_date is True:
		text=RE_DATE_ALL.sub('*DATE*', text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_date', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_currency_symbols is True:
		text = textacy.preprocess.replace_currency_symbols(text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_currency_symbols', u'>'*25, repr(text[:1000]), repr(text[-1000:]))

	# More fundamental stuff, but must come at the end, so not to corrupt above cleaning methods
	if no_numbers is True:
		text = textacy.preprocess.replace_numbers(text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_numbers', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_punct is True:
		text = textacy.preprocess.remove_punct(text)
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'no_punct', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if lowercase is True:
		text = text.lower()
		if run_test:
			print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n'.format(
				u'lowercase', u'>'*25, repr(text[:1000]), repr(text[-1000:]))
	if no_lonelychars:
		text=RE_LONELY_CHAR.sub('', text)
	text=re.sub(u'\*', u'', text)
	text = textacy.preprocess.normalize_whitespace(text)
	if run_test:
		print u'\n\n CLEAN --> {}:\n{}\n{}\n\n{}\n{}\n'.format(
			u'whitespace', u'>'*25, repr(text[:1000]), repr(text[-1000:]), u'-'*100)
	return text

