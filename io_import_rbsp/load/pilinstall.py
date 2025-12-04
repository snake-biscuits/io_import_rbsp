import subprocess
import sys
import os

def install_pillow():

    cmd = [sys.executable, "-m", "pip", "install", "pillow"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print("pillow installed :3") #placeholder bullshit, pls disregard
        return True
    else:
        print(result.stderr)
        print("\n", "Whoops! You have to put the CD in your computer.") #placeholder bullshit, pls disregard
        return False
