import os
from shutil import copy

# Some useful constants:
bar_to_gpa = 1E-4

def readfile(ifilename):
    """Reads a text file and outputs its contents as lines"""
    with open(ifilename, 'r') as file:
        lines = file.readlines()
    
    return(lines)

def writefile(ofilename, lines, align=24, justify=True):
    """Writes a file from lines"""
    with open(ofilename, 'w') as file:
        for line_index in range(len(lines)):
            splitted_line = lines[line_index].split()
            newline = ''
            for string in splitted_line:
                if justify:
                    newline += str(string).ljust(align)
                else:
                    newline += str(string) + ' '
            newline += '\n'
            file.write(newline)
    
    print(f'Saving {ofilename} ...')

    return

def readLineValue(input_line, position):
    """Outputs a value in a certain position within the input line"""
    splitted_line = input_line.split()

    return(splitted_line[position])

def updateLine(input_line, position, value, align=24):
    """Updates a value in a certain position within the input line"""
    splitted_line = input_line.split()
    splitted_line[position] = value
    newline = ''
    for string in splitted_line:
        newline += str(string).ljust(align)
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

            ofilenames.append(ofilename[:-4]) # remove extension .mdp
            writefile(ofilename, newlines)

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

            print(ofilename)

            ofilenames.append(ofilename[:-4]) # remove extension .mdp
            writefile(ofilename, newlines)

    return(ofilenames)

def prepDirs(ofilenames, gro='confin.gro', itps=['thf.itp', 'tip4p.itp'], top='topol.top'):
    """Creates the folders for the MD runs and copies all the input files there"""
    for dirname in ofilenames:
        os.mkdir(dirname)
        print(f'Creating folder {dirname}...')
        copy(gro, dirname)
        copy(top, dirname)
        copy((dirname + '.mdp'), dirname)
        for itp in itps:
            copy(itp, dirname)
        print(f'Copying the input files to the {dirname} folder...')


def genPBSscript(ofilenames, ifilename='gmx.bt', root_dir='/home/misha/nas_home/THF/', computenode='g7'):
    """Generates PBS script for running the MD simulations on mmkluster"""
    inputlines = readfile(ifilename)
    newlines = inputlines
    first_dirname = root_dir + ofilenames[0]
    for line_index in range(len(inputlines)):
        if 'nodes' in inputlines[line_index]:
            nodestring = f'nodes={computenode}:ppn=24'
            newlines[line_index] = updateLine(inputlines[line_index], 2, nodestring)
        if 'cd' in inputlines[line_index]:
            newlines[line_index] = updateLine(inputlines[line_index], 1, first_dirname)
        if 'grompp' in inputlines[line_index]:
            newlines[line_index] = updateLine(inputlines[line_index], 3, (ofilenames[0] + '.mdp'))

    for i in range(len(ofilenames[:-1])):
        dirname = root_dir + ofilenames[i]
        newlines.append('\n')
        newlines.append(f'cp confout.gro ../{ofilenames[i + 1]} \n')
        newlines.append(f'cp state.cpt ../{ofilenames[i + 1]} \n')
        newlines.append('\n')
        newlines.append(f'cd ../{ofilenames[i + 1]} \n')
        newlines.append(f'mv confout.gro confin.gro \n')
        # Production simulation have even index
        if (i % 2) == 0:
            newlines.append(f'gmx grompp -f {ofilenames[i + 1]}.mdp -c confin.gro -p topol.top -t state.cpt \n')
        else:
            newlines.append(f'gmx grompp -f {ofilenames[i + 1]}.mdp -c confin.gro -p topol.top \n')
        newlines.append('gmx mdrun -s topol.tpr \n')

    writefile('thf.bt', newlines, justify=False)

    return

# Generate the mdp files        
ofilenames_eq = genMDP('eqT130p1bar.mdp', pressures=list(range(1000, 21000, 1000)), temperatures=[], production_run=True)
ofilenames_prod = genMDP('eqT130p1bar.mdp', pressures=list(range(1000, 21000, 1000)), temperatures=[], production_run=False)

# Combine the mdp filenames and sort the list
ofilenames = ofilenames_eq + ofilenames_prod
ofilenames.sort()

# Generate the PBS script
genPBSscript(ofilenames, computenode='g7')
# Create folders and copy all the input files there
prepDirs(ofilenames)