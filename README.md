# q-dpico_picprogxxxx
Quick and dirty PIC16FXXXX programmer using the Raspberry Pi Pico and MicroPython 

Based on https://github.com/SyedTahmidMahbub/q-dpico_picprog72  

In-Circuit Serial Programming (ICSP) is not universal for all PIC microcontrollers, that is why I have made different versions of the same script for different models.

Other changes include the removal of the boost converter circuit to reduce the complexity and number of components. This component can be directly replaced by a 12V power supply or a boost converter module.

![boost_converter](https://github.com/user-attachments/assets/b3a208d8-e7d0-44fe-9e79-4b659b66c6bb)
![power_supply](https://github.com/user-attachments/assets/4d6f5a54-4c98-4978-84ab-121f7087d6db)
![boost_converter_usb](https://github.com/user-attachments/assets/e130b4fc-fdee-4607-884a-8e760e288f30)

To load the .hex code to the PIC microcontroller, you first need to verify that the .hex file does not contain comments or an invalid record type (see: https://en.wikipedia.org/wiki/Intel_HEX#Record_structure) (only types 0x00 (data) and 0x01 (EOF) are valid).  
It is recommended to use NotePad++ for this task.

prog72.py   -> PIC16F72 only  
prog84a.py  -> PIC16F84A only  
prog877.py  -> PIC16F877/A only (not working yet)  

![schematic](https://github.com/Kyuchumimo/q-dpico_picprogxxxx/blob/main/schematic.png)

![q-dpico_picprogxxxx](https://github.com/Kyuchumimo/q-dpico_picprogxxxx/assets/74131798/ff9cb71f-5634-42c1-88e2-7aae74238f0d)
