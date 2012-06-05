import game
import logging

logging.basicConfig(filename='player.log',level=logging.DEBUG)
###########
### AI Controller with HTTP abstracted away
###
### DB is a wrapper for whatever storage is backing the AI
### Use this for storage across games
###
### game contains a "storage" object which is a dict which will be
### persisted after returning
###
###########

from game import RESOURCES, GENERATOR_COST, GENERATOR_IMPROVEMENT_COST, PR_COST, MAX_RESOURCE_GENERATORS, MAX_IMPROVED_RESOURCE_GENERATORS

turn_number = 0
surplus = 4
#turn to switch to PR purchasing
switch_to_pr = 70

def start_game(db, game):
    # A new game is starting
    logging.debug("NEW GAME STARTED")
    logging.debug("=======================================")
    print "Starting a game"

def start_turn(db, game, actions):
    global turn_number
    turn_number = turn_number + 1
    logging.debug("New Turn "+str(turn_number))
    logging.debug("=======================================")      

    def trade_for(requirements):

	requiredResources = {}
	availableResources = {}
        need_to_trade = False

	# Loop through each resource ( idea/feature/coffee/website/cash)
	for resource in RESOURCES:
            # If the resource is required for what we're trying to purchase, and the requirements
            # for that purchase are less than we currently have
            if resource in requirements:
		# Build a request dictionary which maps the type of resource we want (e.g idea)
		# to the amount of resources we require beyond what we currently have
                if requirements[resource] > game.resources[resource]:
                    requiredResources[resource] = requirements[resource] - game.resources[resource]
                    need_to_trade = True
                to_offer = game.resources[resource] - requirements[resource]
            else:
                to_offer = game.resources[resource]
            if to_offer > 0:
                availableResources[resource] = to_offer

        #DEBUG START
        logging.debug("required resources: ")
        for resource in requiredResources:
            logging.debug("     need resource "+resource+" - "+str(requiredResources[resource]))
        logging.debug("available resources: ")
        for resource in availableResources:
            logging.debug("     can trade resource "+resource+" - "+str(availableResources[resource]))
        #DEBUG END

        # Try getting each of the resources we need 1 at a time, iterating over the resources we have available to trade
        #offering only 1 of each of the resources at a time. method returns true if we collected enough resoures for the
        #desired resources.

        if need_to_trade:
            return trade_delivery(requiredResources, availableResources)
        else:
            return True

    #Algorithm for delivering trade requests
    #@return True if all of the required resources have been traded for, false if some are still missing
    def trade_delivery(requiredResources, availableResources):
        missingResources = False
        for resourceRequest in requiredResources:
            request = {resourceRequest : 1}
            if sum(availableResources.itervalues()) >= surplus:
                #we have enough surplus resources to trade with the bank, let's do it
                offer = {}
                surplus_count = 0;
                for resource in availableResources:
                    if surplus_count >= surplus:
                        break
                    else:
                        if availableResources[resource] > (surplus - surplus_count):
                            offer[resource] = surplus - surplus_count
                            surplus_count -= offer[resource]
                            availableResources[resource] -= offer[resource]
                        else:
                            offer[resource] = availableResources[resource]
                            surplus_count -= offer[resource]
                            availableResources[resource] -= offer[resource]
                game.trade(offer, request)
                requiredResources[resourceRequest] -= 1
            else:
                for availableResource in availableResources:
                    offer = {availableResource : 1}
                    logging.debug("trade offered: 1 "+resourceRequest+", we gave 1 "+availableResource)
                    if requiredResources[resourceRequest] > 0:
                        if game.trade(offer, request):
                            logging.debug("trade accepted for 1 "+resourceRequest+", we gave 1 "+availableResource)
                            requiredResources[resourceRequest] -= 1
                            availableResources[availableResource] -= 1
                    else:
                        logging.debug("trade declined")
                    if requiredResources[resourceRequest] > 0:
                        missingResources = True
        return not missingResources

    trade_failed = False
    #Only purchase PR when we are close to winning or after turn switch_to_pr
    while (game.get_customers() >= 8 or turn_number > switch_to_pr) and not trade_failed:
        logging.debug("     ...entering trade_for to obtain PR...")
        if trade_for(PR_COST):
            if game.can_purchase_pr() and game.turn:
                game.purchase_pr()
                logging.debug("purchased PR")
            else:
                trade_failed = True
        else:
            trade_failed = True
                

    trade_failed = False
    ### First try to trade for resources requiredResources
    # If we have less than the maximum number of generators
    while sum(game.generators.values()) < MAX_RESOURCE_GENERATORS and not trade_failed:
	# Try to trade for them
        logging.debug("     ...entering trade_for to obtain generators...")
        if trade_for(GENERATOR_COST):
            if game.can_purchase_generator() and game.turn:
                generator_type = game.purchase_generator()
                logging.debug("purchased generator "+generator_type)
            else:
                trade_failed = True
        else:
            trade_failed = True

    trade_failed = False
    # If we have less than the maximum number of improved generators
    while sum(game.improved_generators.values()) < MAX_IMPROVED_RESOURCE_GENERATORS and not trade_failed:
	# Can improve one of our existing ones
        logging.debug("     ...entering trade_for to obtain generator improvement...")
	if trade_for(GENERATOR_IMPROVEMENT_COST):
            if game.can_upgrade_generator() and game.turn:
                generator_type = game.upgrade_generator()
            else:
                trade_failed = True
        else:
            trade_failed = True

    if game.turn:
        game.end_turn()

def time_up(db, game):
    # We have ran out of time for this turn, it has been forced to end
    pass

def end_game(db, game, error=None):
    if error:
        print "Something went wrong! %s" % error
    else:
	print "Game over"

def goal_distance_after_trade(trade):
    trade_delta = 0
    for resource in trade:
        if resource in GENERATOR_COST:
            trade_delta += trade[resource]
        if resource in GENERATOR_IMPROVEMENT_COST:
            trade_delta += trade[resource]
        if resource in PR_COST:
            trade_delta += trade[resource]
    return trade_delta


#calculate distances after effect of trade, if the total sum of distances after the trade is greater
#than before the trade is 'bad' in the most general sense and should be rejected. Otherwise, accept.
def incoming_trade(db, game, player, offering, requesting):
    trade = {"cash": 0,"idea": 0,"website": 0,"coffee": 0,"feature": 0}
    for resource in RESOURCES:
        if resource in offering:
            trade[resource] += offering[resource]
        elif resource in requesting:
            trade[resource] -= requesting[resource]
    if goal_distance_after_trade(trade) > 0:
        return True
    else:
        return False