# -*- coding: utf-8 -*-
"""
zotero.py

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


import os
from pyzotero import zotero
from rdatools.functions import *


class ZoteroCollection(object):
	def __init__(self, library_id, library_type, api_key, collectionID):
		### connection
		self.conn = zotero.Zotero(library_id, library_type, api_key)
		### attributes
		self.library_id = library_id
		self.library_type = library_type
		self.api_key = api_key
		self.collectionID = collectionID
		self.collection = None
		self.utterances = None
		self.cit_notes = None
		self.attachments = None
		self.refresh()

	def refresh(self, from_within=False):
		print u'\n(Re-)Connecting to Zotero collection "{}" of library "{}"'.\
			format(self.library_id, self.collectionID) \
			if not from_within \
			else u'\t...(re-)connecting to Zotero collection "{}" of library "{}"'.\
			format(self.library_id, self.collectionID)
		item_types = self.conn.item_types()
		item_type_map = {'attachment': len(item_types) + 101} # 'attachment' is missing in zot.item_types(), so I define it here.
		for i,t in enumerate(item_types):
			if t[u'itemType'] == u'note' \
			or t[u'itemType'] == u'bookSection' \
			or t[u'itemType'] == u'attachment': # 'attachment' added in case zot.item_types() changes at some point to include it
				item_type_map[t[u'itemType']] = i + 100
			else:
				item_type_map[t[u'itemType']] = i
		self.collection=sorted([item[u'data'] \
			for item in self.conn.everything(
				self.conn.collection_items(self.collectionID))], 
				key=lambda k: item_type_map[k[u'itemType']])
		self.utterances= [item for item in self.collection \
			if not item[u'itemType'] == u'attachment' \
			and not item[u'itemType'] == u'note']
		self.cit_notes= [item for item in self.collection 
			if item[u'itemType'] == u'note' \
			and u'parentItem' in item.iterkeys() \
			and u'RDA citations' in [t.values()[0] for t in item[u'tags']]]
		self.rawtexts= [item for item in self.collection \
			if item['itemType'] == u'attachment' 
			and u'parentItem' and u'path' in item.iterkeys() 
			and u'RDA rawtext' in [t.values()[0] for t in item[u'tags']]]
		self.cleantexts= [item for item in self.collection \
			if item[u'itemType'] == u'attachment' 
			and u'parentItem' and u'path' in item.iterkeys() 
			and u'RDA cleantext' in [t.values()[0] for t in item[u'tags']]]
		return {u'utterances': self.utterances,
				u'cit_notes': self.cit_notes,
				u'attachments': self.attachments}

	def upload_new_citations(self,D):
		print u'\nUploading new citations to Zotero. Please wait...'
		if not D._new_cits:
			print u'\t...no new citations to upload.'
			return
		def upload(chunk):
			""" uploads umatched citations as new documents to Zotero collection
			"""
			upload = self.conn.create_items(chunk)
			if upload[u'failed']:
				print u'\t...an error occurerd while uploading new citations to Zotero!'
		map(upload,[D._new_cits[i:i+50] for i in xrange(0, len(D._new_cits), 50)])
		print u'\t...{} citations successfully uploaded.'.format(len(D._new_cits))
		D._new_cits = []


	def prepare_cleantext(self, path=u'', replace=False, read_method=u'textacy',
							fix_unicode=True, transliterate=True, **kwargs):
 		""" Reads any textfile tagged in Zotero as 'RDA rawtext' and reates 
 		clean txt.file (to be further hand cleaned), 
 		"""
		kwargs = dict(kwargs)
		kwargs[u'transliterate'] = transliterate
		kwargs[u'fix_unicode'] = fix_unicode
 		print u'\nPreparing Zotero cleantext attachments. '\
 			u'Existing files will {}be replaced.\n'\
 			u'\t...settings for text cleaning: {}'.\
 			format('' if replace else 'not ', kwargs)
 		if not os.path.isdir(path):
			if path:
				print u'\t...not a valid path: "{}"'\
					u'-> attachments will be saved here: "{}"'.\
					format(path, os.getcwd())
			path = os.getcwd()
 		if replace == True:
			new_attachments = [{
				u'short': u'RDA_{}.txt'.format(
 					[make_u_label(u[u'date'], u[u'title'])
						for u in self.utterances 
						if u[u'key'] == r[u'parentItem']][0]),
				u'rawpath': r[u'path'],
				u'existing_clean': [c[u'key'] for c in self.cleantexts \
					if c[u'parentItem'] == r[u'parentItem']],
				u'parent': r[u'parentItem'],
				u'tags': [{u'tag':u'RDA cleantext'}]} 
				for r in self.rawtexts
				]
		elif replace == False:
 			new_attachments = [{
 				u'short':u'RDA_{}.txt'.format(
 					[make_u_label(u[u'date'], u[u'title'])
						for u in self.utterances 
						if u['key'] == r['parentItem']][0]),
				u'rawpath': r[u'path'],
				u'existing_clean': '',
				u'parent': r[u'parentItem'],
				u'tags': [{u'tag': u'RDA cleantext'}]} 
				for r in self.rawtexts 
				if not r[u'parentItem'] in [c[u'parentItem'] 
					for c in self.cleantexts]]
		else:
			raise ValueError(u'keyword argument "replace" must be True or False!')
		if new_attachments:
			print u'\t...{} file{} found. Please wait...'.\
				format(len(new_attachments),'s' if len(new_attachments) > 1 else '')
 			for a in new_attachments:
				cleantext = read_text(a[u'rawpath'], read_method=read_method)
				cleantext = clean_text(cleantext, **kwargs)

				### create txt file
				file_path = unicode(os.path.join(path, a[u'short']))
				exists = os.path.exists(file_path)
				print u'\t...creating file: "{}"'.format(file_path)
				with open(file_path, 'w') as f:
					f.write(cleantext)
				
				### create or update Zotero attachment
				upload = self.conn._attachment_template('linked_file') # see https://github.com/urschrei/pyzotero/blob/master/pyzotero/zotero.py
				upload[u'title'] = a[u'short']
				upload[u'path'] = file_path
				upload[u'tags'] = [{u'tag':u'RDA cleantext'}]
				upload[u'contentType'] = u'text/html'
				if not a[u'existing_clean']:
					print u'\t...creating Zotero attachment: "{}"'.format(file_path)
					self.conn.create_items([upload],a['parent'])
				else:
					
					print u'\t...updating path in existing Zotero '\
						'attachment: "{}"'.format(file_path)
					existing = self.conn.item(a['existing_clean'][0])
					existing[u'data'][u'title'] = upload[u'title']
					existing[u'data'][u'path'] = upload[u'path']
					existing[u'data'][u'contentType'] = upload[u'contentType']
					self.conn.update_item(existing)
		else:
				print u'\t...no files to prepare.'
