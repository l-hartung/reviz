import os
import subprocess


def build_all(file, tex):
    """
    generates latex commands to build a graph-file
    :param file: file name
    :param tex: destination folder for generated tex-files
    """
    os.chdir(tex)

    call_clean = 'latexmk -c {}.tex'.format(file)
    call_make = 'latexmk -f -lualatex {}.tex'.format(file)
    #call_make = 'latexmk -f -quiet -lualatex {}.tex'.format(file)

    subprocess.run(call_clean)
    make = subprocess.run(call_make)
    print(make)

    os.chdir('..')
