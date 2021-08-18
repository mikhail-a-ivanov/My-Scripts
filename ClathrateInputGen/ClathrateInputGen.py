import os
from shutil import copy

# Some useful constants:
bar_to_gpa = 1E-4

def readfile(ifilename):
    """Reads a text file and outputs its contents as lines"""
    with open(ifilename, 'r') as file:
        lines = file.readlines()
    
    return(lines)

def writeMDP(ofilename, lines):
    """Writes and mdp file"""
    with open(ofilename, 'w') as file:
        for line_index in range(len(lines)):
            splitted_line = lines[line_index].split()
            newline = ''
            for string in splitted_line:
                newline += "{:<24}".format(string)
            newline += '\n'
            file.write(newline)
    
    print(f'Saving {ofilename} ...')

    return

def readLineValue(input_line, position):
    """Outputs a value in a certain position within the input line"""
    splitted_line = input_line.split()

    return(splitted_line[position])

def updateLine(input_line, position, value):
    """Updates a value in a certain position within the input line"""
    splitted_line = input_line.split()
    splitted_line[position] = value
    newline = ''
    for string in splitted_line:
        newline += "{:<24}".format(string)
    newline += '\n'

    return(newline)

def genMDP(ifilename, pressures=[], temperatures=[], production_run=False):
    """Generates a sequence of mdp files with varying temperatures and pressures.
    Adjusts the barostat, continuation and velocity generation options according to 
    the production_run flag.
    
    Note: It is currently not possible to adjust T and p values simultaneously."""
    inputlines = readfile(ifilename)
    newlines = inputlines
    ofilenames = []

    for line_index in range(len(inputlines)):
         if 'berendsen' in inputlines[line_index] and production_run:
             newlines[line_index] = updateLine(inputlines[line_index], 2, 'parrinello-rahman')
         elif 'berendsen' in inputlines[line_index] and not production_run:
             continue
         elif 'continuation' in inputlines[line_index]:
             if production_run and readLineValue(inputlines[line_index], 2) == 'no':
                 newlines[line_index] = updateLine(inputlines[line_index], 2, 'yes')
         elif 'gen-vel' in inputlines[line_index]:
             if production_run and readLineValue(inputlines[line_index], 2) == 'yes':
                 newlines[line_index] = updateLine(inputlines[line_index], 2, 'no')

    if pressures != []:
        for pressure in pressures:
            for line_index in range(len(inputlines)):
                if 'ref-p' in inputlines[line_index]:
                    newlines[line_index] = updateLine(inputlines[line_index], 2, pressure)
                if 'ref-t' in inputlines[line_index]:
                    ref_T = readLineValue(inputlines[line_index], 2)
               

            if production_run:
                ofilename = f'{round((pressure * bar_to_gpa), 2)}GPa_{int(ref_T)}K_prod.mdp'
            else:
                ofilename = f'{round((pressure * bar_to_gpa), 2)}GPa_{int(ref_T)}K_eq.mdp'

            writeMDP(ofilename, newlines)

    elif temperatures != []:
        for temperature in temperatures:
            for line_index in range(len(inputlines)):
                if 'ref-t' in inputlines[line_index]:
                    newlines[line_index] = updateLine(inputlines[line_index], 2, temperature)
                if 'gen-temp' in inputlines[line_index]:
                    newlines[line_index] = updateLine(inputlines[line_index], 2, temperature)
                if 'ref-p' in inputlines[line_index]:
                    ref_p = readLineValue(inputlines[line_index], 2)
               

            if production_run:
                ofilename = f'{round((float(ref_p) * bar_to_gpa), 2)}GPa_{temperature}K_prod.mdp'
            else:
                ofilename = f'{round((float(ref_p) * bar_to_gpa), 2)}GPa_{temperature}K_eq.mdp'

            ofilenames.append(ofilename[:-4]) # remove extension .mdp
            writeMDP(ofilename, newlines)

    return(ofilenames)

def prepDirs(ofilenames, gro='confin.gro', itps=['thf.itp', 'tip4p.itp'], top='topol.top'):
    for dirname in ofilenames:
        os.mkdir(dirname)
        copy(gro, dirname)
        copy(top, dirname)
        copy((dirname + '.mdp'), dirname)
        for itp in itps:
            copy(itp, dirname)
        
        



ofilenames = genMDP('eqT130p1bar.mdp', pressures=[1000, 2000, 3000], temperatures=[], production_run=False)
prepDirs(ofilenames)