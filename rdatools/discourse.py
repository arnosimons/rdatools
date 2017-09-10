# -*- coding: utf-8 -*-
"""
discourse.py

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
import subprocess
import textacy
import networkx as nx
import gensim
import warnings
import distance
import unicodedata

from rdatools.constants import *
from rdatools.functions import *
from rdatools.corpus import Corpus
from rdatools.tm import TopicModel

class Discourse(object):

	"""
	A ``Discourse`` contains and manages actors and utterances and all the 
	relations between them. 

	Initialize an empty ``Discourse``::

		>>> D = rdatools.Discourse()
		>>> print(D)
		Discourse(0 utterances, 0 actors)

	"""

	def __init__(self):
		# print u'\nYou created a new Discourse ;-)'
		self._graph = nx.MultiDiGraph()
		self._corpus = None
		self._new_cits = []

	def __repr__(self):
		return u'<Dicourse({} utterances, {} actors)>'.format(
			len(self.utterances()), 
			len(self.actors()), 
			)

	def __len__(self):
		return len(self.utterances())


	### generic methods
	##########################################################################

	def _make_label_unique(self, label):
		while label in self._graph:
			label += u'*'
		return label


	### node level methods
	##########################################################################

	def _nodes(self, data=True, manual_if=u'', **kwargs):
		out_type = u'(nid, attr)' if data else u'nid'
		condition = u' and '.join(
			(u'u"{0}" in attr and attr[u"{0}"] == u"""{1}"""'.format(
			k,v.replace('"',"'")) 
		for k,v in kwargs.iteritems()))	
		if manual_if:
			condition = manual_if
			if kwargs:
				print u'Key word arguments are ignored because "manual_if" '\
				'condition is specified'
		command = u"nodes = [{} for nid, attr in self._graph.nodes_iter(data="\
			"True) {}]".format(out_type, u' if {}'.format(condition) 
			if condition else u'')
		exec(command)
		return nodes

	def _node_exists(self, attr):
		result = list(self._nodes(**attr))
		return result[0][0] if result else u''


	# actor level methods

	def actors(self, **attr):
		return self._nodes(kind='actor', **attr)

	def persons(self, **attr):
		return self.actors(a_type=u'person')

	def authors(self, **attr):
		return self._nodes(manual_if=u'self.utterances_actors(edge_attr='\
			'{u"actor":nid, u"relation":u"author"})')

	def editors(self, **attr):
		return self._nodes(manual_if=u'self.utterances_actors(edge_attr='\
			'{u"actor":nid, u"relation":u"editor"})')

	def contributors(self, **attr):
		return self._nodes(manual_if=u'self.utterances_actors(edge_attr='\
			'{u"actor":nid, u"relation":u"contributor"})')

	def add_actor(self, ignore=False, **attr):
		'''
		Name = whole name (person or other)
		Firstname (only for persons)
		Lastname  (only for persons)
		Name overwrites firstname/lastname if actor is a person
		'''
		# initialize attributes:
		attr = clean_attr(attr) 
		attr[u'kind'] = u'actor'
		check_attr_format(attr) 
		# edit attributes: add/check actor specific kv pairs
		if not any(k in attr.iterkeys() for k in [u'name', u'lastname']):
			raise ValueError(u"Provide name or lastname!")
		# determine a_type
		if not u'a_type' in attr.iterkeys():
			if u'name' in attr.iterkeys():
				if len(unpack_name(attr[u'name'])) == 2:
					attr[u'a_type'] = u'person'
				else:
					attr[u'a_type'] = u'other'
			else:
				attr[u'a_type'] = u'person'
		if attr[u'a_type'] == u'person':
			if u'name' in attr.iterkeys():
				if any(k in attr.iterkeys() for k in [u'firstname', u'lastname']):
					warnings.warn(u'firstname/lastname overwritten by name')
				name_split = unpack_name(attr[u'name'])
				attr[u'lastname'] = name_split[0]
				if len(name_split)==2:
					attr[u'firstname'] = name_split[1]
				elif u'firstname' in attr.iterkeys():
					del attr[u'firstname']
			elif u'firstname' in attr.iterkeys():
				attr[u'name'] = ', '.join([attr[u'lastname'], attr[u'firstname']])
			else:
				attr[u'name'] = attr[u'lastname']
		else:
			if not u'name' in attr.iterkeys():
				raise ValueError(u"Provide name!")
			if u'firstname' in attr.iterkeys():
				warnings.warn(u'firstname ignored because actor is not a person')
				del attr[u'firstname']
			if u'lastname' in attr.iterkeys():
				warnings.warn(u'lastname ignored because actor is not a person')
				del attr[u'lastname']
		# add actor node
		node_exists = self._node_exists(attr)
		if node_exists:
			if ignore:
				return node_exists
			else:
				raise KeyError(u"Actor already exists. Did you mean update?")
		attr[u'label'] = self._make_label_unique(attr[u'name'])
		self._graph.add_node(attr[u'label'], **attr) # label also appears as attr now!
		return attr[u'label']
			

	def update_actor(self, label, merge=False, **attr):
		# initialize attributes: 
		special_case = False # Flag for special cases
		attr = clean_attr(attr)
		if not attr:
			raise ValueError(u"No attributes specified")
		attr[u'kind'] = u'actor'
		check_attr_format(attr) 
		# edit attributes: add/check actor specific kv pairs
		label = unicode(label.lower().strip())
		if label not in self._graph:
			raise ValueError(u"Actor {} doesn't exist".format(repr(label)))
		old_attr = self._graph.node[label]
		new_attr = dict(old_attr)
		new_attr.update(attr) # Note that old label is now in new_attr!
		if old_attr == new_attr:
			raise ValueError(u"No changes specified")
		# handle name stuff
		if new_attr[u'a_type'] == u'person':
			if u'name' in attr.iterkeys():
				if any(k in attr.iterkeys() for k in [u'firstname', u'lastname']):
					warnings.warn(u'firstname/lastname overwritten by new name')
				name_split = unpack_name(attr[u'name'])
				new_attr[u'lastname'] = name_split[0]
				if len(name_split)==2:
					new_attr[u'firstname'] = name_split[1]
				elif u'firstname' in new_attr.iterkeys():
					del new_attr[u'firstname']

			elif (
				all(k in attr.iterkeys() for k in [u'firstname', u'lastname']) 
				or (
					u'lastname' in attr.iterkeys() 
					and u'firstname' in new_attr.iterkeys()
					)
				or (
					u'firstname' in attr.iterkeys() 
					and u'lastname' in new_attr.iterkeys()
					)
				):
				new_attr[u'name'] = ', '.join(
					[new_attr[u'lastname'], new_attr[u'firstname']])

			elif u'lastname' in attr.iterkeys():
				new_attr[u'name'] = new_attr[u'lastname']
			elif not old_attr[u'a_type'] == u'person':
				special_case = True
				name_split = unpack_name(new_attr[u'name'])
				new_attr[u'lastname'] = name_split[0]
				if len(name_split)==2:
					new_attr[u'firstname'] = name_split[1]
		else:
			if u'firstname' in new_attr.iterkeys():
				if u'firstname' in attr.iterkeys():
					warnings.warn(
						u'firstname ignored because actor is not a person')
				# Delete key here and in existing node
				del new_attr[u'firstname']
				del self._graph.node[old_attr[u'label']][u'firstname']
			if u'lastname' in new_attr.iterkeys():
				if u'lastname' in attr.iterkeys():
					warnings.warn(
						u'lastname ignored because actor is not a person')
				# Delete key here and in existing node
				del new_attr[u'lastname']
				del self._graph.node[old_attr[u'label']][u'lastname']
		# handle node and label stuff
		if not new_attr[u'name'] == old_attr[u'name'] or special_case:
			del new_attr[u'label'] # To test (below) if node with identical attributes already exists. But don't del before, since old_attr == new_attr (above) wouldn't work
			if self._node_exists(new_attr):
				if merge:
					pass # 1) change all references of old node to (existing) target 2) delete old node
				else:
					raise KeyError(
						u"Utterance already exists. Did you mean merge?")
			new_attr[u'label'] = self._make_label_unique(new_attr[u'name'])
			# relabel the node itself
			mapping={old_attr[u'label']: new_attr[u'label']}
			nx.relabel_nodes(self._graph, mapping, copy=False)
			# relabel references to the node in edge attributes
			for i in self.utterances_actors(edge_attr={u'actor':old_attr[u'label']}):
				self._graph[i[0]][i[1]][i[2]][u'actor']=new_attr[u'label']
			# relabel references to the node in corpus
		# add utterance node
		self._graph.add_node(new_attr[u'label'], **new_attr)
		return new_attr[u'label']


	# utterance level methods

	def _get_firstauthor(self, utterance):
		candidates = self.utterances_actors(edge_attr={u'utterance':utterance})
		for c in candidates:
			if c[3][u'relation'] == u'author' and c[3][u'position'] == u'1':
				return c[1]
		return u''

	def utterances(self, **attr):
		return self._nodes(kind=u'utterance', **attr)

	def articles(self, **attr):
		return self.utterances(u_type=u'journalarticle')

	def books(self, **attr):
		return self.utterances(u_type=u'book')

	def chapters(self, **attr):
		return self.utterances(u_type=u'booksection')

	def documents(self, **attr):
		return self.utterances(u_type=u'document')

	def webpages(self, **attr):
		return self.utterances(u_type=u'webpage')


	def add_utterance(self, allow_doubles=False, ignore=False, **attr):
		# initialize attributes: clean, make unicode, delete empty kv pairs, check formatting
		attr = clean_attr(attr)
		attr[u'kind'] = u'utterance'
		check_attr_format(attr)
		# edit attributes: add/check utterance specific kv pairs		
		if not all(k in attr.iterkeys() for k in [u'title', u'date']):
			raise ValueError(u"Provide title and date!")
		# add utterance node
		if not allow_doubles:
			node_exists = self._node_exists(attr)
			if node_exists:
				if ignore:
					warnings.warn(
						u'Utterance already exists. Did you mean update?')
					return node_exists
				else:
					raise KeyError(
						u"Utterance already exists. Did you mean update?")
		attr[u'label'] = self._make_label_unique(
			make_u_label(date=attr['date'], title=attr[u'title']))
		self._graph.add_node(attr[u'label'], **attr)
		return attr[u'label']

	def update_utterance(self, label, allow_doubles=False, merge=False, **attr):
		# initialize attributes: clean, make unicode, delete empty kv pairs, check formatting
		attr = clean_attr(attr)
		if not attr:
			raise ValueError(u"No attributes specified")
		attr[u'kind'] = u'utterance'
		check_attr_format(attr)
		# edit attributes: add/check utterance specific kv pairs
		label = unicode(label.lower().strip())
		if label not in self._graph:
			raise ValueError(u"Utterance {} doesn't exist".format(repr(label)))
		old_attr = self._graph.node[label]
		new_attr = dict(old_attr)
		new_attr.update(attr) # Note that old label is now in new_attr!
		if old_attr == new_attr:
			raise ValueError(u"No changes specified")
		# handle title/date label stuff
		# Improve code!!!
		if any(k in attr.iterkeys() for k in [u'title', u'date']):
			if not u'title' in attr.iterkeys():
				new_attr[u'title'] = old_attr[u'title']
			if not u'date' in attr.iterkeys():
				new_attr[u'date'] = old_attr[u'date']
			if not (new_attr[u'title'] == old_attr[u'title'] 
				and new_attr[u'date'] == old_attr[u'date']):
				del new_attr[u'label'] # To test (below) if node with identical attributes already exists. But don't del before, since old_attr == new_attr (above) wouldn't work
				if self._node_exists(new_attr) and not allow_doubles:
					# raise KeyError(u"An utterance with identical attributes already exists. Did you mean merge?")
					if merge:
						pass # 1) change all references of old node to (existing) target 2) delete old node
					else:
						raise KeyError(
							u"Utterance already exists. Did you mean merge?")
				new_attr[u'label'] = self._make_label_unique(
					make_u_label(date=new_attr['date'], title=new_attr[u'title']))
				# relabel the node itself
				mapping={old_attr[u'label']: new_attr[u'label']}
				nx.relabel_nodes(self._graph, mapping, copy=False) 
				# relabel references to the node in edge attributes
				for i in self.utterances_actors(
					edge_attr={u'utterance':old_attr[u'label']}):
					self._graph[i[0]][i[1]][i[2]][u'utterance']=new_attr[u'label']
				for i in self.citations(edge_attr={u'citing':old_attr[u'label']}):
					self._graph[i[0]][i[1]][i[2]][u'citing']=new_attr[u'label']
				for i in self.citations(edge_attr={u'cited':old_attr[u'label']}):
					self._graph[i[0]][i[1]][i[2]][u'cited']=new_attr[u'label']
			# relabel references to the node in corpus
		# add utterance node
		self._graph.add_node(new_attr[u'label'], **new_attr)
		return new_attr[u'label']


	### edge level methods
	##########################################################################

	def _edges(self, source_attr={}, target_attr={}, edge_attr={}, 
		edge_attr_ge={}, data=True, keys=True):
		out_type = u'(s, t, key, attr)' if data and keys \
				else u'(s, t, attr)' if data and not keys \
				else u'(s, t)'
		source_attr = u' and '.join(
			(u'(u"{0}" in self._graph.node[s].iterkeys() and self._graph.node[s]'\
				'[u"{0}"] == u"""{1}""")'.format(k,v.replace('"',"'"))
				for k,v in source_attr.iteritems()))
		target_attr = u' and '.join(
			(u'(u"{0}" in self._graph.node[t].iterkeys() and self._graph.node[t]'\
				'[u"{0}"] == u"""{1}""")'.format(k,v.replace('"',"'"))  
				for k,v in target_attr.iteritems()))
		edge_attr = u' and '.join(
			(u'(u"{0}" in attr.iterkeys() and attr[u"{0}"] == u"""{1}""")'.format(
				k,v.replace('"',"'"))
				for k,v in edge_attr.iteritems()))
		edge_attr_ge = u' and '.join(
			(u'(u"{0}" in attr.iterkeys() and attr[u"{0}"] >= {1})'.format(
				k,v.replace('"',"'"))
				for k,v in edge_attr_ge.iteritems()))
		# print source_attr
		command = u'''edges = [
				{}
				for s, tdict in self._graph.adjacency_iter()
				{}
				for t, keydict in tdict.iteritems()
				{}
				for key,attr in keydict.iteritems()
				{}{}			
			]'''.format(
				out_type,
				u'if {}'.format(source_attr) if source_attr else u'',
				u'if {}'.format(target_attr) if target_attr else u'',
				u'if {}'.format(edge_attr) if edge_attr else u'',
				u'if {}'.format(edge_attr_ge) if edge_attr_ge else u'',
				)
		# print command
		exec(command)
		return edges

	def _edges_via(self, source_attr={}, connector_attr={}, target_attr={}, 
		edge1_attr={}, edge2_attr={}, connector=True):
		out_type = u'(s1, t2, {u"connector":t1})' if connector else u'(s1, t2)'
		source_attr = u' and '.join(
			(u'(u"{0}" in self._graph.node[s1].iterkeys() and self._graph.node[s1]'\
				'[u"{0}"] == u"{1}")'.format(k,v) 
				for k,v in source_attr.iteritems()))
		connector_attr = u' and '.join(
			(u'(u"{0}" in self._graph.node[t1].iterkeys() and self._graph.node[t1]'\
				'[u"{0}"] == u"{1}")'.format(k,v) 
				for k,v in connector_attr.iteritems()))
		target_attr = u' and '.join(
			(u'(u"{0}" in self._graph.node[t2].iterkeys() and self._graph.node[t2]'\
				'[u"{0}"] == u"{1}")'.format(k,v) 
				for k,v in target_attr.iteritems()))
		edge1_attr = u' and '.join(
			(u'(u"{0}" in attr1.iterkeys() and attr1[u"{0}"] == u"{1}")'.format(k,v) 
				for k,v in edge1_attr.iteritems()))
		edge2_attr = u' and '.join(
			(u'(u"{0}" in attr2.iterkeys() and attr2[u"{0}"] == u"{1}")'.format(k,v) 
				for k,v in edge2_attr.iteritems()))
		# print source_attr
		command = u'''edges = [
				{}
				for s1, tdict1 in self._graph.adjacency_iter()
				{}
				for t1, keydict1 in tdict1.iteritems()
				{}
				for key1,attr1 in keydict1.iteritems()
				{}
				for t2, keydict2 in self._graph.adj[t1].iteritems()
				{}
				for key2,attr2 in keydict2.iteritems()
				{}
			]'''.format(
				out_type,
				u'if {}'.format(source_attr) if source_attr else u'',
				u'if {}'.format(connector_attr) if connector_attr else u'',
				u'if {}'.format(edge1_attr) if edge1_attr else u'',
				u'if {}'.format(target_attr) if target_attr else u'',
				u'if {}'.format(edge2_attr) if edge2_attr else u'',
				)
		# print command
		exec(command)
		return edges

	def _edge_is_unique(self, attr):
		if attr[u'kind'] == u'utterance_actor':
			source_attr = {u'kind':u'utterance'}
			target_attr = {u'kind':u'actor'}
		elif attr[u'kind'] == u'citation':
			source_attr = {u'kind':u'utterance'}
			target_attr = {u'kind':u'utterance'}
		result = list(self._edges(
			source_attr=source_attr, target_attr=target_attr, edge_attr=attr))
		return False if result else True


	# utterances_utterances level methods
	def citations(self, source_attr={}, target_attr={}, edge_attr={}, 
		data=True, keys=True):
		source_attr[u'kind'] = u'utterance'
		target_attr[u'kind'] = u'utterance'
		edge_attr[u'relation'] = u'citation'
		return self._edges(source_attr=source_attr, target_attr=target_attr, 
			edge_attr=edge_attr, data=data, keys=keys)

	def add_citation(self, citing, cited, **attr):
		attr[u'citing'] = citing
		attr[u'cited'] = cited
		attr[u'relation'] = u'citation'
		attr = clean_attr(attr)
		attr[u'kind'] = u'citation'
		if attr[u'citing'] not in self._graph:
			raise ValueError(u"Citing utterance {} doesn't exist".format(
				repr(attr[u'citing'])))
		if attr[u'cited'] not in self._graph:
			raise ValueError(u"Cited utterance {} doesn't exist".format(
				repr(attr[u'cited'])))
		if not self._edge_is_unique(attr):
			warnings.warn(u'Citation edge already exists.')
			return
		self._graph.add_edge(attr[u'citing'], attr[u'cited'], **attr)

	# utterances_actors level methods

	def utterances_actors(self, source_attr={}, target_attr={}, 
		edge_attr={}, data=True, keys=True):
		source_attr[u'kind'] = u'utterance'
		target_attr[u'kind'] = u'actor'
		return self._edges(source_attr=source_attr, target_attr=target_attr, 
			edge_attr=edge_attr, data=data, keys=keys)

	def add_utterance_actor(self, utterance, actor, relation, ignore=False, **attr):
		attr[u'utterance'] = utterance
		attr[u'actor'] = actor
		attr[u'relation'] = relation
		attr = clean_attr(attr)
		attr[u'kind'] = u'utterance_actor'
		if attr[u'utterance'] not in self._graph:
			raise ValueError(u"Utterance {} doesn't exist".format(
				repr(attr[u'utterance'])))
		if attr[u'actor'] not in self._graph:
			raise ValueError(u"Actor {} doesn't exist".format(
				repr(attr[u'actor'])))
		if not self._edge_is_unique(attr):
			if ignore:
				warnings.warn(u'Utterance-actor edge already exists.')
				return
			else:
				raise KeyError(
					u"Utterance-actor edge already exists. Did you mean update?")
		self._graph.add_edge(attr[u'utterance'], attr[u'actor'], **attr)


	def times_cited(self, citations, min=1, data=True):
		''' returns list of utterances with freq and connectors as attributes
			requires u-u edge list as input, as returned by citations()
		'''
		citations = list(set(c[:2] for c in citations))
		cit_dict = {}
		for c in citations:
			if c[1] in cit_dict.iterkeys():
				cit_dict[c[1]][u'freq'] += 1
				cit_dict[c[1]][u'connectors'][len(cit_dict[c[1]][u'connectors'])] = c[0]
			else:
				cit_dict[c[1]] = {u'connectors':{0:c[0]}, u'freq':1}
		times_cited = sorted(
			[c for c in cit_dict.iteritems() if c[1][u'freq'] >= min],
			key=lambda c: c[1][u'freq'], reverse=True
			)
		return times_cited if data else [c[0] for c in times_cited]
		

	def co_x2(self, focus=u'target', source_attr={}, target_attr={}, 
		edge_attr={}, edge_attr_ge={}):
		''' for all direct edges in graph (reachable through _edge method)
		'''
		two_mode = self._edges(
			source_attr=source_attr, 
			target_attr=target_attr,
			edge_attr=edge_attr,
			edge_attr_ge=edge_attr_ge,
			data=False, 
			keys=False
			)
		return adjacency(two_mode, focus)

	# def co_x3(self, focus=u'target', source_attr={}, connector_attr={}, target_attr={}, edge1_attr={}, edge2_attr={}):
	# 	''' for indirect edges in graph (reachable through _edge_via method)
	# 	'''
	# 	two_mode = self._edges_via(
	# 		source_attr=source_attr,
	# 		connector_attr=connector_attr, 
	# 		target_attr=target_attr,
	# 		edge1_attr=edge1_attr,
	# 		edge2_attr=edge2_attr, 
	# 		connector=False,
	# 		)
	# 	return adjacency(two_mode, focus)


	def co_authors(self, source_attr={}, target_attr={}, edge_attr={}):
		source_attr[u'kind'] = u'utterance'
		target_attr[u'kind'] = u'actor'
		edge_attr[u'relation'] = u'author'
		return self.co_x2(
			focus=u'target', 
			source_attr=source_attr, 
			target_attr=target_attr, 
			edge_attr=edge_attr)

	def co_editors(self, source_attr={}, target_attr={}, edge_attr={}):
		source_attr[u'kind'] = u'utterance'
		target_attr[u'kind'] = u'actor'
		edge_attr[u'relation'] = u'editor'
		return self.co_x2(
			focus=u'target', 
			source_attr=source_attr, 
			target_attr=target_attr, 
			edge_attr=edge_attr)


	def co_citations(self, source_attr={}, target_attr={}, edge_attr={}):
		source_attr[u'kind'] = u'utterance'
		target_attr[u'kind'] = u'utterance'
		edge_attr[u'relation'] = u'citation'
		return self.co_x2(
			focus=u'target', 
			source_attr=source_attr, 
			target_attr=target_attr, 
			edge_attr=edge_attr)

	def bibliographic_coupling(self, source_attr={}, target_attr={}, edge_attr={}):
		source_attr[u'kind'] = u'utterance'
		target_attr[u'kind'] = u'utterance'
		edge_attr[u'relation'] = u'citation'
		return self.co_x2(
			focus=u'source', 
			source_attr=source_attr, 
			target_attr=target_attr, 
			edge_attr=edge_attr)


	### Zotero related methods
	##########################################################################

	def load_zotero_basic(self, ZC, zotero_refresh=False):
		print u'\nFetching basic data from Zotero collection: "{}"'. \
			format(ZC.collectionID)
		count_actors = set()
		count_utterances = set()
		if zotero_refresh:
			ZC.refresh()
		for item in ZC.utterances:
			# use all zotero fields as u_attr in special zot_* namespace except date, title and type (global namespace). Don't use creators, since they alreay go to actors
			u_attr = {u''.join([u'zot_',k]):v 
				for k,v in item.iteritems() 
				if v and not k in [u'date',u'title',u'itemType', u'creators']}
			u_attr[u'date'] = item[u'date'] or u'0000'
			u_attr[u'title'] = item[u'title']
			u_attr[u'u_type'] = item[u'itemType']
			u_attr[u'ignore'] = True
			u_label = self.add_utterance(**u_attr)
			count_utterances.add(u_label)
			### fetch actors (creators)
			counter = 1
			for creator in item[u'creators']:
				# dealing with position for creatorType (author/editor/)
				this_creatorType = creator[u'creatorType']
				if counter == 1: # matches only in the first iteration. Used to initialize au_position assignment 
					last_creatorType = this_creatorType
				if not last_creatorType == this_creatorType: # matches for each creator type (e.g. 'author' and 'editor')
					counter = 1
				a_label = self.add_actor(
					lastname=creator[u'lastName'], 
					firstname=creator[u'firstName'],
					ignore=True,
					)
				count_actors.add(a_label)
				self.add_utterance_actor(
					u_label, 
					a_label,
					relation=creator[u'creatorType'], 
					position=unicode(counter),
					ignore = True,
					)
				counter += 1
				last_creatorType = this_creatorType
		print u'\t...{} utterances added'.format(len(count_utterances))
		print u'\t...{} actors added'.format(len(count_actors))


	def load_zotero_citations(self, ZC, zotero_refresh=False,
		fuzzy_t=True, fuzzy_y=True, fuzzy_ty=True, 
		nlev=0.1, title_sim=0.9, date_span=(4,4)):
		""" loads citations from notes flagged as 'RDA citations' in Zotero collection
		"""
		if not ZC.cit_notes:
			raise ValueError(u'No cit_notes found. Check your Zotero tags and '\
				u'consider refreshing your ZoteroCollection object')
		print u'\nFetching citations from Zotero collection: "{}"'.\
			format(ZC.collectionID)
		if zotero_refresh:
			print u'\t...refresh Zotero'
			ZC.refresh()
		### helper functions
		def _parse_authors(authors, a_grammar): # here or outside method/class?
			outlist = []
			parsed_authors = re.sub(r'\b[Ee][Tt] [Aa][Ll]\.* *,*;*', r'', authors)
			if ';' in a_grammar:
				parsed_authors = re.sub(
					r'[, ]+and |[, ]+And |[, ]+AND |[, ]*&', r'; ', parsed_authors)
				parsed_authors = re.sub(
					r';[ \t]*;',r'; ',parsed_authors) # kill double commas
				parsed_authors = parsed_authors.rstrip(u';')
			else:
				parsed_authors = re.sub(
					r'[, ]+and |[, ]+And |[, ]+AND |[, ]*&', r', ', parsed_authors)
				parsed_authors = re.sub(
					r',[ \t]*,', r', ', parsed_authors) # kill double commas
				parsed_authors = parsed_authors.rstrip(',')		
			if a_grammar  ==u'ln,fn;':
				for a in parsed_authors.split(u';'):
					lastname = a.split(u',')[0].strip()
					firstname = a.split(u',')[1].strip()
					outlist.append((lastname, firstname))
			elif a_grammar==u'ln,fn,':
				parsed_authors=parsed_authors.split(',')
				if not len(parsed_authors) & 1:
					parsed_authors = [','.join(parsed_authors[i:i+2]) 
						for i in range(0, len(parsed_authors), 2)]
					for a in parsed_authors:
						lastname = a.split(u',')[0].strip()
						firstname = a.split(u',')[1].strip()
						outlist.append((lastname, firstname))
				elif len(parsed_authors) == 1:
					lastname = parsed_authors[0].strip()
					firstname = u''
					outlist.append((lastname, firstname))
				else:
					outlist.append((u'xxx', u'xxx')) # Does this eveer happen? Construct test case!
			elif a_grammar == u'fn ln,':
				for a in parsed_authors.split(u','):
					a_split = a.strip().rsplit(u' ',1)
					if len(a_split) > 1:
						lastname =  a_split[1]
						firstname = a_split[0]
						outlist.append((lastname, firstname))
					else:
						lastname = a_split[0]
						firstname = u''
						outlist.append((lastname, firstname))
			elif a_grammar == u'fn ln;':
				for a in parsed_authors.split(u';'):
					a_split = a.strip().rsplit(u' ',1)
					if len(a_split) > 1:
						lastname = a_split[1]
						firstname = a_split[0]
						outlist.append((lastname, firstname))
					else:
						lastname = a_split[0]
						firstname = u''
						outlist.append((lastname, firstname))
			return outlist

		### process cit_notes
		for item in ZC.cit_notes:
			parent_zot_key = item[u'parentItem']
			utterance = list(self.utterances(zot_key=parent_zot_key)) # list with format: {label: {attr}}
			
			if len(utterance) == 1: 
				utterance = utterance[0][1] # utterance now a dict!
			else: # if no parent item found...
				print utterance
				raise ValueError(u'No singular match for zot_key: "{}"'.format(
					parent_zot_key))
			print u'\tProcessing citation list of "{}"'.format(
				utterance[u'label'])

			# set default grammars
			c_grammar = DEFAULT_C_GRAMMAR
			a_grammar = DEFAULT_A_GRAMMAR
			print  u'\t...default citation grammar: "{}"'.\
				format(C_GRAMMARS[c_grammar])
			print  u'\t...default author grammar: "{}"'.\
				format(A_GRAMMARS[a_grammar])

			# clean citationlist
			cit_note = unicodedata.normalize("NFKC", item['note']) # nennt z.B. "&"" Zeichen um...(in "&amp;"" oder so)
	 		cit_note = RE_P_TAGS.sub('', cit_note) # kill stuff (html tags and repeated blanks)
	 		cit_note = RE_AMP.sub('&', cit_note) # make real "&" symbols
	 		cit_note = RE_CIT_LINEBREAKS.sub('\n', cit_note) # make stuff to linebreaks
	 		cit_note = RE_CLEAN_DOUBLELINEBREAK.sub('\n\n', cit_note)  # Kill arbitrary \n and blanks between item blocks
	 		cit_note = RE_EMPTY_END_OF_STRING.sub('', cit_note) # Kill arbitrary \n and blanks at the end of the note
	 		cit_note = RE_EMPTY_END_OF_LINE.sub('\n', cit_note) # Kill arbitrary blanks and tabs before a linebreak
			cit_note = cit_note.split('\n\n') # split into blocks

			# Process cit_note block by block
			for block in cit_note:
				block = block.strip()
				if u'\n' in block:
					# print '\n',block,'\n'
					parserinfo = u' | '.join([c_grammar, a_grammar])
					cit = block.split('\n')

					# split citation candidates from control prompts (such as C_GRAMMAR changes)
					if len(cit) in range(3,5):

						# dissect and match citation
						cit_date = unicode(cit[c_grammar.lower().split(r'/').\
							index(u'y')]).strip(u' |(|)|.|,')
						cit_year = get_year(cit_date)
						cit_authors = _parse_authors(
							cit[c_grammar.lower().split(r'/').index(u'a')],
								a_grammar)
						cit_firstauthor = cit_authors[0][0].lower() # what if no authors?
						cit_title = unicode(cit[c_grammar.lower().split(r'/').
							index(u't')]).strip().lower()						
						match_2 = []
						match_3 = []
						match_4 = []
						direct_match = False
						for nid, attr in self._graph.nodes_iter(data=True):
							if attr[u'kind'] == u'utterance':
								if str_length_similarity(
									attr[u'title'], cit_title) >= title_sim:
									if int(cit_year) + date_span[1] \
										>= int(get_year(attr[u'date'])) \
										>= int(cit_year) - date_span[0]:
										if self._get_firstauthor(
											attr[u'label']).split(
											u',')[0].strip(
											u'*') == cit_firstauthor.split(
											u',')[0].strip(u'*'):
											if get_year(attr[u'date']) == cit_year:
												# 1) same firstauthor, same year, same title
												if attr[u'title'] == cit_title:
													print u'\t...match 1, same firstauthor, '\
													'same year, same title as "{}"'.\
														format(attr[u'label'])
													self.add_citation(
														utterance[u'label'], 
														attr[u'label'], 
														match_type=u'1', 
														citation=block)
													direct_match = True
													break
												# 2) fuzzy title, same firstauthor, same year
												elif distance.nlevenshtein(
													cit_title, attr[u'title'], 
													method=2) <= nlev:
													match_2.append(attr)
											else: 
												# 3) fuzzy year, same firstauthor, same title
												if attr[u'title'] == cit_title:
													match_3.append(attr)
												# 4) fuzzy year, fuzzy date, same firstauthor
												elif distance.nlevenshtein(
													cit_title, attr[u'title'], 
													method=2) <= nlev:
													match_4.append(attr)
						if not direct_match:
							if match_2:
								if len(match_2) == 1:
									print u'\t...match 2, fuzzy title, '\
										'same firstauthor, same year as "{}"'.\
										format(match_2[0][u'label'])
									self.add_citation(
										utterance[u'label'], 
										match_2[0][u'label'], 
										match_type=u'2', 
										citation=block)
								else:
									raise ValueError(
										u'More than one match for fuzzy title, '\
										'firstauthor, year')
							elif match_3:
								if len(match_3) == 1:
									print u'\t...match 3, fuzzy year, '\
									'same firstauthor, same title as "{}"'.\
										format(match_3[0][u'label'])
									self.add_citation(
										utterance[u'label'], 
									match_3[0][u'label'], 
									match_type=u'3', 
									citation=block)
								else:
									raise ValueError(
										u'More than one match for fuzzy year, '\
										'same firstauthor, same title')
							elif match_4:
								if len(match_4) == 1:
									print u'\t...match 4, fuzzy year, fuzzy date, '\
									'same firstauthor as "{}"'.\
										format(match_4[0][u'label'])
									self.add_citation(
										utterance[u'label'], 
									match_4[0][u'label'], 
									match_type=u'4', 
									citation=block)
								else:
									raise ValueError(
										u'More than one match for fuzzy year, '\
										'fuzzy date, same firstauthor')
							else:
								### add to _new_cits
								creators = [{u'lastName': author[0],
										u'firstName': author[1],
										u'creatorType': u'author'} 
										for author in cit_authors]
								new_cit = ZC.conn.item_template(u'document')
								new_cit[u'title'] = cit_title
								new_cit[u'date'] = cit_date
								new_cit[u'creators'] = creators
								new_cit[u'collections'] = [ZC.collectionID]
								new_cit[u'tags'].append(
									{u'tag': u'RDA new citation'})
								if not new_cit in self._new_cits:
									self._new_cits.append(new_cit)
									print u'\t...no match: "{}" '\
									'--> saved as potential Zotero upload'.\
										format(c_label)	
								else:
									print u'\t...no match: "{}" '\
									'--> was already saved as potential Zotero upload'.\
										format(c_label)
					else:
						print u'\t...citations must have 3-4 lines -> ignoring: "{}"'.\
							format(cit)

				elif u'A_GRAMMAR' in block:
					a_grammar_match = re.match(
						r'^A_GRAMMAR=(?P<new_a_grammar>.*)$', block)
					if a_grammar_match:
						new_a_grammar = re.sub(r', *', r',', a_grammar_match.\
							group('new_a_grammar'))
						if new_a_grammar in A_GRAMMARS.iterkeys():
							print u'\t...author grammar changed to: "{}"'.\
								format(A_GRAMMARS[new_a_grammar])
							a_grammar = new_a_grammar
						else:
							print u'\t..."{}" is not an allowed author grammar'.\
								format(new_a_grammar)
				elif u'C_GRAMMAR' in block:
					c_grammar_match = re.match(
						r'^C_GRAMMAR=(?P<new_c_grammar>.*)$', block)
					if c_grammar_match:
						new_c_grammar = re.sub(r'/ *',r'/', c_grammar_match.\
							group(u'new_c_grammar'))
						if new_c_grammar in C_GRAMMARS.iterkeys():
							c_grammar = new_c_grammar
							print u'\t...citation grammar changed to: "{}"'.\
								format(C_GRAMMARS[new_c_grammar])
						else:
							print u'\t..."{}" is not an allowed citation grammar'.\
								format(new_c_grammar)
				else:
					print u'\t...cannot interpret this line: "{}"'.format(block)
	

	def load_zotero_cleantexts(self, ZC, zotero_refresh=False, 
		read_method=u'textacy', **kwargs):
		print u'\nLoading Zotero cleantexts into corpus'
		kwargs = dict(kwargs)
		if not isinstance(self._corpus, Corpus):
			print u'\t...making new corpus'
			self._corpus = Corpus()
		if zotero_refresh == True:
			ZC.refresh(from_within=True)
		if ZC.cleantexts:
			texts = []
			metadatas = []
			for item in ZC.cleantexts:
				print u'\t...loading "{}"'.format(item[u'path'])
				text = read_text(item['path'], read_method=read_method)
				text = clean_text(text, **kwargs)
				texts.append(text)
				# parent_attr = [u for u in self.utterances(zot_key=item[u'parentItem'])][0][1]
				# keys = [k for k in parent_attr.iterkeys()]
				# values = [v for v in parent_attr.itervalues()]
				# metadata = dict(zip(keys, values))
				parent_label = [u for u in self.utterances(
					zot_key=item[u'parentItem'])][0][1][u'label']
				self._graph[parent_label][u'cleantext_path'] = item[u'path'] # Add cleantext path to utterance attr
				metadata = {u'label':parent_label}
				metadata.update({u'from_format': item[u'path'].rsplit('.')[1],
								 u'from_path': item[u'path']})
				metadatas.append(metadata)
			self._corpus.add_texts(texts=texts, metadatas=metadatas)
		else:
			print u'\t...no cleantexts to load'

	### Text analytical methods
	##########################################################################

	def edit_cleantext(self, label):
		file = self._graph[label][u'cleantext_path']
		subprocess.call(['sublime',file])


	def make_corpus(self, reset=False):
		print u'\nMaking new corpus'
		if not isinstance(self._corpus, Corpus) or reset:
			self._corpus = Corpus()
			print u'\t...done' if not reset \
				else u'\t...corpus reset. All existing data deleted.'
		else:
			print u'\t...corpus already exists, use "reset" to replace'

	def co_words(self, min_freq=3, width=4, 
		directed=False, lemma=True, per_doc=True, connectors=False,
		filter_stops=True, filter_punct=True, filter_nums=True,
		include_pos=None, exclude_pos=None):
		''' Option for connector = author?
		'''
		print u'\nExtracting co-words'
		if not isinstance(self._corpus, Corpus):
			print u'\t...no corpus. Make one first.'
			return
		if self._corpus.__len__() < 1:
			print u'\t...corpus is empty.'
			return
		kwargs = {
			u'filter_stops':filter_stops,
			u'filter_punct':filter_punct,
			u'filter_nums':filter_nums,
			u'include_pos':include_pos,
			u'exclude_pos':exclude_pos, # Note that min_freq is used here not within textacy.extract.words() but for co-words! 
		}
		G = nx.DiGraph() if directed else nx.Graph()
		label_tokens_pairs = ((
			doc.metadata[u'label'], textacy.extract.words(doc, **kwargs)) 
			for doc in self._corpus)
		for ltp in label_tokens_pairs:
			for win in sliding_window(ltp[1], width):
				win = [t.lemma_ for t in win] \
					if lemma else [t.lower_ for t in win]
				for i in range(1,width):
					if not G.has_edge(win[0], win[i]):
						G.add_edge(win[0], win[i], 
							freq = float(1) / float(i), 
							connectors = {ltp[0]:1})
				
					elif per_doc :
						if not ltp[0] in G.edge[win[0]][win[i]]\
							[u'connectors'].iterkeys():
							G.edge[win[0]][win[i]][u'freq'] += float(1) / float(i)
							G.edge[win[0]][win[i]][u'connectors'][ltp[0]] = 1
					elif not per_doc:
						G.edge[win[0]][win[i]][u'freq'] += float(1) / float(i)
						if not ltp[0] in G.edge[win[0]][win[i]][u'connectors'].iterkeys():
							G.edge[win[0]][win[i]][u'connectors'][ltp[0]] = 1
						else:
							G.edge[win[0]][win[i]][u'connectors'][ltp[0]] += float(1) / float(i)
		return (e if connectors else e[:2]+({u'freq':e[2][u'freq']},) 
			for e in G.edges(data=True) if e[2][u'freq']>=min_freq)

	def topics(self, selection=None, method=u'nmf', n_topics=20, 
		weighting=u'tfidf', normalize=True, smooth_idf=True, 
		min_df=1, max_df=1.0, max_n_terms=100000):
		# http://textacy.readthedocs.io/en/latest/_modules/textacy/tm/topic_model.html
		# https://textacy.readthedocs.io/en/latest/api_reference.html#textacy.vsm.Vectorizer
		print u'\nExtracting topics'
		if not isinstance(self._corpus, Corpus):
			print u'\t...no corpus. Make one first.'
			return
		if self._corpus.__len__() < 1:
			print u'\t...corpus is empty.'
			return
		terms_list = (doc.to_terms_list(ngrams=1, named_entities=True, as_strings=True) 
			for doc in self._corpus) # add if conditions!
		# understanding min_df/max_df -> https://stackoverflow.com/questions/27697766/understanding-min-df-and-max-df-in-scikit-countvectorizer
		vectorizer = textacy.vsm.Vectorizer(weighting=weighting, normalize=normalize, 
			smooth_idf=smooth_idf, min_df=min_df, max_df=max_df, max_n_terms=max_n_terms)
		return TopicModel(terms_list, vectorizer, method=method, n_topics=n_topics)

	def words_in_context(self, words, ignore_case=True, window_width=50, print_only=True):
		# https://radimrehurek.com/gensim/models/word2vec.html
		# http://textminingonline.com/getting-started-with-word2vec-and-glove-in-python
		# https://rare-technologies.com/word2vec-tutorial/
		print u'\nWord(s) in context for: "{}"'.format(words)
		result = ((doc.metadata[u'label'], textacy.text_utils.keyword_in_context(doc.text, words, 
			ignore_case=ignore_case, window_width=window_width, print_only=False)) 
			for doc in self._corpus)
		if print_only:
			for label_context in result:
				print u'\n{0}\n{1}\n{0}'.format(79*u'#',label_context[0])
				for line in label_context[1]:
					print line

	# def word2vec(self, size=100, window=5, min_count=5, workers=4):
	# 	print u'\nTraining word2vec model'
	# 	# input must be list of sents, whereby sents must be list of words!
	# 	sents = [list(doc.sents) for doc in self._corpus]
	# 	for s in sents[:3]:
	# 		print s
	# 	model = gensim.models.Word2Vec(sents, size=size, window=window, min_count=min_count, workers=workers)
	# 	# model = gensim.models.Word2Vec(iter=1)  # an empty model, no training yet
	# 	# model.build_vocab(sents)  # can be a non-repeatable, 1-pass generator
	# 	# model.train(sents)  # can be a non-repeatable, 1-pass generator
	# 	return model

	