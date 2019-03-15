# This script demonstrates how to generate a classification from a datacube
#
# Firstly, the datacube is defined and a working directory (output directory)
#
# The following scripts are called

# outputImagesFromDataCubeScript: A matlab script that generates quantised
# images that are put into outputDirectory

# extract_features: A python script that extracts bottle neck features using
# CNNs defined in the config file xml.  The features are stored in
# outputDirectory

# testHAB: A python script that uses the model defined in the xml file and
# generates a classification based on the datacube extracted images
# The classification probablity is printed to stdout.
#
# THE UNIVERSITY OF BRISTOL: HAB PROJECT
# Author Dr Paul Hill March 2019

import sys
import os
import extract_features
import testHAB
import pudb; pu.db


h5name = '/home/cosc/csprh/linux/HABCODE/scratch/HAB/tmpTest/testCubes/Cube_09073_09081_737173.h5'
outputDirectory = '/home/cosc/csprh/linux/HABCODE/scratch/HAB/tmpTest/CNNIms'

mstringApp = '/Applications/MATLAB_R2016a.app/bin/matlab'
mstringApp = 'matlab'

#h5name = '/Users/csprh/Dlaptop/MATLAB/MYCODE/HAB/WORK/HAB/florida2/Cube_09073_09081_737173.h5'
#outputDirectory = '/Users/csprh/Dlaptop/MATLAB/MYCODE/HAB/WORK/HAB/CNNIms'

mstring = mstringApp + ' -nosplash -r \"outputImagesFromDataCubeScript ' +  h5name + ' ' + outputDirectory + '\"'
os.system(mstring)
extract_features.main(['cnfgXMLs/NASNet11_lstm0.xml', outputDirectory])
testHAB.main(['cnfgXMLs/NASNet11_lstm0.xml', outputDirectory])



