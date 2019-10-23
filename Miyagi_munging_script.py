#################################################################
# Information about This Script
#################################################################

# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 15:16:32 2019

@author: bellwoar(UPenn iGEM2019)
@author: Keisuke Yamada(UPenn iGEM2019)
"""

###Munge File for #MillerLab OpenSLS
#
# Ian Kinstlinger
# Revised 08/2015
#
#


##################################################################
# Import Libraries
##################################################################


### Import Libraries

import math
import re
import os
from Tkinter import Tk
from tkFileDialog import askopenfilename
from tkFileDialog import asksaveasfile
#from tkFileDialog import asksave


#################################################################
#Define Parameters
##################################################################


### Define Parameters
## Parameters appearing on .gcode files
## Change numbers when necessary
TRAVEL_SPEED = 9000 #[mm/min] moving speed while not extruding
PRINT_SPEED = 10000 #[mm/min] moving speed while extruding(printing speed)
FAN_SPEED = 255 #0-255 strength of fan(pressure)
WAX_TEMP = 90 #[Celcius] temperature of wax to be heated
BED_TEMP = 0 #[Celcius] temperature of printer bed
WAX_WAIT_TIME = 0 #[sec]
COLD_EXTRUDE_TEMP = 40 #[Celcius] allow cold extrusion
MAX_ACCELERATION_X = 3000 #Default=1000 [mm/min]
MAX_ACCELERATION_Y = 3000 #Default=1000 [mm/min]
MAX_ACCELERATION_Z = 3000 #Default=1000 [mm/min]
MAX_ACCELERATION_E = 5000 #Default=5000 [mm/min]
PRINT_ACCELERATION = 3000 #Default=1250 [mm/min]
RETRACT_ACCELERATION = 1250 #Default=1250 [mm/min]
TRAVEL_ACCELERATION = 1250 #Default=1250 [mm/min]
MAX_FEEDRATE_X = 200 #Default=200 [mm/min]
MAX_FEEDRATE_Y = 200 #Default=200 [mm/min]
MAX_FEEDRATE_Z = 12 #Default=12 [mm/min]
MAX_FEEDRATE_E = 120 #Default=120 [mm/min]
FIRMWARE_VERSION = '3.7.2'


### Define Extrusion Parameters
## Parameters used within this munging script
extrusion_method = 'continuous' #Default='continuous', alternative variable is 'dropwise'
z_height_manual = 3 #Default=3[mm], height of the extruder while extruding wax
#This Parameter only affect continuous extrusion
angle_limit = 60 #Default=60[deg], maximum angle changes for continuous extrusion
#These four parameters only affect dropwise extrusion
switching_time = 30 #Default=30[ms] ON/OFF switching time of pressure
drop_interval = 1.2 #Default=1.2 [mm] Interval of droplets
count_dots = 20 #Default=20 Number of dots


### Define Internal Parameters
## Parameters internally used within this munging script
## Do not change these parameters unless changing the whole algorithm
absolute_flg = 0
prev_position = [0,0,0] #[x,y,z]
next_position = [0,0,0] #[x,y,z]
prev_prev_position = [0,0,0] #[x,y,z]
next_angle = 1000 #[deg]
prev_angle = 1000 #[deg]
first_line_flg = 0
length_remain = 0.0 #[mm]
#last_lines = 'G4 ; wait\n' \
#             'M221 S100\n' \
#             'M104 S0 ; turn off temperature\n' \
#             'M140 S0 ; turn off heatbed\n' \
#             'M107 ; turn off fan\n' \
#             'M1001 ; turn off wax mode\n' \
#             'M84 ; disable motors\n' \
#             'G28 W ; move to the home position\n' \
#             'G0 X20 Y20 Z50\n'
#             'M73 P100 R0\n' \
#             'M73 Q100 S0\n'
last_lines = 'G4 ; wait\n'\
             'M221 S100\n'\
             'M107 ; turn off fan\n'\
             'M84 ; disable motors\n'\
             'G0 X20 Y20 Z50 F3000\n'\
             'M73 P100 R0\n'\
             'M73 Q100 S0\n'
line_library = [] #[beginning x, beginning y, ending x, ending y]
rest_library = []


##################################################################
# Define Functions
##################################################################


## Function to update the extruder position
def updatePosition(line_update, position):
    x_update = position[0]
    y_update = position[1]
    z_update = position[2]

    if re.search('X-?[0-9.]+', line_update):
        x_update = float((re.search('X-?[0-9.]+', line_update)).group(0)[1:])

    if re.search('Y-?[0-9.]+', line_update):
        y_update = float((re.search('Y-?[0-9.]+', line_update)).group(0)[1:])

    if re.search('Z-?[0-9.]+', line_update):
        z_update = float((re.search('Z-?[0-9.]+', line_update)).group(0)[1:])

    return [x_update,y_update,z_update]

## Function to update the angle between previous and next movement
def updateAngle(prev_prev_pos_angle, prev_pos_angle, next_pos_angle):
    new_diagonal = math.sqrt((next_pos_angle[0]-prev_pos_angle[0])**2+(next_pos_angle[1]-prev_pos_angle[1])**2)
    new_base = math.sqrt((prev_pos_angle[0]-prev_prev_pos_angle[0])**2+(prev_pos_angle[1]-prev_prev_pos_angle[1])**2)
    new_angle = math.degrees(math.acos(min(new_diagonal, new_base)/max(new_diagonal, new_base)))

    return new_angle

## Function to shorten the printed line for 'len_shorten' [mm]
#Line direction is [x1,y1]->[x2,y2]
#x2, y2 side is curtailed
def shortenLine(x1_shorten, y1_shorten, x2_shorten, y2_shorten, len_shorten):
    length_shorten = math.sqrt((x2_shorten-x1_shorten)**2+(y2_shorten-y1_shorten)**2)
    length_base = abs(x2_shorten-x1_shorten)

    angle_shorten = math.acos(length_base/length_shorten)
    if y2_shorten>=y1_shorten and x2_shorten<=x1_shorten:
        angle_shorten = math.pi-angle_shorten
    elif y2_shorten<y1_shorten:
        if x2_shorten<=x1_shorten:
            angle_shorten = math.pi+angle_shorten
        elif x2_shorten>x1_shorten:
            angle_shorten = 2*math.pi-angle_shorten

    new_x2_shorten = x1_shorten + (length_shorten-len_shorten)*math.cos(angle_shorten)
    new_y2_shorten = y1_shorten + (length_shorten-len_shorten)*math.sin(angle_shorten)

    return new_x2_shorten, new_y2_shorten

## Function to check intersection of two lines
# Line1 [x1,y1] -> [x2,y2]
# Line2 [x3,y3] -> [x4,y4]
def intersectionCheck(x1, y1, x2, y2, x3, y3, x4, y4):
    score_a = (x3 - x4) * (y1 - y3) + (y3 - y4) * (x3 - x1)
    score_b = (x3 - x4) * (y2 - y3) + (y3 - y4) * (x3 - x2)
    score_c = (x1 - x2) * (y3 - y1) + (y1 - y2) * (x1 - x3)
    score_d = (x1 - x2) * (y4 - y1) + (y1 - y2) * (x1 - x4)
    flg_check = False
    if score_a*score_b<=0 and score_c*score_d<=0:
        flg_check = True
        if (x1==x3 and y1==y3) or (x1==x4 and y1==y4) or (x2==x3 and y2==y3) or (x2==x4 and y2==y4):
            flg_check = False

    return flg_check


## Function to choose the optimal resting position within the resting point library
#
def takeRest(line_rest, prev_pos_rest, next_pos_rest, prev_prev_pos_rest, lib_rest, flg_first_rest):
    new_line_rest = ''

    candidate_rest1 = []
    candidate_rest2 = []
    #count = 0

    for position_rest in lib_rest:
        x1 = position_rest[0]
        y1 = position_rest[1]
        #x2, y2 = shortenLine(x1, y1, prev_pos_rest[0], prev_pos_rest[1],1.5)
        x2 = prev_pos_rest[0]
        y2 = prev_pos_rest[1]
        flg_rest = False
        count_rest = 0

        for position_line in line_library:
            x3 = position_line[0]
            y3 = position_line[1]
            x4 = position_line[2]
            y4 = position_line[3]

            intersect = intersectionCheck(x1,y1,x2,y2,x3,y3,x4,y4)

            if not intersect:
                count_rest += 1
                if count_rest == len(line_library):
                    flg_rest = True
            else:
                break

        if flg_rest:
            length_candidate = math.sqrt((prev_pos_rest[0]-x1)**2+(prev_pos_rest[1]-y1)**2)
            length_line = math.sqrt((prev_prev_pos_rest[0]-prev_pos_rest[0])**2+(prev_prev_pos_rest[1]-prev_pos_rest[1])**2)
            angle_candidate = math.acos(min(length_candidate,length_line)/max(length_candidate,length_line))
            position_rest.append(angle_candidate)
            candidate_rest1.append(position_rest)

    for position_rest in lib_rest:
        x1 = position_rest[0]
        y1 = position_rest[1]
        #x2, y2 = shortenLine(x1, y1, prev_pos_rest[0], prev_pos_rest[1],1.5)
        x2 = prev_pos_rest[0]
        y2 = prev_pos_rest[1]
        flg_rest = False
        count_rest = 0

        for position_line in line_library:
            x3 = position_line[0]
            y3 = position_line[1]
            x4 = position_line[2]
            y4 = position_line[3]

            intersect = intersectionCheck(x1,y1,x2,y2,x3,y3,x4,y4)

            if not intersect:
                count_rest += 1
                if count_rest == len(line_library):
                    flg_rest = True
            else:
                break

        if flg_rest:
            length_candidate = math.sqrt((prev_pos_rest[0]-x1)**2+(prev_pos_rest[1]-y1)**2)
            length_line = math.sqrt((prev_pos_rest[0]-next_pos_rest[0])**2+(prev_pos_rest[1]-next_pos_rest[1])**2)
            angle_candidate = math.acos(min(length_candidate,length_line)/max(length_candidate,length_line))
            position_rest.append(angle_candidate)
            candidate_rest2.append(position_rest)

    final_rest1 = [0,0,0]
    final_rest2 = [0,0,math.pi]
    for cand_rest2 in candidate_rest2:
        if math.pi-cand_rest2[2] < final_rest2[2]:
            final_rest2 = cand_rest2
    for cand_rest1 in candidate_rest1:
        if math.pi-cand_rest1[2] > final_rest1[2]:
            final_rest1 = cand_rest1


    if final_rest2 == [0,0,math.pi]:
        print('error: increase the number of resting point library')
        print(prev_pos_rest)
        print(next_pos_rest)
        print('~~~~~~~')

    #new_prev_x_rest, new_prev_y_rest = shortenLine(next_pos_rest[0], next_pos_rest[1], prev_pos_rest[0], prev_pos_rest[1], 1)
    #if flg_first_rest:
    new_prev_x_rest = prev_pos_rest[0]
    new_prev_y_rest = prev_pos_rest[1]

    new_line_rest += 'G1 X' + str(final_rest1[0]) + ' Y' + str(final_rest1[1]) + ' ;resting point1\n' + \
                     'M107\nG0 Z30 F4000\n' + \
                     'G0 X' + str(final_rest2[0]) + ' Y' + str(final_rest2[1]) + ' ;resting point2\n' \
                     'G4 S10\n' + 'G0 Z' + str(z_height_manual) + '\n' + \
                     'M106\n' + \
                     'G1 X' + str(new_prev_x_rest) + ' Y' + str(new_prev_y_rest) + ' F' + str(PRINT_SPEED) + '\n' +\
                     line_rest

    return new_line_rest


## Function to chop up a wax line into wax droplets
def chopLine(previous, next, length_remain, count_chopline):
    line = ''
    if length_remain==0:
        line += 'M106\n' + 'G4 P' + str(switching_time) + '\nM107\n'

    distance = round(((next[0]-previous[0])**2+(next[1]-previous[1])**2)**0.5, 3)
    num_drops = int((distance+length_remain)//drop_interval)
    drop_x = previous[0]
    drop_y = previous[1]
    x_interval = round((next[0]-previous[0])*drop_interval/distance, 3)
    y_interval = round((next[1]-previous[1])*drop_interval/distance, 3)
    extruder_up_interval = 40/drop_interval
    if drop_interval <= 1:
        extruder_up_interval = 40

    for i in range(num_drops):
        drop_x += x_interval
        drop_y += y_interval
        line += 'G1 X' + str(drop_x) + ' Y' + str(drop_y) + ' F' + str(PRINT_SPEED) + '\n' #move to the next position
        line += 'M106\n' + 'G4 P' +str(switching_time) + '\nM107\n' #print a drop
        count_chopline += 1
        if count_chopline >= extruder_up_interval:
            line += 'G0 Z50 F1000\n' + 'G4 S10\n' + 'G0 Z' + str(z_height_manual) + '\nG1 F' + str(
                PRINT_SPEED) + '\n'
            count_chopline = 0

    new_remain = round(((next[0]-drop_x)**2+(next[1]-drop_y)**2)**0.5, 3)

    return line, new_remain, count_chopline

## Function to build a library of lines written in input .gcode file
def buildLibrary(orig):
    abs_flg_lib = 0
    next_lib = [0,0,0]
    prev_lib = [0,0,0]
    library_lib = []

    for line_lib in orig:
        if abs_flg_lib < 2:
            if re.search('G1', line_lib):
                if not (re.search('X', line_lib) or re.search('Y', line_lib) or re.search('Z', line_lib)):
                    a = 1

                elif re.search('intro line', line_lib):
                    a = 1

                elif re.search('go outside', line_lib):
                    a = 1

                elif re.search('E-?[0-9.]+', line_lib):  # Extrude move
                    next_lib = updatePosition(line_lib, prev_lib)
                    library_lib.append([prev_lib[0], prev_lib[1], next_lib[0], next_lib[1]])

                    prev_lib = next_lib  # update position

                else:  # No extrude; G0
                    next_lib = updatePosition(line_lib, next_lib)  # update position
                    prev_lib = next_lib

            if re.search('BEFORE_LAYER_CHANGE', line_lib):
                abs_flg_lib += 1

        elif abs_flg_lib == 2:
            break

    return library_lib

### Function to build a library of resting points
def buildRest(num_rest):
    center_rest = [125,100] #Center of the resting circle
    size_rest = 55 #radius of the resting circle
    rest_list = []

    for angle_rest in range(0,num_rest):
        new_x_rest = center_rest[0] + size_rest*math.cos(2*angle_rest*math.pi/num_rest)
        new_y_rest = center_rest[1] + size_rest*math.sin(2*angle_rest*math.pi/num_rest)
        rest_list.append([new_x_rest, new_y_rest])

    return rest_list


##################################################################
# Main Lines
##################################################################


##### Choose input and output files
print("\n\nChoose the original G-code file")
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
orig_gcode = askopenfilename(initialdir=os.getcwd(), title="Select file") # show an "Open" dialog box and return the path to the selected file
print(orig_gcode)
Munged = asksaveasfile(mode='w', defaultextension=".gcode")

##### Build a library of printed lines within input .gcode
with open(orig_gcode, 'r') as code_library:
    line_library = buildLibrary(code_library)

##### Build a library for resting position
rest_library = buildRest(24)

##### Process each line
with open(orig_gcode, 'r') as original_gcode:
    for line in original_gcode:

        ### Remove the carriage return that ends each line (for editing ease)
        line = line.replace('\n', '')

        if absolute_flg < 2:## Extracting printing commands for the first layer(0 is before 1st layer, 1 is end of 1st layer)

            ### Set maximum accelerations
            if re.search('M201', line):
                line = 'M201 X' + str(MAX_ACCELERATION_X) + \
                       ' Y' + str(MAX_ACCELERATION_Y) + \
                       ' Z' + str(MAX_ACCELERATION_Z) + \
                       ' E' + str(MAX_ACCELERATION_E) + ' ; sets maximum accelerations, mm/sec^2'

            ### Set maximum feedrates
            elif re.search('M203', line):
                line = 'M203 X' + str(MAX_FEEDRATE_X) + \
                       ' Y' + str(MAX_FEEDRATE_Y) + \
                       ' Z' + str(MAX_FEEDRATE_Z) + \
                       ' E' + str(MAX_FEEDRATE_Z) + ' ; sets maximum feedrates, mm/sec'

            ### Set actual acceleration
            elif re.search('M204 P', line):
                line = 'M204 P' + str(PRINT_ACCELERATION) + \
                       ' R' + str(RETRACT_ACCELERATION) + \
                       ' T' + str(TRAVEL_ACCELERATION) + \
                       ' ; sets acceleration (P, T) and retract acceleration (R), mm/sec^2'

            ### Set firmware version
            elif re.search('M115', line):
                line = 'M115 U' + FIRMWARE_VERSION + ' ; tell printer latest fw version'

            ### Set extruder temperature to WAX_TEMP
            elif re.search('M104 S', line):
                line = 'M1001 S1 ; wax mode\n'
                line += 'M104 S' + str(WAX_TEMP) + ' ; set extruder temp'
            elif re.search('M109 S', line):
                line = 'M109 S' + str(WAX_TEMP) + ' ; wait for extruder temp'
                line += '\nG4 S' + str(WAX_WAIT_TIME) + ' ; wait for wax melting'
                line += '\nM302 S' + str(COLD_EXTRUDE_TEMP) + '; allow cold extrusion'

            ### Set printer bed temperature to BED_TEMP
            elif re.search('M140 S', line):
                line = 'M140 S' + str(BED_TEMP) + ' ; set bed temp'
            elif re.search('M190 S', line):
                line = 'M190 S' + str(BED_TEMP) + ' ; wait for bed temp'

            ### Partly ignore Z calibration
            elif re.search('G80', line) and not(re.search(';G80', line)):
                line = ';' + line

            ### Set XYZ motion & extrusion
            elif re.search('G1', line):

                ## Delete unnecessary commands
                if not(re.search('X', line) or re.search('Y', line) or re.search('Z', line)):
                    line = 'delete_flg'
                elif(re.search('intro line', line)):
                    line = 'delete_flg'
                elif(re.search('go outside', line)):
                    line = 'delete_flg'

                ## Extrusion
                elif re.search('E-?[0-9.]+', line): #Extrude move
                    value_only = float((re.search('E-?[0-9.]+', line)).group(0)[1:]) #Extract E parameter value

                    # Get rid of original extrusion command
                    line = re.sub('E-?[0-9.]+', '', line)

                    # Get rid of original speed command
                    if re.search('F[0-9.]+', line):
                        line = re.sub('F[0-9.]+', '', line)

                    # Update position and moving angle
                    next_position = updatePosition(line, prev_position)
                    next_angle = updateAngle(prev_prev_position, prev_position, next_position)

                    # No Extrusion
                    if value_only <= 0:
                        line = re.sub('G1', 'G0', line) # Rapid Move
                        line += "F" + str(TRAVEL_SPEED) # Set Speed

                    # Extrusion
                    else:
                        if not re.search('intro line',line):
                            if extrusion_method == 'continuous':
                                line += 'F' + str(PRINT_SPEED) + '\n'
                            elif extrusion_method == 'dropwise':
                                line, length_remain, count_dots = chopLine(prev_position, next_position, length_remain, count_dots)

                    # Add Resting point when moving angle is too big
                    if extrusion_method == 'continuous':
                        if next_angle > angle_limit and prev_angle < 180:
                            next_length = math.sqrt((next_position[0]-prev_position[0])**2+(next_position[1]-prev_position[1])**2)
                            line = takeRest(line, prev_position, next_position, prev_prev_position, rest_library, False)
                        if first_line_flg == 0:
                            first_line_flg += 1
                            line = takeRest(line, prev_position, next_position, prev_prev_position,rest_library, True)

                    # Record position and angle
                    prev_prev_position = prev_position
                    prev_position = next_position  # update position
                    prev_angle = next_angle

                ## No Extrusion
                else:
                    # Replace original movement commands
                    line = re.sub('G1', 'G0', line)
                    if re.search('F[0-9.]+', line):
                        line = re.sub('F[0-9.]+', '', line)
                    line += ' F' + str(TRAVEL_SPEED)

                    # Replace original Z height commands
                    if re.search('Z-?[0-9.]+', line):
                        z_value = float((re.search('Z-?[0-9.]+', line)).group(0)[1:])
                        z_value = z_height_manual
                        line = re.sub('Z-?[0-9.]+', 'Z'+str(z_value), line)

                    # Update positions
                    next_position = updatePosition(line, next_position)
                    prev_position = next_position

            ### Delete unnecessary lines and add back the carriage return
            if line == 'delete_flg':
                line = ''
            else:
                line += '\n'

            ### Delete everything after first layer
            if re.search('BEFORE_LAYER_CHANGE', line):
                if absolute_flg == 1:
                    line += 'M107\n'
                absolute_flg += 1

        ### Remove all lines after first layer
        elif absolute_flg == 2:
            line = ''

        Munged.write(line)

### Add commands for printer to finish printing
Munged.write(last_lines)