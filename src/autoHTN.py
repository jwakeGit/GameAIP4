import pyhop
import json

def check_enough (state, ID, item, num):
	if getattr(state,item)[ID] >= num: return []
	return False

def produce_enough (state, ID, item, num):
	return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods ('have_enough', check_enough, produce_enough)

def produce (state, ID, item):
	return [('produce_{}'.format(item), ID)]

pyhop.declare_methods ('produce', produce)

def make_method (name, rule):
	def method (state, ID):
		subtasks = []
		plank_subtask = None

		# if this method consumes any items
		if 'Consumes' in rule:

			# look at all the items
			for item, num in rule['Consumes'].items():
				if item != 'plank':
					subtasks.append(('have_enough', ID, item, num))
				else:
					plank_subtask = ('have_enough', ID, item, num)
		
		# if this method has preconditions
		if 'Requires' in rule:
			# look at all the preconditions
			for item, num in rule['Requires'].items():
				subtasks.append(('have_enough', ID, item, num))

		if plank_subtask is not None:
			subtasks.append(plank_subtask)

		subtasks.append(('op_' + name, ID))
		
		return subtasks
		
	return method

def declare_methods (data):
	# some recipes are faster than others for the same product even though they might require extra tools
	# sort the recipes so that faster recipes go first

	data_sorted = []

	# look at all the recipes in the crafting.json
	for name, rule in data['Recipes'].items():
		# if data_sorted isn't empty
		if len(data_sorted) != 0:
			i = 0

			# look at each recipe in data_sorted
			for other_name, other_rule in data_sorted:
				# if the recipe in crafting.json is faster than the recipe in data_sorted
				if rule['Time'] < other_rule['Time']:
					# stop looking
					break
				
				i += 1

			# put the recipe before the slower recipe in data_sorted
			data_sorted.insert(i, (name, rule))
		else:
			data_sorted.append((name, rule))
	
	methods_list = {}

	# look at all the recipes in data_sorted
	for name, rule in data_sorted:
		method = make_method(name, rule)
		method.__name__ = name

		# look at each item that this method produces
		for item in rule['Produces'].keys():
			# if there are other methods that produce the item
			if item in methods_list:
				# add this method to the list
				methods_list[item].append(method)
			else:
				methods_list[item] = [method]
	
	# look at all the items along with their methods in methods_list
	for item, methods in methods_list.items():
		pyhop.declare_methods('produce_' + item, *methods)

	# for method_name, rule in data['Recipies'].items():
		# method = make_method(method_name, rule)
			# note: i'm not sure what we do with the name argument in make_method.
		# method.__name__ = 'produce_' + method_name
		# for each subtask method that could be used to make this:
			# index them in a tuple with inverse relation to their efficiency
				# for example: subtask_tuple[0] = most efficient subtask

		# pyhop.declare_methods(method_name, subtask_tuple)	
	pass			

def make_operator (rule):
	def operator (state, ID):
		# if we have time to do this operator
		if state.time[ID] >= rule['Time']:
			# if this operator has preconditions
			if 'Requires' in rule:
				# look at all the preconditions
				for item, num in rule['Requires'].items():
					# if we don't have enough of an item
					if getattr(state,item)[ID] < num:
						print('debug 1')
						return False
						
			# if this operator consumes any items
			if 'Consumes' in rule:
				# update all the items that this operator consumes
				for item, num in rule['Consumes'].items():
					# calculate the amount of an item after doing this operator
					num_new = getattr(state,item)[ID] - num

					# if we don't have enough of the item
					if num_new < 0:
						print('debug 2')
						return False

					setattr(state, item, {ID: num_new})
			state.time[ID] -= rule['Time']
			
			# update all the items that this operator produces
			for item, num in rule['Produces'].items():
				setattr(state, item, {ID: getattr(state,item)[ID] + num})
			return state
		print('debug 3')
		return False
	return operator

def declare_operators (data):
	# look at all the recipes in the crafting.json
	for operator_name, rule in data['Recipes'].items():
		operator = make_operator(rule)
		operator.__name__ = 'op_' + operator_name

		pyhop.declare_operators(operator)
	pass

def add_heuristic (data, ID):
	# prune search branch if heuristic() returns True
	# do not change parameters to heuristic(), but can add more heuristic functions with the same parameters: 
	# e.g. def heuristic2(...); pyhop.add_check(heuristic2)
	# def tool_heuristic (state, curr_task, tasks, plan, depth, calling_stack):
	# 	print(curr_task)
	# 	print(tasks)

	# 	if 'produce' in curr_task:
	# 		if 'wooden_axe' in curr_task:
	# 			if state.made_wooden_axe[ID] is True or \
	# 			state.made_stone_axe[ID] is True or \
	# 			state.made_iron_axe[ID] is True:
	# 				print('dont do wooden_axe')
	# 				return True
	# 			else:
	# 				state.made_wooden_axe[ID] = True
	# 				print('made wooden axe')
	# 		elif 'stone_axe' in curr_task:
	# 			if state.made_stone_axe[ID] is True or \
	# 			state.made_iron_axe[ID] is True:
	# 				print('dont do stone_axe')
	# 				return True
	# 			else:
	# 				state.made_stone_axe[ID] = True
	# 				print('made stone axe')
	# 		elif 'iron_axe' in curr_task:
	# 			if state.made_iron_axe[ID] is True:
	# 				print('dont do iron_axe')
	# 				return True
	# 			else:
	# 				state.made_iron_axe[ID] = True
	# 				print('made iron axe')
	# 		elif 'wooden_pickaxe' in curr_task:
	# 			if state.made_wooden_pickaxe[ID] is True or \
	# 			state.made_stone_pickaxe[ID] is True or \
	# 			state.made_iron_pickaxe[ID] is True:
	# 				print('dont do wooden_pickaxe')
	# 				return True
	# 			else:
	# 				state.made_wooden_pickaxe[ID] = True
	# 		elif 'stone_pickaxe' in curr_task:
	# 			if state.made_stone_pickaxe[ID] is True or \
	# 			state.made_iron_pickaxe[ID] is True:
	# 				print('dont do stone_pickaxe')
	# 				return True
	# 			else:
	# 				state.made_stone_pickaxe[ID] = True
	# 		elif 'iron_pickaxe' in curr_task:
	# 			if state.made_iron_pickaxe[ID] is True:
	# 				print('dont do iron_pickaxe')
	# 				return True
	# 			else:
	# 				state.made_iron_pickaxe[ID] = True
	# 	return False # if True, prune this branch
	
	# pyhop.add_check(tool_heuristic)
	
	def overarching_heuristic (state, curr_task, tasks, plan, depth, calling_stack):
		print(curr_task)
		print(tasks)

		if 'produce' in curr_task:
			if 'wooden_axe' in curr_task:
				if state.axe_tier < 1: return True
				elif state.made_wooden_axe[ID] is True:
					return True
				else:
					state.made_wooden_axe[ID] = True
			elif 'stone_axe' in curr_task:
				if state.axe_tier < 2: return True
				elif state.made_stone_axe[ID] is True:
					return True
				else:
					state.made_stone_axe[ID] = True
			elif 'iron_axe' in curr_task:
				if state.axe_tier < 3: return True
				if state.made_iron_axe[ID] is True:
					return True
				else:
					state.made_iron_axe[ID] = True
			elif 'wooden_pickaxe' in curr_task:
				if state.pickaxe_tier < 1: return True
				elif state.made_wooden_pickaxe[ID] is True:
					return True
				else:
					state.made_wooden_pickaxe[ID] = True
			elif 'stone_pickaxe' in curr_task:
				if state.pickaxe_tier < 2: return True
				if state.made_stone_pickaxe[ID] is True:
					return True
				else:
					state.made_stone_pickaxe[ID] = True
			elif 'iron_pickaxe' in curr_task:
				if state.pickaxe_tier < 3: return True
				if state.made_iron_pickaxe[ID] is True:
					return True
				else:
					state.made_iron_pickaxe[ID] = True

	pyhop.add_check(overarching_heuristic)


def set_up_state (data, ID, time=0):
	state = pyhop.State('state')
	state.time = {ID: time}
	state.axe_tier = 0
	state.pickaxe_tier = 1

	for item in data['Items']:
		setattr(state, item, {ID: 0})

	for item in data['Tools']:
		setattr(state, item, {ID: 0})
		setattr(state, 'made_' + item, {ID: False})

	for item, num in data['Initial'].items():
		setattr(state, item, {ID: num})

	return state

def set_up_goals (data, ID):
	goals = []
	for item, num in data['Goal'].items():
		goals.append(('have_enough', ID, item, num))

	return goals

if __name__ == '__main__':
	rules_filename = 'crafting.json'

	with open(rules_filename) as f:
		data = json.load(f)

	state = set_up_state(data, 'agent', time=175) # allot time here
	goals = set_up_goals(data, 'agent')

	declare_operators(data)
	declare_methods(data)
	add_heuristic(data, 'agent')

	for scan_task in goals:
		pickaxe_tier_3 = ["cart", "rail", "iron_pickaxe"]
		pickaxe_tier_2 = ["ingot", "ore", "furnace", "iron_axe", "stone_pickaxe"]
		pickaxe_tier_1 = ["coal", "cobble", "stone_axe"]

		axe_tier_3 = ["iron_axe"]
		axe_tier_2 = ["stone_axe"]
		axe_tier_1 = ["wooden_axe"]
				
		if any(x in scan_task for x in pickaxe_tier_3): state.pickaxe_tier = 3
		elif any(x in scan_task for x in pickaxe_tier_2): state.pickaxe_tier = 2
		elif any(x in scan_task for x in pickaxe_tier_1): state.pickaxe_tier = 1

		if any(x in scan_task for x in axe_tier_3): state.axe_tier = 3
		elif any(x in scan_task for x in axe_tier_2): state.axe_tier = 2
		elif any(x in scan_task for x in axe_tier_1): state.axe_tier = 1

	# pyhop.print_operators()
	# pyhop.print_methods()

	# Hint: verbose output can take a long time even if the solution is correct; 
	# try verbose=1 if it is taking too long
	print(state.pickaxe_tier)
	pyhop.pyhop(state, goals, verbose=1)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)
