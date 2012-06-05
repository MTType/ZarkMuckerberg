############
### Abstract away storage so that we can use in-memory for testing and Couch when running for real
############

# TODO: Add couchdb
from memory_storage import *

# decorator to add the DB to arguments
def use_db(f):
	def inner_func(*args, **kwargs):
		return f(get_db(), *args, **kwargs)
	return inner_func