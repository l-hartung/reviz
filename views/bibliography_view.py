import os
from utils.latex import build_all


def run_bib(tex, bib):
    """
    generates the code for the references of a citation graph and runs latex to produce the output
    :param tex: path to bibtex-file
    """
    with open(os.path.join(tex, 'bibl.tex'), 'w') as file:
        file.write("\\documentclass[a4paper]{article}\n")
        file.write("\\usepackage[style=alphabetic, backend=biber]{biblatex}\n")
        file.write("\\usepackage[margin=1cm]{geometry}\n")
        if bib is not None and bib != "":
            file.write("\\addbibresource{" + bib + "}\n")
        else:
            file.write("\\addbibresource{literature.bib}\n")
        file.write("\\begin{document}\n")
        file.write("\\nocite{*}\n")
        file.write("\\printbibliography\n")
        file.write("\\end{document}\n")
    build_all('bibl', tex)
