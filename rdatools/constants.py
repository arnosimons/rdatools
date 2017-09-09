# -*- coding: utf-8 -*-
"""
constants.py

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


A_GRAMMARS = {
	u'ln,fn;': u'lastname, firstname;',
	u'ln,fn,': u'lastname, firstname,',
	u'fn ln,': u'firstname lastname,',
	u'fn ln;': u'firstname lastname;',
	u'ln;': u'lastname;',
	u'ln,': u'lastname,'
	}
C_GRAMMARS = {
	u'a/y/t/r': u'author/year/title/rest',
	u'a/t/y/r': u'author/title/year/rest',
	u'y/a/t/r': u'year/author/title/rest',
	u'y/t/a/r': u'year/title/author/rest',
	u't/a/y/r': u'title/author/year/rest',
	u't/y/a/r': u'title/year/author/rest'
	}
DEFAULT_A_GRAMMAR = u'ln,fn;'
DEFAULT_C_GRAMMAR = u'a/y/t/r'
ZOT_TEMPLATE_TXT = {
	u'contentType': u'text/plain', 
	u'itemType': u'attachment', 
	u'title': u'', 
	u'accessDate': u'', 
	u'linkMode': u'linked_file', 
	u'charset': u'', 
	u'relations': {}, 
	u'note': u'', 
	u'url': u'', 
	u'path': u'', 
	u'tags': []
	}

FORBIDDENKEYS = [
	u'kind',
	u'label',
	u'manual_if',
	]
NOFIRSTNAME = u'_firstname'
# NONAMECHARS = (c for c in u',.?!@#$%^&*()+=:;"\'`~') # more chars?


RE_ESCAPE = re.compile(r'|'.join([r"(\\)'",r'(\\)"']))
RE_CHAR = re.compile(r'[\'",/:)(.&%\[\]\\*+-]')
RE_LONELY_CHAR = re.compile(r'(?<=\b)'
	+r'[bcdefghjklmnopqrstuvwxyzBCDEFGHJKLMNOPQRSTUVWXYZ](?=\b)')
RE_NUM = re.compile(r'[\d]+')
RE_P_TAGS = re.compile(r'<p>|</p>| ( )')
RE_AMP = re.compile(r'&amp;')
RE_CIT_LINEBREAKS = re.compile(r'<br />|<br>|<br/>|\r|\v')
RE_LINEBREAKS = re.compile(r'<br />|<br>|<br/>|\r|\v|\n')
RE_DOUBLE_SPACE = re.compile(r'\s+')
RE_CLEAN_DOUBLELINEBREAK = re.compile(r'\n([\s]*\n)') # yellow brackets needed?
RE_EMPTY_END_OF_STRING = re.compile(r'\n[\s]*$')
RE_EMPTY_END_OF_LINE = re.compile(r'[ \t]+\n')
RE_FORTHCOMING = re.compile(r'forthcoming|Forthcoming|FORTHCOMING|'\
	r'In Print|in print|IN PRINT')
RE_INTEXT_CITATION_CANDIDATE = re.compile(
	r'\([^()]*(?:19|20)\d\d[a-f]*[^()]*\)')
RE_DOI = re.compile(r'[dD][oO][iI]: *10[0-9./():<>;A-Za-z-]+|'\
	r'http://dx.doi.org/10[0-9./():<>;A-Za-z-]+')
_MONTH = r'(?:[Jj][aA][nN][uU]*[aA]*[rR]*[yY]*|'\
	r'[fF][eE][bB][rR]*[uU]*[aA]*[rR]*[yY]*|'\
	r'[mM][aA][rR][cC]*[hH]*|'\
	r'[Aa][Pp][Rr][Ii]*[Ll]*|'\
	r'[Mm][aa][Yy]|[jJ][uU][nN][eE]*|'\
	r'[jJ][uU][lL][yY]*|[aA][uU][gG][uU]*[sS]*[tT]*|'\
	r'[sS][eE][pP][tT]*[eE]*[mM]*[bB]*[eE]*[rR]*|'\
	r'[oO][cC][tT][oO]*[bB]*[eE]*[rR]*|'\
	r'[nN][oO][vV][eE]*[mM]*[bB]*[eE]*[rR]*|'\
	r'[dD][eE][cC][eE]*[mM]*[bB]*[eE]*[rR]*)'
_YEAR = r'\d\d\d\d'
_RECENTYEAR = r'(?:19|20)\d\d'
_MODERNYEAR = r'(?:15|16|17|18|19|20)\d\d'
_DAYOFMONTH = r'(?:0*[1-9]|1\d|2\d|30|31)'

_DATE_MY = r' '.join([_MONTH, _RECENTYEAR])
_DATE_DMY = r' '.join([_DAYOFMONTH, _MONTH, _RECENTYEAR])
_DATE_DMY_NUM = \
	r'(?:0*[1-9]|1\d|2\d|30|31)(?:/|-)(?:0*[1-9]|1[012])(?:/|-)(?:19|20)\d\d'

_DATE_MDY = r' '.join([_MONTH, _DAYOFMONTH+r',*', _RECENTYEAR])
_DATE_YMD = r' '.join([_RECENTYEAR, _MONTH, _DAYOFMONTH])
_DATE_YMD_NUM = \
	r'(?:19|20)\d\d(?:/|-)(?:0*[1-9]|1[012])(?:/|-)(?:0*[1-9]|1\d|2\d|30|31)'


_DATE_ALL = r'|'.join(
	[_DATE_MY, _DATE_DMY, _DATE_YMD, _DATE_MDY, _DATE_YMD_NUM, _DATE_DMY_NUM])



RE_DATE_MY = re.compile(r'\b'+_DATE_MY+r'\b')
RE_DATE_DMY = re.compile(r'\b'+_DATE_DMY+r'\b')
RE_DATE_MDY = re.compile(r'\b'+_DATE_MDY+r'\b')
RE_DATE_ALL = re.compile(r'\b'+_DATE_ALL+r'\b')
RE_MONTH = re.compile(r'\b'+_MONTH+r'\b')
RE_YEAR = re.compile(r'\b'+_YEAR+r'\b')
RE_RECENTYEAR = re.compile(r'\b'+_RECENTYEAR+r'\b')
RE_DAYOFMONTH = re.compile(r'\b'+_DAYOFMONTH+r'\b')

RE_VALID_DATE = re.compile(u'^'+_YEAR+'|'+_DATE_ALL+'$') # other formats?


RE_VALID_FIRSTNAME = re.compile(u'^[-a-zßäëïöüáéíóúàèìòùâêîôûøæå \.]*$') # more chars?
RE_VALID_LASTNAME = re.compile(u'^[-a-zßäëïöüáéíóúàèìòùâêîôûøæå ]*$') # more chars?
_NAME = u'[a-zßäëïöüáéíóúàèìòùâêîôûøæå][-a-zßäëïöüáéíóúàèìòùâêîôûøæå, \.]*'
RE_VALID_NAME = re.compile(u'^'+_NAME+'$') # more chars?

RE_VALID_A_LABEL = re.compile(u'^'+_NAME+'\**$') # more chars?
RE_VALID_U_LABEL = re.compile(u'^'+_YEAR+'_*((?<=_).*)\**$') # other formats ?
