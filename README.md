# MIYAGI-Open-source-wax-printing-conversion-kit-

## Contents
  * [Hardware Instructions](#hardware-instructions)
    * [Machined Part](#machined-part)
    * [3D Printed Parts](#3d-printed-parts)
    * [Electronic Components](#electoric-components)
    * [Assembly](#assembly)
  * [Software Instructions](#software-instructions)
    * [Updating Prusa Firmware](#updating-prusa-firmware)
    * [Slicing and Munging](#slicing-and-munging)
    * [Modifying Firmware](#modifying-firmware)
  * [Demonstration](#demonstration)
    
## Hardware Instructions

### Machined Part

### 3D Printed Parts

### Electronic Conponents

### Assembly

## Software Instructions

### Updating Prusa Firmware
#### What you need:
  * .hex file for update
  * PrusaSlicer 2.0.0 (or Slic3r PE)

#### Steps:
General description about updating Prusa firmware provided by the Prusa Research can be found [here](https://help.prusa3d.com/article/r5ByKgVm69-firmware-upgrade-and-flashing).

1. Download our .hex file (prusa3d_fw_MK3S_3_7_2_Miyagi.hex) or generate your own .hex file
    - The type of Prusa 3D printer we used was MK3S, and the firmware version was 3.7.2. In case you have a different type of printer or wish to use a later firmware version, you need to generate your own .hex file. Follow detailed instructions under [firmawre modfication section](#modifying-firmware).
    
2. Connect your Prusa 3D printer to your computer.

3. Open the PrusaSlicer, click on the Configuration menu and select the .hex file in your local computer.

4. Flash!

### Slicing and Munging
#### What you need:
   * PrusaSlicer 2.0.0
   * Miyagi_munging_script.py
   * python 2.7 environment
   * .stl file to print
   
#### Steps:
1. Create a device to print and save it as .stl file, or download our Miyagi_sample.stl file.
     - Make sure the device you create can be drawn with only one stroke of line.

2. Open PrusaSlicer and upload the .stl file.

3. Change slicing settings as follows.
     - Go to _Print Settings -> Layers and perimeters_ and set _Perimeters_ to 1 and _Solid layers_ to 0 for both _Top_ and _Bottom_.
     - Go to _Print Settings -> Infill_ and set _Fill density_ to 0%.
     - Go to _Print Settings -> Skirt and brim_ and set _Loops_ to 0 and _Skirt height_ to 0.
     - Go to _Print Settings -> Support material_ and set _Raft layers_ to 0 layers.
     - Go to _Print Settings -> Advanced_ and set all the _Extrusion width_ to 1mm.
     - Go back to _Plater_, show the slicing window (bottom left), and make sure you have only one perimeter path.
     - Good to save the setting as a custom preset.
     
4. Click _Slice now_ and _Generate gcode_ and then save your sliced .gcode file.

5. Download _Miyagi_munging_script.py_ from this page.

6. Run _Miyagi_munging_script.py_.

7. Choose your sliced .gcode file and name a new .gcode file.

8. Generated .gcode file is ready to print wax. Transfer the .gcode file to the printer through SD card. 

### Modifying Firmware
_Note:_
This instruction is made for Linux OS, Prusa 3D printer MK3S. If you were using different printer model, different version of firmware, or different OS, this instruction may not be optimized. Original instruction provided by the Prusa Research can be found [here](https://github.com/prusa3d/Prusa-Firmware). 

1. Clone repository of the original firmware ([forked page](https://github.com/PenniGEM2019/Prusa-Firmware#2b)).
     - Make sure to clone a correct version of firmware.
     
2. In your local computer, under "Firmware/variants/" directory, select the configuration file .h corresponding to your printer model, make a copy of this file and rename it as "Configuration_prusa.h". Move this renamed file into "Firmware/" directory.

3. In the terminal window, go to the directory you cloned the repository. Run `sudo ./build.sh`.
     - You may need to run `sudo chmod +x build.sh` and `sudo chmod +x lang/*.sh` beforehand.
     
4. Output .hex file is at "PrusaFirmware/lang/firmware.hex" . In the same folder you can find hex files for other languages as well.

5. Using the .hex file, update printer firmware. Follow [the instruction](#updating-prusa-firmware) as you need.

## Demonstration
Demonstration of drawing a device and detailed characterization of our printer are on our [iGEM wiki page](https://2019.igem.org/Team:Penn/Results).
