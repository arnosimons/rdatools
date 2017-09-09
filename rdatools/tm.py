# -*- coding: utf-8 -*-
"""
tm.py

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

class TopicModel(object):
	'''
	This class only implements textacy's original TM handling.
	'''

	def __init__(self, terms_list, vectorizer, method=u'nmf', n_topics=20):
		print '-----> Yo!'
		self.vectorizer = vectorizer
		self.doc_term_matrix = self.vectorizer.fit_transform(terms_list)
		self.model = textacy.tm.TopicModel(method, n_topics=n_topics)
		self.model.fit(self.doc_term_matrix)
		# self.doc_topic_matrix = self.model.transform(self.doc_term_matrix)
		self.doc_topic_matrix = self.model.get_doc_topic_matrix(
			self.doc_term_matrix, normalize=True) # builds on model.transform
		self.id2term = vectorizer.id_to_term

	def __repr__(self):
		return repr(self.model)

	def __len__(self):
		return len(self.model)

	def top_topic_terms(self, topics=-1, top_n=10, weights=False):
		return self.model.top_topic_terms(
			self.id2term , topics=-1, top_n=10, weights=False)

	def top_topic_docs(self, topics=-1, top_n=10, weights=False):
		return self.model.top_topic_docs(
			self.doc_topic_matrix, topics=-1, top_n=10, weights=False)

	def top_doc_topics(self, docs=-1, top_n=3, weights=False):
		return self.model.top_doc_topics(
			self.doc_topic_matrix, docs=-1, top_n=3, weights=False)

	def topic_weights(self):
		return self.model.topic_weights(self.doc_topic_matrix)

	def termite_plot(self, topics=-1, sort_topics_by='index', highlight_topics=None, 
		n_terms=25, rank_terms_by='topic_weight', sort_terms_by='seriation', 
		save=False):
		return self.model.termite_plot(self.doc_term_matrix, self.id2term , 
			topics=-1, sort_topics_by='index', highlight_topics=None, n_terms=25, 
			rank_terms_by='topic_weight', sort_terms_by='seriation', save=False)


