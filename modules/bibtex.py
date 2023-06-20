import bibtexparser
import random
from .mytimer import measureStart, measureEnd
from .config import bibKeyDoi, bibKeyEprint, bibKeyPrefix, bibKeyID, bibKeyTitle, bibKeyType, bibKeyUrl, bibKeyPrefix, bibRefPrefix


def setReferenceKey(entry, entries, references):
    for i in range(len(references) + 1):
        x = bibKeyPrefix + str(i)
        if x not in references:
            entry[x] = x
            references[x] = entries.index(entry)


def load_bib_helper(bib):
    with open(bib) as bibtex_file:
        parser = bibtexparser.bparser.BibTexParser()
        parser.customization = bibtexparser.customization.convert_to_unicode
        bib_database = bibtexparser.load(bibtex_file, parser=parser)
    for e in bib_database.entries:
        if bibKeyDoi in e:
            u = e[bibKeyDoi]
            if u.startswith(".org/"):
                u = u[5:]
            if u.startswith("/"):
                u = u[1:]
            e[bibKeyDoi] = u
        if bibKeyEprint in e:
            u = e[bibKeyEprint]
            if u.startswith("arXiv:"):
                u = u[6:]
            e[bibKeyEprint] = u
    print("loaded", bib, flush=True)
    return bib_database


def findABibKeyPrefix(e):
    for k in e.keys():
        if k.startswith(bibKeyPrefix):
            return k
    return None


def load_bib(bib):
    measure = measureStart()
    bib_database = load_bib_helper(bib)
    references = {}
    entries = []
    for e in bib_database.entries:
        for k in e.keys():
            if k.startswith(bibKeyPrefix):
                references[k] = len(entries)
        entries.append(e)
    for e in entries:
        if findABibKeyPrefix(e) is None:
            setReferenceKey(e, entries, references)
    print("preprocessed", bib, flush=True)
    random.shuffle(entries)
    measureEnd(measure)
    return entries, references


def generate_bib(filename, entries):
    measure = measureStart()
    with open(filename, "w") as f:
        sentries = sorted(entries, key=lambda x: x[bibKeyID])
        keyctr = 0
        keymap = {}
        for e in sentries:
            if len(e) > 0:
                if (bibKeyTitle in e and e[bibKeyTitle] != "") or (bibKeyDoi in e and e[bibKeyDoi] != "") or (bibKeyEprint in e and e[bibKeyEprint] != "") or (bibKeyUrl in e and e[bibKeyUrl] != ""):
                    keyctr = keyctr + 1
                    for k in e:
                        if k.startswith(bibKeyPrefix):
                            keymap[int(k[len(bibKeyPrefix):])] = keyctr
        for e in sentries:
            if len(e) > 0:
                if (bibKeyTitle in e and e[bibKeyTitle] != "") or (bibKeyDoi in e and e[bibKeyDoi] != "") or (bibKeyEprint in e and e[bibKeyEprint] != "") or (bibKeyUrl in e and e[bibKeyUrl] != ""):
                    f.write("@" + e[bibKeyType] + "{" + e[bibKeyID] + ",\n")
                    e1 = {}
                    mykey = None
                    for k in sorted(e):
                        v = e[k]
                        if k.startswith(bibKeyPrefix):
                            kk = int(k[len(bibKeyPrefix):])
                            if kk in keymap:
                                mykey = bibKeyPrefix + str(keymap[kk])
                                e1[bibKeyPrefix + str(keymap[kk])] = bibKeyPrefix + str(keymap[kk])
                        elif k.startswith(bibRefPrefix):
                            kk = int(k[len(bibRefPrefix):])
                            if kk in keymap:
                                e1[bibRefPrefix + str(keymap[kk])] = bibRefPrefix + str(keymap[kk])
                        else:
                            e1[k] = v
                    mykey = bibRefPrefix + mykey[len(bibKeyPrefix):]
                    for k in sorted(e1):
                        if k != mykey:
                            v = e1[k]
                            if k != bibKeyType and k != bibKeyID and len(v) > 0:
                                f.write(("  " + k + " = " + "{" + v + "},\n").replace("%", "\\%"))
                    f.write("}\n")
    print("written", filename, flush=True)
    measureEnd(measure)
