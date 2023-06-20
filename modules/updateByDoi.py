import bibtexparser
from doi2bib.crossref import get_bib_from_doi
from .config import saveAfterElements, bibKeyDoi, bibKeyCheckedDoi
from .mergeExisting import merge_entries
from .bibtex import generate_bib


def updateByDoi(entries, bibfile):
    ctr = 0
    c = 0
    for entry in entries:
        c = c + 1
        if ctr > saveAfterElements:
            ctr = 0
            generate_bib(bibfile, entries)
        if bibKeyDoi in entry and bibKeyCheckedDoi not in entry:
            print("checking doi", c - 1, len(entries))
            found, bibstr = get_bib_from_doi(entry[bibKeyDoi])
            entry[bibKeyCheckedDoi] = "False"
            if found:
                parser = bibtexparser.bparser.BibTexParser()
                parser.customization = bibtexparser.customization.convert_to_unicode
                etr = bibtexparser.loads(bibstr, parser=parser).entries
                if len(etr) > 0:
                    merge_entries(entry, etr[0], 1)
                    entry[bibKeyCheckedDoi] = "True"
                    ctr = ctr + 1
    print("updated by doi", flush=True)
