#!/usr/bin/env python3
import gclib
from pprint import pprint
import spur
import numpy as np
from source_move_beta import *
from linear_move_beta import *
from rotary_move_beta import *


def main():

    print(' Hello! Welcome to the super ineractive GUI for the CAGE motor movement software! \n')
    print(' WARNING: Did you lift the motor assembly with the rack and pinion? \n \n')
    print(' DO NOT DO ANY MOTOR MOVEMENTS UNLESS ASSEMBLY IS LIFTED OFF THE DETECTOR \n \n')
    zero = input(' If you haven\'t zeroed the motors to their home positions, would you like to do that now? \n y/n -->')

    print('test')

    if zero == 'y':

        rotary_zero = input(' Zero the rotary motor? \n y/n -->')
        if rotary_zero == 'y':
            zero_rotary_motor()

        linear_zero = input(' Zero the linear motor? \n y/n -->')
        if linear_zero =='y':
            zero_linear_motor()

        source_zero = input(' Zero the source motor? \n y/n -->')
        if source_zero == 'y':
            zero_source_motor()

    print(' Alright, if you have already zeroed the motors, or didn\'t need to, now it is time to move motors.')

    source_check = input(' IMPORTANT: Did you just zero the source motor? \n y/n -->')
    if source_check == 'y':
        center_source_motor()

    # linear_program()
    # rotary_program()
    # source_program()

    # g.GClose()

if __name__=="__main__":
    main()
