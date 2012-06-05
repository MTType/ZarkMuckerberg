#########
### Just store stuff in memory - not pretty but it'll be fine for this use
#########

from uuid import uuid4
from copy import copy

class MemoryStorage(object):
	def __init__(self):
		self.docs = {}
		self.types = {}

	def save(self, doc):
		if not 'id' in doc:
			doc['id'] = uuid4().hex
		self.docs[doc['id']] = doc

		if 'type' in doc:
			if doc['type'] not in self.types:
				self.types[doc['type']] = {}

			self.types[doc['type']][doc['id']] = doc
		return doc['id']

	def get_by_type(self, doc_type):
		if doc_type not in self.types:
			return []
		return [copy(doc) for doc in self.types[doc_type].values()]

	def get(self, key):
		if self.exists(key):
			return copy(self.docs[key])
		return None

	def exists(self, key):
		if key in self.docs:
			return True
		return False

	def get_by_keys(self, keys):
		return [self.get(key) for key in keys if self.exists(key)]

	def empty(self):
		self.docs = {}
		self.types = {}


memory_storage = MemoryStorage()

def get_db():
	return memory_storage