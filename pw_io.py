
import matplotlib.pyplot 	as plt
import matplotlib.animation as animation
import numpy 				as np
import pandas 				as pd
from esa import SAW 					

from itertools import product

class TSContingencyEvent:

	def __init__(self, event):

		self.event = event["TSEventString"]
		self.object = event["WhoAmI"]
		self.time = event["TSTimeInSeconds"]

	def __str__(self) -> str:
		return f"({self.object}, {self.event}, T={self.time})"

#Does not implement CTG Elements yet, but it is in class
class TSContingency:

	def __init__(self, ctg_record, ctg_elem_records):

		#Data Structure
		self.name = ctg_record["TSCTGName"]
		self.ctg_events = [TSContingencyEvent(ctg_elem_records.loc[ind,:]) for ind in ctg_elem_records.index]
		self.ctg_record = ctg_record

	def __str__(self) -> str:
		return self.name
		#return f"TS Contingency Name: {self.label}\n" + "\n".join([ " --> " + str(e) for e in self.events])
	
	def __repr__(self):
		return f"{self.name} ({len(self.ctg_events)} Events)"
	
	def getName(self):
		return self.name
	
	# Parameter: actions DataFrame of TSContingencyElements
	def addEvents(self, events_df):

		#For Every TSContingencyElement create a TSEvent Object
		for event in events_df.to_dict('records'):
			self.events.append(TSContingencyEvent(event))

		return self
	
	#Number of Events
	def getNumEvents(self):
		return len(self.events)

# Transient Simulation Results Class for many tasks
# Parameters: 
# - Transient Data (Generic, N Dimensional)
class Transient:

	def __init__(self, data):
		self.data = data

	def __str__(self):
		return self.data[1].to_string()
	
	#TO-DO: Parameterize which field to animate over
	# e.g. Time Varying Frames, Load Varying Frames, etc
	@staticmethod
	def animation(transients, fps = 5):
		fig = plt.figure()

		def frames(i):
			plt.clf()
			return Transient.plot(transients[i]) 
			
		a = animation.FuncAnimation(fig, frames, frames=len(transients), interval=1000/fps)
		return a

	@staticmethod
	def saveAnimation(anim, filePath, fps=5):
		writergif = animation.PillowWriter(fps) 
		anim.save(filePath, writer=writergif)

	def stableRef(self, mw):
		self.nr_ref = mw

	@staticmethod
	# Super-Imposes the grid range over one plot, colored by different states
	def plotOverlay(transients):

		cmap = plt.get_cmap('gnuplot')
		colors = [cmap(i) for i in np.linspace(0, 1, len(transients))]

		for color, transient in zip(colors,transients):
			Transient.plot(transient, color)



	# Plot Transient Set
	# --> N Objects, 1 Field (for now)
	@staticmethod
	def plot(transient, color=None):

		#Only support 1 for now
		if isinstance(transient, list):
			transient = transient[0]

		#Get List of Series Names Excluding Sys Load MW
		meta 		= transient.data[0]
		sysMeta 	= meta.loc[meta["ObjectType"]=="Case Information"]
		seriesMeta 	= meta.loc[meta["ObjectType"]!="Case Information"]

		print(transient.data[1])
		print(sysMeta)

		#Extract Data
		time 		= transient.data[1]["time"]
		sysData 	= transient.data[1][sysMeta.index]
		seriesData 	= transient.data[1][seriesMeta.index]

		#For On-Screen Legend
		sysNames 	= list(sysMeta["ColHeader"])
		seriesNames = list(seriesMeta["ObjectType"] + " " + seriesMeta["PrimaryKey"])
		
		sysData.columns 	= sysNames
		seriesData.columns 	= seriesNames

		# Assumes Series Data Homogenous
		fields = seriesMeta["ColHeader"].unique()

		#If Color Specified
		if color is not None:
			plt.plot(time, seriesData, color=color)
		else:
			plt.plot(time, seriesData)

		plt.title("Transient Simulation")
		plt.xlabel("Time (s)")
		plt.ylabel(fields[0]) #Assume 1 Data Type
		plt.ylim(0.3,1.2)
		plt.xlim(time.min(), time.max())

		#Stable Ref
		'''		
		if self.nr_ref is not None:
			t = 0
			time_l =  list(reqData["time"])
			for i in range(len(time_l)):
				if self.nr_ref > self.loadData[0] + self.loadData[1]*time_l[i]:
					t = time_l[i]
				else:
					break
			plt.plotvline(x = t, color = 'b')
		'''
	

#Range of states - Abstract
class GridRange:

	def __init__(self, range, steps=None):

		#If Steps given, assumed numeric range
		if steps is not None:
			min = range[0]
			max = range[1]
			res = (max-min)/steps
			self._states = np.arange(min, max+res, res)
			self._seqLen = steps
		#Otherwise, a list of pre-determiend values
		else:
			self._states = range
			self._seqLen = len(range)

		self._seqNum = 0
	
	def __str__(self) -> str:

		s = f"GridRange ({self._seqLen} Combinations):\n"
		for state in self._states:
			s += str(state) + "\n"

		return s
	
	def __len__(self):
		return self._seqLen

	def __iter__(self):
		self._seqNum = 0
		return self
	
	def __next__(self):

		#Check if Survey Complete
		if self._seqNum == self._seqLen:
			raise StopIteration
		
		#Get State of current iteration
		state = self._states[self._seqNum]

		#Advance State & Return State
		self._seqNum += 1
		return state
	
	@staticmethod
	def validate(o):
		if isinstance(o, GridRange):
			return o
		elif isinstance(o, list):
			return GridRange(o)
		else:
			return GridRange([o])
		

# Survey  Implementations:
# - System-Load  MW (Load Mult)
# - Zone-Load Differential MW (Zones w/ High Load difference)
# - P/Q Ratio
# - Bus Shunts (G/Cap/Reactor)
# - Injection Groups
# - IBR % (Ratio of IBR to SG)
# - Zoned IBR/SG Differential (e.g. Large Inertial Zone & Small IBR Zone)
# - Contingencies (is this useful though?) - Maybe be a user-only loop
#
# Advanced Survey Implementations:
# - Alterntaive Grid Topologies
# - Control System Parameters
class GridConditions:

	def __init__(self):

		#Action Exists Without ESA until owned by another object
		self.esa = None

		#Built-In Configurable Grid Option Format
		# "Option Name": [Default Value, Implementation Function]
		self._options = {
			"Contingency": 
			[
				["SimOnly"],
				lambda *args: None
			],
			"Base Load":
			[
				[1],
				self.__configBaseLoad
			],
			"Ramp Rate":
			[
				[0],
				self.__configRampRate
			]
		}

		#Storage for custom ones
		self._custom_funcs = []

	# ESA object passed when survey called
	def __call__(self, esa):
		self.esa = esa
		return self
	
	# Enter with ESA Object
	def __enter__(self):
		self.esa.SaveState()
		#NEED TO SET LOAD ZONE LOADPMW to save on transients
		''' 
		CREATE Zone Load Characteristic - REturn message if not done
		load change Will not work without assigning sched to LC
		load_char = {
			"ObjectType": ["Zone"],
			"BusNum": ["Nan"],
			"LoadID": [""],
			"TSFlag": [1], # Enable Here
		}
		load_char = pd.DataFrame(load_char)
		self.esa.change_and_confirm_params_multiple_element(
			ObjectType='LoadCharacteristic_LoadTimeSchedule',
			command_df=load_char
		)
		'''
		return self
	
	#Safely Leave PW Case as it was entered - incase 2 sims are run
	def __exit__(self, type, value, traceback):
		self.esa.LoadState() 
		self.esa = None

	#Actual Ramp Application
	def __configRampRate(self, rate):

		# At T=0, LoadMult MUST be 1 for DSTimeSched
		sched = "WB_SCHED"
		time = 1000
		endLF = 1 + rate*time # Rate = Increase of load by (% of BaseLoad) per second
		data = {'DSTimeSchedName': [sched, sched], 'DSTimeSchedTime': [0, time], 'DSTimeSchedValue': [1, endLF]}
		data = pd.DataFrame(data)
		self.esa.change_and_confirm_params_multiple_element(
			ObjectType='DSTimeScheduleTimePoint',
			command_df=data
		)

	def __configBaseLoad(self, baseLoad):

		self.esa.change_and_confirm_params_multiple_element(
			ObjectType = 'Zone',
			command_df = pd.DataFrame({'ZoneNum': [1], 'SchedValue': [baseLoad]})
		)

	#Gets possible values for each option
	def __optionVals(self):
		for v in self._options.values():
			yield v[0]

	#Gets function for each option
	def __optionFuncs(self):
		for v in self._options.values():
			yield v[1]

	#Go through passed Grid Sequences and apply  states
	def apply(self):

		if not isinstance(self.esa, SAW):
			raise Exception("ESA not passed to conditional object to be applied.")

		#Apply every possible combination of options given
		for condition in product(*self.__optionVals()): 

			print("\nApplying to Power World: ")
			for option, optionFunc, value in zip(self._options.keys(), self.__optionFuncs(), condition):
				print(str(option) + " : " + str(value))
				optionFunc(value)

			yield condition[0] #Relies on internal structue having CTG first

	# Base Load
	def baseLoad(self, baseLoad):
		self._options["Base Load"][0] = GridRange.validate(baseLoad)
		return self		

	#User-Facing Sequence
	def loadRampRate(self, rate):
		self._options["Ramp Rate"][0] 	= GridRange.validate(rate)
		return self
	
	#Sets Contingencies to do by label name
	def contingencies(self, ctg):
		self._options["Contingency"][0] = GridRange.validate(ctg)
		return self
		
# ESA I/O Class for Transient Simulations
class TransientStabilityIO:

	def __init__(self, esa):

		#Grid Work Bench Object for IO
		self.esa = esa
		
		#Obj+Field Pair for Results
		self._objects = set()
		self._fields = set()
	
	#Define Objects of Interest
	def focus(self, *objects):
		self._objects = set(objects)
		return self
	
	#Define Fields for Objects (V, Hz, etc.)
	def fields(self, *objFields):
		self._fields = set(objFields)
		return self
	
	#Implement PF tolerance to prevent wiggle at start
	def PFTolerance(self, tol):
		return self
		
	# Order a TS Solve through ESA
	def dispatchTSSolve(self, ctg):

		#Produce Obj+Field Retrieval List
		# Zone '1' | TSLoadP
		objFieldList = [*self.objFields()]

		#Check Fields existing before trying to solve
		if len(objFieldList)<=0:
			raise Exception(f"No (Object,Field) pair in focus.")

		#Solve through ESA
		self.esa.RunScriptCommand(f'TSSolve("{ctg}")')

		#Get Specified Data Fields and return Transient DataFrame
		ts_data = self.esa.TSGetContingencyResults(ctg, objFieldList)

		print(ts_data)
	
		return Transient(ts_data)

	# Run TS for CTG in PW (Heavy-Compute Time)
	def solve(self, conditions=GridConditions()):

		sol = []

		#Solve Over All Conditions, Open Safely
		with conditions(self.esa):
			for ctg in conditions.apply():
				sol.append(self.dispatchTSSolve(ctg)) # Use a co-routine here....
				
		print("Simulations Complete")		
		return sol

	# Returns Array of Custom Transient Contingency Objects
	def getAllCTG(self):

		ctgs = []

		#Get Actual CTGs that are shown in PW (They can contain many steps or 'elements')
		ctg_fields = ["TSCTGName", "TSTimeInSeconds", "TimeStep", "Category", "CTGSkip", "CTGViol", "TSTotalLoadMWTripped", "TSTotalLoadMWIslanded"]
		ctg_records = self.esa.GetParametersMultipleElement("tscontingency", ctg_fields)

		# Retrieve CTG 'Steps'
		ctg_elem_fields = list(self.esa.GetFieldList("tscontingencyelement")["internal_field_name"])
		ctg_elem_records = self.esa.GetParametersMultipleElement("tscontingencyelement",ctg_elem_fields)
		
		# For Every Contingency 
		for ind in ctg_records.index:
			ctg_elems = ctg_elem_records.loc[ctg_elem_records["TSCTGName"]==ctg_records["TSCTGName"][ind],:]
			ctgs.append(TSContingency(ctg_records.loc[ind,:], ctg_elems))
		
		return ctgs
	
	# Object + Field Format for ESA
	def objFields(self):

		for o in self._objects:
			for f in self._fields:
				yield o + " | " + f   # Ex --> ["Bus '2' | TSBusVPU"]
	