import os
import subprocess


def build_all(filename, tex):
    """
    generates latex commands to build a graph-file
    :param filename: file name
    :param tex: destination folder for generated tex-files
    """
    #os.chdir(tex)

    full_name = os.path.join(tex, filename)

    call_clean = '/usr/bin/latexmk -c {}.tex'.format(full_name)
    call_make = '/usr/bin/latexmk -f -lualatex -outdir={} {}.tex'.format(tex, full_name)
    #call_make = 'latexmk -f -quiet -lualatex {}.tex'.format(full_name)

    subprocess.call(call_clean, shell=True)
    print("cleaned")
    make = subprocess.call(call_make, shell=True)
    print(make)

    os.chdir('..')
