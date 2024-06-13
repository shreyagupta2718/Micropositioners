# stage map: Maps the motorized stages' names to values the code can work with. tuples are (channel, axis). The motor controller 
# can only send commands to one channel at a time, but it can send commands to multiple axes on the same channel. 
# For this reason we wish to have x and y linear stages on the same channel so that we can control them simultaneously using 
# arrow keys. 
stage_map   = dict({'x':(1,1),'y':(1,2),'z':(3,1)})

#axis_speeds: Available speed options for the linear stages. Lowest -> highest: 1,2,4,3.  
axis_speeds = dict({'x':1,'y':1,'z':1})

# runnable: A global variable which is True if the computer successfully connected to the AGU-C8 motor controller,
# False otherwise. 
runnable = False # arbitrary value that is neither true nor false. When runnable has this value, we know that Initializer()
                 # has not been called yet. ???

jogspeed       = 0
measuredposition = 0
positivestepamplitude = 0

##################################################################################
## The code below follows the sample code provided by Newport in the AG-LS25-27
## software download package. 
##################################################################################
import sys
import os
import inspect
# Import the .NET Common Language Runtime (CLR) to allow interaction with .NET
import clr
import numpy as np
import time

print ("Python %s\n\n" % (sys.version,))

strCurrFile = os.path.abspath (inspect.stack()[0][1])
print ("Executing File = %s\n" % strCurrFile)
##################################################################################
## The code below follows the sample code provided by Newport in the AG-LS25-27
## soft
# Initialize the DLL folder path to where the DLLs are located
strPathDllFolder = os.path.dirname (strCurrFile)
print ("Executing Dir  = %s\n" % strPathDllFolder)

# Add the DLL folder path to the system search path (before adding references)
sys.path.append (strPathDllFolder)

# Add a reference to each .NET assembly required
clr.AddReference ("CmdLibAgilis")
clr.AddReference ("VCPIOLib")

# Import a class from a namespace
from Newport.Motion.CmdLibAgilis import *
from Newport.VCPIOLib import *
from System.Text import StringBuilder

################################################### FUNCTION DEFINITIONS ###################################################

# <summary>
# This method opens the first valid device in the list of discovered devices.
# </summary>
def OpenFirstValidDevice () :
    # For each device key in the list
    for oDeviceKey in strDeviceKeyList :
        strDeviceKey = str (oDeviceKey)
        
        # If the device was opened
        if (oCmdLib.Open (strDeviceKey) == 0) :
            return strDeviceKey

    # No device was opened
    return ""

# <summary>
# This function gets the jog speed of the specified axis.
# </summary>
def GetJogSpeed():
    global jogspeed
    bStatus,jogspeed = oCmdLib.GetJogMode(nAxis,jogspeed)
    
    if (bStatus):
        return True
    
    print ("ERROR! Could not get the jog speed.\n")
    return False

# <summary>
# This function sets the jog speed of the specified axis.
# </summary>
def SetJogSpeed(nAxis,targetjogspeed):
    bStatus = oCmdLib.StartJogging(nAxis,targetjogspeed)
    
    if (bStatus):
        return True
    
    print("ERROR! Could not set the jog mode!\n")
    return False

# <summary>
# This function stops motion along the specified axis.
# </summary>
def StopTheJogging(nAxis):
    bStatus = oCmdLib.StopMotion(nAxis)
    if (bStatus):
        return True
    
    print("ERROR! Could not stop jogging!\n")
    return False