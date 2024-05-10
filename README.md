# q-dpico_picprogxxxx
Quick and dirty PIC16FXXXX programmer using the Raspberry Pi Pico and MicroPython 

Based on https://github.com/SyedTahmidMahbub/q-dpico_picprog72  

In-Circuit Serial Programming (ICSP) is not universal for all PIC microcontrollers, that is why I have made different versions of the same script for different models.

Other changes include the removal of the boost converter circuit to reduce the complexity and number of components. This component can be directly replaced by a 12V power supply or a boost converter module.

To load the .hex code to the PIC microcontroller, you first need to verify that the .hex file does not contain comments or an invalid record type (see: https://en.wikipedia.org/wiki/Intel_HEX#Record_structure) (only types 0x00 (data) and 0x01 (EOF) are valid).  
It is recommended to use NotePad++ for this task.

![schematic](https://github.com/Kyuchumimo/q-dpico_picprogxxxx/blob/main/schematic.png)
