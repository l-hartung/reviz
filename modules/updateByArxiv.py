from .config import saveAfterElements, bibKeyEprint, bibKeyCheckedEprint
from arxivcheck.arxiv import check_arxiv_published
from .mergeExisting import merge_entries
from .bibtex import generate_bib
import bibtexparser


def updateByArxiv(entries, bibfile):
    ctr = 0
    c = 0
    for entry in entries:
        c = c + 1
        if ctr > saveAfterElements:
            ctr = 0
            generate_bib(bibfile, entries)
        if bibKeyEprint in entry and bibKeyCheckedEprint not in entry:
            print("checking eprint", c - 1, len(entries))
            try:
                found, _, bibstr = check_arxiv_published(entry[bibKeyEprint], field="id")
                entry[bibKeyCheckedEprint] = "False"
                if found:
                    parser = bibtexparser.bparser.BibTexParser()
                    parser.customization = bibtexparser.customization.convert_to_unicode
                    etr = bibtexparser.loads(bibstr, parser=parser).entries
                    if len(etr) > 0:
                        merge_entries(entry, etr[0], 1)
                        entry[bibKeyCheckedEprint] = "True"
                        ctr = ctr + 1
            except:
                pass
    print("updated by arxiv", flush=True)
