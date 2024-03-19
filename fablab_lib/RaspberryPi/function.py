"""
    This file contains functions for Raspberry Pi.
    
Compatible: Raspberry Pi 3B, 3B+, 4B
Language: Python 3.7.3
IDE: Thonny 3.2.7
OS: Raspbian 10 (buster)
"""

import os
import sys

def restart_program():
    """
    Restarts the current program.
    -----------------------------
    
    Note: this function does not return. Any cleanup action (like saving data) must 
    be done before calling this function.
    """
    python = sys.executable
    os.execl(python,python, *sys.argv)


def restart_raspberry():
    """
    'Restarts the Raspberry Pi.'
    ----------------------------

    Note: this function does not return. Any cleanup action (like saving data) must
    be done before calling this function.
    """
    os.system('sudo reboot')