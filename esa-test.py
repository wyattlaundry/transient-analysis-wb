CASE_PATH = r"C:\Users\wyatt\Documents\Power World\Cases\Hawaii\Hawaii40_20231026.pwb"

#Imports
from gridworkbench import GridWorkbench
from pw_io import *

#Grid Work Bench - Handles ESA Connection
wb = GridWorkbench()
wb.open_pwb(CASE_PATH)

# PW Transient Interface
tIO   = TransientStabilityIO(wb.esa)

# Grid Modifications
conditions = {
    BaseLoad	: trange(0.9, 1.9, n=30),
    Contingency	: tIO.getAllCTG()#All
}

# Solve Transients With Conditions
ts = tIO.runtime(5)						\
		.view("Bus", 31, "TSBusVPU")	\
		.solve(conditions)				\

#Animation 1
animConfig = {
    "Frames":{
        "Key": Contingency,
        "FPS": 3
	},
    "ColorBar": {
        "Key"  : BaseLoad,
        "Range": (1,2)
	},
    "Path": r"C:\Users\wyatt\Documents\Result1.gif"
}
ts.animate(animConfig)

#Close PW
wb.close_pwb()

















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

