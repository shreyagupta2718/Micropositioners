######################## Imports ##############################

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

########################### Global variables ###############################

# Defined below are several "speed_list" variables. speed_list contains the text that will appear in the
# drop-down menu from which a speed is selected. The actual speed settings that the motor controller accepts
# are integers 1 to 4. They are mapped to their corresponding "level" of speed in speed_list_dict.
# speed_list_z and speed_list_dict_z do a similar thing, but only with the two lowest speeds. This is because
# having a high speed for the vertical motorized stage risks damaging the sample or microscope objective lens.
speed_list = ["Very slow", "Slow", "Fast", "Very fast"]
speed_list_dict = ({"Very slow":1,"Slow":2,"Fast":3,"Very fast":4})
speed_list_z = ["Very slow", "Slow"]
speed_list_dict_z = ({"Very slow":1,"Slow":2})

# stage map: Maps the motorized stages' names to values the code can work with. tuples are (channel, axis). The motor controller 
# can only send commands to one channel at a time, but it can send commands to multiple axes on the same channel. 
# For this reason we wish to have x and y linear stages on the same channel so that we can control them simultaneously using 
# arrow keys. 
stage_map   = dict({'x':(1,1),'y':(1,2),'z':(3,1)})

#axis_speeds is initialized to slow, slow, very slow for x,y,z. Lowest -> highest: 1,2,3,4.  
init_x = "Slow"
init_y = "Slow"
init_z = "Very fast"
axis_speeds = dict({'x':speed_list_dict[init_x],'y':speed_list_dict[init_y],'z':speed_list_dict[init_z]})

# runnable: A global variable which is True if the computer successfully connected to the AGU-C8 motor controller,
# False otherwise. 
runnable = False # arbitrary value that is neither true nor false. When runnable has this value, we know that Initializer()
                 # has not been called yet. ???

#jogspeed       = 0
#measuredposition = 0
#positivestepamplitude = 0

########################### Helpers ########################################

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
# def GetJogSpeed():
#     global jogspeed
#     bStatus,jogspeed = oCmdLib.GetJogMode(nAxis,jogspeed)
    
#     if (bStatus):
#         return True
    
#     print ("ERROR! Could not get the jog speed.\n")
#     return False

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

############################ Open device, start communication ##############################

# <summary>
# Initializer: When called, checks if any valid devices are connected and opens the first one. IF MULTIPLE DEVICES CONNECTED
# THIS MAY HAVE TO BE CHANGED! (e.g. if camera is also connected-> test this out!???)
# Returns TRUE if a valid device was found, FALSE otherwise.
# </summary>
def Initializer():
    global stage_map, strDeviceKey, strDeviceKeyList, oCmdLib, oDeviceIO, runnable
    print ("Waiting for device discovery...\n")
    
    runnable = False # ???

    # Call the Virtual COM Port I/O Library constructor with 
    # true passed in so that logging is turned on for this sample
    oDeviceIO = VCPIOLib (True)
    oCmdLib = CmdLibAgilis (oDeviceIO)

    # Discover the devices that are available for communication
    oDeviceIO.DiscoverDevices ()

    # Get the list of discovered devices
    strDeviceKeyList = np.array ([])
    strDeviceKeyList = oDeviceIO.GetDeviceKeys ()

    # If no devices were discovered
    if (not strDeviceKeyList) : ## (not strDeviceKeyList) = True if empty!
        print ("No devices discovered.\n")
    else :
        # Open the first valid device in the list of discovered devices
        strDeviceKey = OpenFirstValidDevice ()
        #print ("Device Key = %s" % strDeviceKey)

        # If the device was opened
        if (strDeviceKey != "") :
            # Set the controller to Remote Mode
            if (oCmdLib.SetRemoteMode ()) :

                runnable = True
            else :
                print ("Could not put the controller into Remote Mode.\n")

        else :
            print ("Could not open the device.\n")

    return runnable

############################# Helpers to start and stop motion #########################

# <summary>
# Starts motion along input axis in input direction at input speed
# Returns True if motion started successfully, False otherwise.
# </summary>
def Start_Motion(axis,direction,speed):
    global stage_map, strDeviceKey, strDeviceKeyList, oCmdLib, oDeviceIO, runnable
    runnable2 = False
    if runnable: # We need to have called Initializer() before we can set channel and send commands
        (nChannel,nAxis) = stage_map[axis]
        if direction=='positive':
            targetjogspeed = speed
        else:
            targetjogspeed = -1*speed

        if (oCmdLib.SetChannel (nChannel)):
            SetJogSpeed(nAxis,targetjogspeed)

            runnable2 = True
        else:
            print ("Could not set the current channel in Start_Motion.\n")

    else:
        print("Initialization failed.\n")
    return runnable2

# <summary>
# Stops motion along input axis.
# Returns True if motion stopped successfully,
# False otherwise.
# </summary>
def Stop_Motion(axis):
    global stage_map, strDeviceKey, strDeviceKeyList, oCmdLib, oDeviceIO
    (nChannel,nAxis) = stage_map[axis]
    runnable3 = False
    #print("STOP_MOTION: nChannel = ",nChannel)
    if (oCmdLib.SetChannel (nChannel)):
        if StopTheJogging(nAxis):
            runnable3 = True
    else:
        print("ERROR! Command to end motion failed! THIS SHOULD NEVER BE PRINTED!!")
    return runnable3
# <summary>
# Stops motion along ALL axes on the AG-UC8 motor controller.
# Returns True if all motion stopped successfully, False
# otherwise.
# </summary>
def Stop_All_Motion():
    global stage_map, strDeviceKey, strDeviceKeyList, oCmdLib, oDeviceIO
    # Below, iterate over all channels and axes. AG-UC8 motor controller
    # has 4 channels each with 2 axes.
    lochannel = [1,2,3,4]
    loaxis    = [1,2]
    runnable4 = False
    time.sleep(0.1)         # see below for reason
    for nChannel in lochannel:
        for nAxis in loaxis:
            if (oCmdLib.SetChannel (nChannel)):
                if StopTheJogging(nAxis):
                    runnable4 = True
                else:
                    runnable4 = False
            time.sleep(0.1) # Without this there are issues. I think the AGU-C8 controller
                            # needs time to carry out its commands. (Can the issues also be
                            # caused by fast inputs? This would be a problem!)
    if runnable4 == True:
        print("All motion has been stopped.")
    else:
        print('ERROR! Command to end all motion failed! THIS SHOULD NEVER BE PRINTED!!.')
    return runnable4

###################################################################################################
######################################### TKINTER  GUI ############################################
###################################################################################################

import tkinter as tk
import tkinter.font as font
root = tk.Tk()
#root.geometry("210x275") # selects specific dimensions. Problematic as this needs to be changed any time you add a new widget.
root.title('Motor Control')
root.resizable(0, 0) # makes window un-resizeable
thefont = font.Font(size=30)

Initializer() # opens devices, begins communication

# next two global variables track which axes and directions are active/running.
# dir_status will contain "positive"/"negative" 
axis_status = dict({'x':False,'y':False,'z':False})
dir_status  = dict({'x':False,'y':False,'z':False})

# <summary>
# Runs the stage specified by 'axis' in the specified direction. If run_motor is called on a stage
# while the stage is already running, the command is ignored (because the two commands conflict).
# If the horizontal (x and y) stages are in motion and run_motor is called to activate vertical stage
# (z), this command is also ignored because the AGU-C8 motor controller cannot run them simultaneously.
# </summary>
def run_motor(axis,direction):
    try:
        global mydict, axis_status, dir_status, axis_speeds
        if axis_status[axis] == False: # We will only turn ON a linear stage if it is NOT already running!
            if ((axis=='x' or axis=='y') and axis_status['z'] == False) or (axis=='z' and (axis_status['x'] == False and axis_status['y'] == False)):
                # This condition is here because the z stage is connected in a separate channel to x and y linear
                # stages (the latter 2 of which are connected together). If z is running and then we send a command to run x/y,
                # the motor controller will first turn off z and then turn on x/y (because it cannot keep 2 separate channels
                # running simultaneously). This would make z stop while the program thinks it is still running, so might as well
                # not permit x/y to be activated while z is running and vice versa.
                print('motor began moving in {} {}.'.format(direction,axis))
                (mydict[(axis,direction)]).config(bg='blue') # for x and y, since they never get pressed so never display "active bgrnd"
                (mydict[(axis,direction)]).config(activebackground='blue') #for z, since button 1 makes them active
                if Start_Motion(axis,direction,axis_speeds[axis]):
                    axis_status[axis] = True # we are now moving in this axis, so this indicates it
                    dir_status[axis]  = direction
                    print("axis = {}, axis_status = {}, dir_status = {}".format(axis, axis_status[axis],dir_status[axis]))
                else: # this part is questionable. rework ???
                    print("Could not start motion. The program will be terminated.\n")
                    Stop_All_Motion()
                    root.destroy()

        elif (axis_status[axis]==True and dir_status[axis]==direction and axis=='z'): # if z axis is already running in input direction and we press
            stop_motor(axis,direction)                                                # button again, we want the z motor to stop. (This is not pretty code
            if (axis_status[axis] or dir_status[axis]):                               # structure, since this makes a stop command in a run_motor function.)
                print("Error! Stop function did not work. This shouldn't occur!")
                print(axis_status[axis],dir_status[axis])
    except:
        Stop_All_Motion()
        print("AN ERROR OCCURRED IN run_motor!")
        

def stop_motor(axis,direction):
    try:
        global mydict, axis_status, dir_status
        if axis_status[axis]==True and (dir_status[axis]==direction):  # only acts if the axis IS already running AND IN GIVEN DIRECTION
            (mydict[(axis,direction)]).config(bg='white')
            print("Motion along {} stopped.".format(axis))
            Stop_Motion(axis)
            axis_status[axis] = False
            dir_status[axis]  = False
    except:
        Stop_All_Motion()
        print("AN ERROR OCCURRED IN stop_motor!")

def manage_speeds(axis,selection):
    try:
        global axis_speeds
        axis_speeds[axis] = selection
        print("Speed in {} has been set to {}.\n".format(axis,selection))
    except:
        Stop_All_Motion()
        print("AN ERROR OCCURRED IN manage_speeds!")
        
def emergency_stop_button():
    try:
        global mydict, axis_status, dir_status
        if Stop_All_Motion():
            for axis in ['x','y','z']:
                axis_status[axis] = False
                dir_status[axis]  = False
                for direction in ['positive', 'negative']:
                    (mydict[(axis,direction)]).config(bg='white')
                    (mydict[(axis,direction)]).config(activebackground='white')
        else:
            print("Stop_All_Motion() failed in emergency_stop_button!!")
    except:
        print("AN ERROR OCCURRED IN emergency_stop_button!")

##################################  x motion  ##################################
move_x_right = tk.Button(root,text='right',bg='white')
move_x_right['font'] = thefont
move_x_right.grid(column=2,row=0,ipadx=1,ipady=1)

x_speed_frame = tk.Frame(root)
x_speed_frame.grid(column=1,row=0,padx=20,pady=10)
stage_label = tk.Label(x_speed_frame,text="Horizontal stage 1")
stage_label.grid()
x_speed_value = tk.StringVar(root)
x_speed_value.set(init_x) # Set the default value of the speed selection tab
x_speed_select = tk.OptionMenu(x_speed_frame, x_speed_value, *speed_list,command=lambda selection:manage_speeds('x',speed_list_dict[selection]))
x_speed_select.config(width=13)
x_speed_select.grid()

move_x_left = tk.Button(root,text='left',bg='white')
move_x_left['font'] = thefont
move_x_left.grid(column=0,row=0,ipadx=1,ipady=1)
##################################  y motion  ##################################
move_y_right = tk.Button(root,text='in',bg='white')
move_y_right['font'] = thefont
move_y_right.grid(column=2,row=1,ipadx=1,ipady=1)

y_speed_frame = tk.Frame(root)
y_speed_frame.grid(column=1,row=1,padx=20,pady=10)
stage_label = tk.Label(y_speed_frame,text="Horizontal stage 2")
stage_label.grid()
y_speed_value = tk.StringVar(root)
y_speed_value.set(init_y) # Set the default value of the speed selection tab
y_speed_select = tk.OptionMenu(y_speed_frame, y_speed_value, *speed_list,command=lambda selection:manage_speeds('y',speed_list_dict[selection]))
y_speed_select.config(width=13)
y_speed_select.grid()

move_y_left = tk.Button(root,text='out',bg='white')
move_y_left['font'] = thefont
move_y_left.grid(column=0,row=1,ipadx=1,ipady=1)

##################################  z motion  ##################################
move_z_right = tk.Button(root,text='down',bg='white')
move_z_right['font'] = thefont
move_z_right.grid(column=2,row=3,ipadx=1,ipady=1)
move_z_right.bind('<ButtonPress-1>',lambda event:run_motor('z','positive'))
#move_z_right.bind('<ButtonRelease-1>',lambda event:stop_motor('z','positive'))

z_speed_frame = tk.Frame(root)
z_speed_frame.grid(column=1,row=3,padx=20,pady=10)
stage_label = tk.Label(z_speed_frame,text="Vertical stage")
stage_label.grid()
z_speed_value = tk.StringVar(root)
z_speed_value.set(init_z) # Set the default value of the speed selection tab
z_speed_select = tk.OptionMenu(z_speed_frame, z_speed_value, *speed_list_z,command=lambda selection:manage_speeds('z',speed_list_dict[selection]))
z_speed_select.config(width=13)
z_speed_select.grid()

move_z_left = tk.Button(root,text='up',bg='white')
move_z_left['font'] = thefont
move_z_left.grid(column=0,row=3,ipadx=1,ipady=1)
move_z_left.bind('<ButtonPress-1>',lambda event:run_motor('z','negative'))
#move_z_left.bind('<ButtonRelease-1>',lambda event:stop_motor('z','negative'))
################################  other stuff  #################################
emergency_button = tk.Button(root, text="STOP ALL MOTION!")
emergency_button['font'] = font.Font(size=10)
emergency_button.grid(column=0,columnspan=3,row=4,ipadx=1,ipady=1)
emergency_button.bind('<ButtonPress-1>', lambda event:emergency_stop_button())

main_button = tk.Button(root,text="Click here for x-y motion")
main_button['font'] = font.Font(size=10)
main_button.grid(column=0,columnspan=3,row=5,ipadx=1,ipady=1)

main_button.bind('<Right>',lambda event:run_motor('x','positive'))
main_button.bind('<KeyRelease-Right>',lambda event:stop_motor('x','positive'))
main_button.bind('<Left>',lambda event:run_motor('x','negative'))
main_button.bind('<KeyRelease-Left>',lambda event:stop_motor('x','negative'))
main_button.bind('<Up>',lambda event:run_motor('y','positive'))
main_button.bind('<KeyRelease-Up>',lambda event:stop_motor('y','positive'))
main_button.bind('<Down>',lambda event:run_motor('y','negative'))
main_button.bind('<KeyRelease-Down>',lambda event:stop_motor('y','negative'))

main_button.focus_set()

# mydict: maps the 3 axes/motors (x,y,z) and 2 directions (positive, negative) to their
# respective buttons defined above. mydict must be defined after button definition and
# before root.mainloop() is called.
mydict = dict({
            ('z','negative'):move_z_left,
            ('z','positive'):move_z_right,
            ('y','negative'):move_y_left,
            ('y','positive'):move_y_right,
            ('x','negative'):move_x_left,
            ('x','positive'):move_x_right,
        })

root.mainloop()
# Close the device
oCmdLib.Close ()

print ("Shutting down.")

# Shut down all communication
oDeviceIO.Shutdown ()