# -*- coding: utf-8 -*-
"""
corpus.py

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


import textacy


class Corpus(textacy.Corpus):

	def __init__(self, lang=u'en'):
		textacy.Corpus.__init__(self, lang=u'en')

	def stopwords(self, case_sensitive=True):
		if case_sensitive == True:
			return sorted([l.orth_ for l in self.spacy_lang.vocab if l.is_stop])
		elif case_sensitive == False:
			return sorted(set([l.lower_ for l in self.spacy_lang.vocab if l.is_stop]))
		else:
			raise ValueError(u'keyword argument "case_sensitive" must be True or False.')
		# return sorted(list(self._stopwords))

	def add_stopwords(self,words,case_sensitive=True):
		print u'\n Adding stopwords:', words
		for word in words:
			if case_sensitive:
				self.spacy_lang.vocab[unicode(word.lower())].is_stop = True
				self.spacy_lang.vocab[unicode(word.upper())].is_stop = True
				self.spacy_lang.vocab[unicode(word.title())].is_stop = True
			else:
				self.spacy_lang.vocab[unicode(word)].is_stop = True

	def remove_stopwords(self,words,case_sensitive=True):
		print u'\n Removing stopwords:', words
		for word in words:
			if case_sensitive:
				self.spacy_lang.vocab[unicode(word.lower())].is_stop = False
				self.spacy_lang.vocab[unicode(word.upper())].is_stop = False
				self.spacy_lang.vocab[unicode(word.title())].is_stop = False
			else:
				self.spacy_lang.vocab[unicode(word)].is_stop = False

