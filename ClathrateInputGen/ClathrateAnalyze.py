import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt

root_dir = os.getcwd()

def gmxEnergy(path, property, ofilename):
    """A function that enters a directory, runs gmx energy and collects the output
    
    Notable property codes for the THF-clathrate system:
    7 - Potential; 8 - Kinetic Energy; 9 - Total Energy;
    11 - Temperature; 13 - Pressure; 15 - Box-X;
    18 - Volume; 19 - Density;"""

    print(f'Moving to {path}...')
    os.chdir(path)
    command = f'echo {property} | gmx energy -o {ofilename}'
    process = subprocess.run(command, check=True, shell=True, 
                            capture_output=True, universal_newlines=True)
    output = process.stdout
    average = output.split()[-5]
    print(f'Saving average value of property {property}...')
    
    return(average)

def collectAverages(dirs_file, property, xvgfilename='pres.xvg', ofilename='averages.dat'):
    averages = []
    dir_list = []
    with open(dirs_file, 'r') as file:
        dirs = file.readlines()
    for dir in dirs:
        if 'prod' in dir and not '#' in dir:
            average = gmxEnergy((root_dir + "/" + dir[:-1]), property, f'{xvgfilename}')
            averages.append(average)
            dir_list.append(dir[:-1])

    return(averages, dir_list)

def saveAverages(averages, dir_list, ofilename='pressures.dat', header=f'# Source folder; Average \n'):
    os.chdir(root_dir)
    print(f'\nWriting averages to {ofilename}...')
    with open(ofilename, 'w') as file:
        file.write(header)
        for i in range(len(dir_list)):
            file.write(dir_list[i].ljust(24))
            file.write(averages[i].ljust(24))
            file.write('\n')

    return

def plotData(x, y, ofilename='p-rho.png', xlabel='Pressure, bar', ylabel='Density, $kg/m^3$', label='Density'):
    os.chdir(root_dir)
    X = (r for r in open(x) if not r[0] in ('@', '#'))
    Y = (r for r in open(y) if not r[0] in ('@', '#'))
    
    Xdata = np.genfromtxt(X)
    Ydata = np.genfromtxt(Y)

    fig, ax = plt.subplots()

    ax.plot(Xdata.T[1], Ydata.T[1], '.-r', lw=1, label=label)
    ax.set(xlabel=xlabel, ylabel=ylabel)
    ax.legend()
    ax.grid()
    plt.savefig(ofilename, dpi=300, format='png')

    return

# Save pressures
averages, dir_list = collectAverages('dirs.txt', 13, xvgfilename='pres.xvg')
saveAverages(averages, dir_list, ofilename='pressures.dat', header=f'# Source folder; Pressure (bar) \n')

# Save densities
averages, dir_list = collectAverages('dirs.txt', 19, xvgfilename='dens.xvg')
saveAverages(averages, dir_list, ofilename='densities.dat', header=f'# Source folder; Density (kg/m3) \n')

# Save p-rho plot
plotData(x='pressures.dat', y='densities.dat', ofilename='p-rho.png')




