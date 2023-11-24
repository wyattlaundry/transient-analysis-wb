CASE_PATH = r"C:\Users\wyatt\OneDrive - Texas A&M University\PhD Research\Stability Project\Cases\Hawaii\Hawaii40_20231026.pwb"

#Imports
from gridworkbench import GridWorkbench
from pw_io import TransientStabilityIO
from pw_io import Transient
from pw_io import GridRange
from pw_io import GridConditions
import matplotlib.pyplot as plt

#Grid Work Bench - Handles ESA Connection
wb = GridWorkbench()
wb.open_pwb(CASE_PATH)

#Transient Object
tIO = TransientStabilityIO(wb.esa)
tCTGS = tIO.getAllCTG()

#Ranged Varaibles
baseLoad = GridRange(range = [1.4, 4.8], steps = 2)
rampRate = GridRange(range = [0.01, 0.2], steps = 12)
ctgs 	 = GridRange([tCTGS[5]])

#Grid Behavior
conditions = (GridConditions() 
			.baseLoad(1)
			.loadRampRate(0)
            .contingencies(tCTGS[0]))

#Configure TS Event
#Func to set time of simulation (conditional/determiend)
tIO.focus(*["Bus '" + str(i) + "'" for i in range(2,15)])  	\
   .fields("TSBusVPU")

# Solve
ts = tIO.solve(conditions)
	
# Display	
Transient.plotOverlay(ts)
plt.show()
#a = Transient.animation(ts)
#plt.show()

#Close PW
wb.close_pwb()

# Save
#filePath = r"C:\Users\wyatt\OneDrive - Texas A&M University\PhD Research\Stability Project\Visuals\anim.gif"
#Transient.saveAnimation(a, filePath)


'''

Power Flow - Not in Use


#Reference from NR PF (Load Mult)
for t in ts:
	t.stableRef(2)

base_mw = 1136.29
solved_set = {"Load" : []}
for i in range(100):

	m = 0.9 + i/20

	data = {'ZoneNum': [1], 'SchedValue': [m]}
	data = pd.DataFrame(data)
	wb.esa.change_and_confirm_params_multiple_element(
		ObjectType='Zone',
		command_df=data
	)

	try:
		cmd = "SolvePowerFlow(RECTNEWT)"
		wb.esa.RunScriptCommand(cmd)
	except:
		break

	solved_set["Load"].append(m*base_mw)

print(solved_set)

'''

