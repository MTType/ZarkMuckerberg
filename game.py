import json
from httplib2 import Http

GENERATORS = {
	"suggestion_box": "idea",
	"coder": "feature",
	"kettle": "coffee",
	"designer": "website",
	"angel_investor": "cash"
}

# RULE SETTINGS
GENERATOR_COST = {
	"cash": 1,
	"idea": 1,
	"website": 1,
	"coffee": 1
}

GENERATOR_IMPROVEMENT_COST = {
	"feature": 3,
	"coffee": 2
}

PR_COST = {
	"cash": 1,
	"idea": 1
}

RESOURCES = GENERATORS.values()

MAX_RESOURCE_GENERATORS = 5
MAX_IMPROVED_RESOURCE_GENERATORS = 4

class Game(object):
	def __init__(self, game, player):
		self.game = game
		self.secret = player['secret']
		self.resources = player['resources']
		self.generators = player['generators']
		self.improved_generators = player['improved_generators']
		self.pr = player['pr']
		self.customers = player['customers']
		self.actions = player['actions']
		self.turn = False

        def get_customers(self):
            return self.customers

	def request(self, resource, body=None, method='POST', allow_error = False):
		http = Http()

		if not body:
			body = {}

		body['player_id'] = self.game['id']
		body['secret'] = self.secret
		body = json.dumps(body)

		response, data = http.request("%s/%s" % (self.game['endpoint'], resource), method=method, body=body, headers={"Content-type": "application/json"})

		if not allow_error and response.status != 200:
			print "Error ", data
			return False

		try:
			data = json.loads(data)
			if 'player' in data:
				player = data['player']
				self.resources = player['resources']
				self.generators = player['generators']
				self.improved_generators = player['improved_generators']
				del data['player']
		except ValueError:
			pass

		if allow_error:
			return response, data
		return data

	def can_purchase_pr(self):
		for resource in PR_COST:
			if self.resources[resource] < PR_COST[resource]:
				return False
		return True

	def purchase_pr(self):
		data = self.request('purchase_pr')
		if data:
			return data['highest_pr']

	def can_purchase_generator(self):
		if sum(self.generators.values()) >= MAX_RESOURCE_GENERATORS:
			return False # Can't have more than 5 generators

		for resource in GENERATOR_COST:
			if self.resources[resource] < GENERATOR_COST[resource]:
				return False
		return True

	def purchase_generator(self):
		data = self.request('purchase_generator')
		if data:
			return data['generator_type']
		return False

	def can_upgrade_generator(self):
		if sum(self.improved_generators.values()) >= MAX_IMPROVED_RESOURCE_GENERATORS:
			return False # Can't have more than 5 generators

		if sum(self.generators.values()) < 1:
			return False # Need an original generator to upgrade

		for resource in GENERATOR_IMPROVEMENT_COST:
			if self.resources[resource] < GENERATOR_IMPROVEMENT_COST[resource]:
				return False
		return True

	def upgrade_generator(self, generator_type=None):
		if not generator_type:
			for generator in self.generators:
				if self.generators[generator] > 0:
					generator_type = generator
					break

		if not generator_type:
			return False

		response, data = self.request('upgrade_generator', {"generator_type": generator_type}, allow_error=True)

		if response.status == 200:
			return data['generator_type']
		return False

	def trade(self, offering, requesting):
		response, data = self.request('trade', {'offering': offering, 'requesting': requesting}, allow_error=True)
		if response.status == 200:
			return data['accepted_by']
		return False

	def end_turn(self):
		self.request('end_turn')
		self.turn = False