import os
from utils.latex import build_all


def run_bib(tex):
    """
    generates the code for the references of a citation graph and runs latex to produce the output
    :param tex: path to bibtex-file
    """
    texCode = '''
    \\documentclass[a4paper]{article}
    \\usepackage[style=alphabetic, backend=biber]{biblatex}
    \\usepackage[margin=1cm]{geometry}

    \\addbibresource{library.bib}

    \\begin{document}
    
    \\nocite{*}
    
    \\printbibliography
    \\end{document}
    '''

    with open(os.path.join(tex, 'bibl.tex'), 'w') as file:
        citation_file = file.write(texCode)

    build_all('bibl', tex)