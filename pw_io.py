
import matplotlib.pyplot 	as plt
import matplotlib.animation as animation
import matplotlib 			as mpl
import numpy 				as np
import pandas 				as pd

from abc 		import ABC, abstractmethod
from esa 		import SAW, CommandNotRespectedError				
from itertools 	import product, groupby

#Helper Functions

#tRange
#Returns list of equally n equally spaces values inclusive over min max
def trange(min, max, n):
	res = (max-min)/(n-1)
	return np.arange(min, max+res, res)

# A singular action inside a contingency
class TSContingencyEvent:

	def __init__(self, event):

		self.event = event["TSEventString"]
		self.object = event["WhoAmI"]
		self.time = event["TSTimeInSeconds"]

	def __str__(self) -> str:
		return f"({self.object}, {self.event}, T={self.time})"

#Represents data for contingency
class TSContingency:

	def __init__(self, ctg_record, ctg_elem_records):

		#Data Structure
		self.name = ctg_record["TSCTGName"]
		self.ctg_events = [TSContingencyEvent(ctg_elem_records.loc[ind,:]) for ind in ctg_elem_records.index]
		self.ctg_record = ctg_record

	def __str__(self) -> str:
		return self.name
	
	def __repr__(self):
		return self.name
	
	def __lt__(self, other): 
		return self.name < other.name
	def __gt__(self, other): 
		return self.name > other.name
	def __le__(self, other): 
		return self.name <= other.name
	def __ge__(self, other): 
		return self.name >= other.name
	def __eq__(self, other): 
		return self.name == other.name
	def __ne__(self, other): 
		return self.name != other.name
	
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
	
#Transient Helper Class to assist in plotting/analysis
#Contains list of transients
class TransientSet:

	#Create Transient Set with a list of Transient Objects
	def __init__(self, transients):

		#Transient Data
		self.transients = list(transients)
		
		#Default Plot Colors
		for transient in self.transients:
			transient.setColor('b')


	#Returns number of frames
	def numFrames(self):
		return len(self.frameGroups[1])
	
	#For any given frame (should I make this frame-independent?) define color of a transient by a param
	# To-DO Call again if frameBy called after this??? only applies to non-range
	def colorBy(self, param, range=None):

		#Save param to assist in plotting
		self.colorParam = param

		#Set Global Color Map
		self.cmap = mpl.colormaps.get_cmap('cool')

		#Returns value in [0, 1] based on above ranges- Scalars Only
		def tColor(value):
			scaled = (value-min(self.cbMin, self.cbMax))/abs(self.cbMax-self.cbMin)
			clamped = max(min(1, scaled), 0)
			return self.cmap(clamped)
		
		if range: #Param should be numeric if range passed

			#Order matters
			self.cbMin = range[0]  # First element
			self.cbMax = range[-1] # Last Element

			#Color by Val if scalar
			for transient in self.transients:
				transient.setColor(tColor(transient.condition[param]))
			
		else: #Color by frame no range

			#For each frame
			for frameTransients in self.frameGroups[1]:

				#Linear Color scheme
				colors = [self.cmap(i) for i in np.linspace(0, 1, len(frameTransients))]
				for i, transient in enumerate(frameTransients):
					transient.setColor(colors[i])
		
	#Returns a list of keys and respective transient lists
	def group(self, rootParam):

		#Group keys and group lists
		groupKeys = []
		tGroups   = []

		#Returns Transient object by its desired parameter value
		def p(transient):
			return transient.condition[rootParam]

		#For each group, add the key and the list
		for k, g in groupby(sorted(self.transients, key=p), key=p):
			
			groupKeys.append(k)
			tGroups.append(list(g)) 

		return groupKeys, tGroups
	
	#Accessed by animation function
	def frames(self, i):

		#Clear last frame
		self.ax.clear()

		#Per-Frame Transient Data
		transients = self.frameGroups[1][i] # Transient Object List
		frameParamValue = self.frameGroups[0][i] #Value Unique to frame

		#Frame Sub-Title
		self.ax.set_title(self.frameParam.toStr() + ": " + r"$\bf{" + str(frameParamValue) + "}$" , 
					loc="left",
					fontsize=9)
		
		#Axis Titles - NEED ACCESS TO REQESTED FIELDS
		self.ax.set(xlabel="Time (s)", ylabel=f"Bus Voltage p.u.")
		
		#Plot all onto this frame
		for transient in transients:
			transient.plot(self.fig, self.ax)

		return (self.fig, self.ax)
	
	#Static Helper function to animate transient related data
	def animate(self, config):

		#Generate frames by parameter
		self.frameGroups = self.group(config["Frames"]["Key"])
		self.frameParam  = config["Frames"]["Key"]
		fps = config["Frames"]["FPS"]

		#Save Location
		filePath = config["Path"]

		#Blank plot
		fig, ax = plt.subplots()

		#Construct CB 
		if (c_key := config["ColorBar"]["Key"]) and (c_rng:= config["ColorBar"]["Range"]):

			#Color config
			self.colorBy(c_key, c_rng)

			#CB Object
			cb = fig.colorbar(	mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(self.cbMin, self.cbMax), cmap=self.cmap),
								ax=ax, 
								orientation='vertical', 
								label=c_key.toStr())
			
			#Flip if passed values in reverse order
			if self.cbMin > self.cbMax:
				cb.ax.invert_yaxis()
			
		#Make Animation
		self.fig = fig
		self.ax = ax
		anim = animation.FuncAnimation(fig, self.frames, frames=self.numFrames(), interval=1000/fps)
		
		#Save Animation
		writergif = animation.PillowWriter(fps) 
		anim.save(filePath, writer=writergif)

# Class Representing dat aof a single Transient Simulation
# Fields:
# - Sim Data
# - Grid Conditions During Sim
class Transient:

	#Transient Data and the Grid Conditions it was performemd on
	def __init__(self, data, condition):
		self.data = data
		self.condition = condition
		self.plotColor = 'b'

	#String representation: output pandas table
	def __str__(self):
		return self.data[1].to_string()
	
	def setColor(self, color):
		self.plotColor = color

	# Plot Transient Set (basic, just gets values on screen. TGroup handlees varaiations)
	def plot(self, fig=None, ax=None):

		#Get List of Series Names Excluding Sys Load MW
		meta 		= self.data[0]
		sysMeta 	= meta.loc[meta["ObjectType"]=="Case Information"]
		seriesMeta 	= meta.loc[meta["ObjectType"]!="Case Information"]

		#Extract Data
		time 		= self.data[1]["time"]
		sysData 	= self.data[1][sysMeta.index]
		seriesData 	= self.data[1][seriesMeta.index]

		#For On-Screen Legend
		sysNames 	= list(sysMeta["ColHeader"])
		seriesNames = list(seriesMeta["ObjectType"] + " " + seriesMeta["PrimaryKey"])
		
		sysData.columns 	= sysNames
		seriesData.columns 	= seriesNames

		# Assumes Series Data Homogenous
		fields = seriesMeta["ColHeader"].unique()

		if fig == None:
			fig, ax = plt.subplots()

		#Plot with Specified Color
		ax.plot(time, seriesData, color=self.plotColor)
		
		#Plot Options
		fig.suptitle("Transient Simulation", fontsize=14, fontweight='bold')
		ax.set_ylim(0.3,1.2)
		ax.set_xlim(time.min(), time.max())

class Condition(ABC):

	@property
	@abstractmethod
	def default():
		pass

	@staticmethod
	@abstractmethod
	def toStr():
		pass

	@staticmethod
	@abstractmethod
	#Target condition config is passed, including this condition!
	def apply(esa, conditions):
		pass

class Contingency(Condition):

	default = ["SimOnly"]

	def toStr():
		return "Contingency"

	def apply(esa, conditions):
		pass

class BaseLoad(Condition):

	default = [1]

	def toStr():
		return "Base Load MW Mult"

	def apply(esa, conditions):

		baseLoad = conditions[BaseLoad]

		esa.change_and_confirm_params_multiple_element(
			ObjectType = 'Zone',
			command_df = pd.DataFrame({'ZoneNum': [1], 'SchedValue': [baseLoad]})
		)

class RampRate(Condition):

	default = [0]

	def toStr():
		return "Ramp Rate"

	def apply(esa, conditions):

		rate = conditions[RampRate]

		# At T=0, LoadMult MUST be 1 for DSTimeSched
		sched = "WB_SCHED"
		time = 1000
		endLF = 1 + rate*time # Rate = Increase of load by (% of BaseLoad) per second
		data = {'DSTimeSchedName': [sched, sched], 'DSTimeSchedTime': [0, time], 'DSTimeSchedValue': [1, endLF]}
		data = pd.DataFrame(data)
		esa.change_and_confirm_params_multiple_element(
			ObjectType='DSTimeScheduleTimePoint',
			command_df=data
		)

# Conditions to Implement:
# - Zone-Load Differential MW (Zones w/ High Load difference)
# - Load P/Q Ratio
# - Bus Shunts (G/Cap/Reactor)
# - Injection Groups
# - IBR % (Ratio of IBR to SG)
# - Zoned IBR/SG Differential (e.g. Large Inertial Zone & Small IBR Zone)
# - Contingencies (is this useful though?) - Maybe be a user-only loop
#
# Advanced Survey Implementations:
# - Alterntaive Grid Topologies
# - Control System Parameters
class GridIterator:

	conditionOptions =  {
		Contingency	: Contingency.default,
		BaseLoad	: BaseLoad.default,
		RampRate	: RampRate.default #'step size' next
	}

	def __init__(self, conditions, esa):

		#Add Condition if only valid Condition type
		for condition, value in conditions.items():
			if type(condition) is type(Condition):
				self.conditionOptions[condition] = self.__toIter(value)

		#Action Exists Without ESA until owned by another object
		self.esa = esa
	
	# Enter with ESA Object
	def __enter__(self):

		# Save pre-simulation state so it can be restored if anything goes wrong
		if not self.esa.SaveState():
			print("Case backup saved for restoration.")
		else:
			print("Failed to save case state. Investigate before continuing.")

		# Create 'SimOnly' contingency if it does not exist
		try:
			self.esa.change_and_confirm_params_multiple_element(
				ObjectType = 'TSContingency',
				command_df = pd.DataFrame({'TSCTGName': ['SimOnly']})#, 'SchedValue': [baseLoad]})
			)
		except(CommandNotRespectedError):
			print("Failure to create 'SimOnly' Contingency")
		else:
			print("Contingency 'SimOnly' Initialized")

		#TSGetVCurveData("FileName", filter);This field comapres to QV curve!

		#TSRunResultAnalyzer PW Post-transient analysis

		#Tolerance MVA

		#Need to auto create DSTimeSChedule & LoadCharacteristic for Ramp
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
		print("Begining Simulations\n")

		return self
	
	#Safely Leave PW Case as it was entered - incase 2 sims are run
	def __exit__(self, type, value, traceback):

		print("Simulations Finished.\n")

		#Revert to original state
		print("Reverting to original PF state.")
		self.esa.LoadState() 

		#Disable ram storage for all objects when done
		print("Disabling RAM Results Storage")
		self.esa.RunScriptCommand('TSResultStorageSetAll(ALL, NO)')

		# Clear Ram TSClearResultsFromRAM Need to determine how this affets this program before adding
		# SaveCase() Do I want to commit these changes? Don't know yet

		self.esa = None

	#Go through passed Grid Sequences and apply  states
	def applyAll(self):

		#If ESA not passed
		if not isinstance(self.esa, SAW):
			raise Exception("ESA not passed to conditional object to be applied.")

		#Apply every possible combination of options given
		for allConditionPerm in product(*self.conditionOptions.values()): 

			print("Applying to Power World: ")

			scenario = dict(zip(self.conditionOptions.keys(), allConditionPerm))
			for option, value in scenario.items():
				print(option.toStr() + " : " + str(value))
				option.apply(self.esa, scenario)

			print()

			yield scenario
	
	#Forces inputs into iterable since we treat them all as loops
	def __toIter(self, obj):

		#Checks to see if param is iterable or singular
		try:
			iterator = iter(obj)
		except TypeError:
			return [obj]
		else:
			return obj
		
# ESA I/O Class for Transient Simulations
class TransientStabilityIO:

	def __init__(self, esa):

		#PW Interface
		self.esa = esa
		
		#Sim duration - None -> by Contingency
		self.__runtime = None

		#Fields to retrieve data from
		self.targetFields = []
		
	# Order a TS Solve through ESA - condtion must be contain single bits
	def dispatchTSSolve(self, scenario):

		#Save  fields in RAM during sim
		for objType in map(lambda x: x["Object"], self.targetFields):
			self.esa.RunScriptCommand(f'TSResultStorageSetAll({objType}, YES)')
		
		#Make PW formatted object field list
		objFieldList = list(map(
			lambda o: f"{o['Object']} '{o['ID']}' | {o['Field']}",
			self.targetFields
		))

		#Solve through ESA
		if self.__runtime:
			script = f'TSSolve({scenario[Contingency]}, [0,{self.__runtime}])'
		else:
			script = f'TSSolve({scenario[Contingency]})'
		self.esa.RunScriptCommand(script)
		

		#Get Specified Data Fields and return Transient DataFrame
		ts_data = self.esa.TSGetContingencyResults(scenario[Contingency], objFieldList)

		return Transient(ts_data, scenario)
	
	#Set Runtime
	def runtime(self, sec):
		self.__runtime = sec
		return self
	
	# Add TS parameter to record
	def view(self, obj, id, field):

		#only one target for now
		self.targetFields=[{
			"Object": obj,
			"ID": id,
			"Field": field
		}]

		return self
	
	# Run TS for CTG in PW (Heavy-Compute Time)
	def solve(self, conditions={}):

		#Check Fields existing before trying to apply anything
		if len(self.targetFields)<=0:
			raise Exception(f"No (Object,Field) pair in focus.")

		#Solve Over All Conditions, Open Safely
		def compute():
			with GridIterator(conditions, self.esa) as grid:
				for scenario in grid.applyAll():
					yield self.dispatchTSSolve(scenario) # To-Do: Use a co-routine here to plot while computing....
					
		return TransientSet(compute())

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
	
	