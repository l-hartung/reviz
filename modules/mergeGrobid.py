import os
from .config import bibRefPrefix, bibKeyPrefix, bibKeyID, bibKeyCheckedTei, bibKeyFile
from .mergeExisting import isMatchingEntry, merge_entries
from .bibtex import load_bib_helper, findABibKeyPrefix, generate_bib, setReferenceKey
from os.path import isdir, isfile, abspath
from git import Repo

grobidBaseURL = "https://github.com/kermitt2/grobid.git"
grobidBaseFolder = "/libGrobid"
grobidJar = grobidBaseFolder + "/grobid-core/build/libs/grobid-core-0.8.0-SNAPSHOT.jar"

grobidBibtexURL = "https://github.com/kermitt2/grobid-example.git"
grobidBibtexFolder = "/libGrobid-bibtex"


def installGrobid():
    if not isdir(grobidBaseFolder):
        Repo.clone_from(grobidBaseURL, grobidBaseFolder)
    if not isdir(grobidBibtexFolder):
        Repo.clone_from(grobidBibtexURL, grobidBibtexFolder)
    wdir = os.getcwd()
    if not isfile(grobidJar):
        os.chdir(grobidBaseFolder)
        os.system("./gradlew install")
    if not isfile(grobidBibtexFolder + "/lib/grobid-core-0.8.0-SNAPSHOT.jar"):
        os.chdir(wdir)
        os.system("cp " + grobidJar + " " + grobidBibtexFolder + "/lib/")
    with open(grobidBibtexFolder + "/grobid-example.properties", "w") as f:
        f.write("grobid_example.pGrobidHome=../" + grobidBaseFolder + "/grobid-home")
    if not isfile(grobidBibtexFolder + "/target/org.grobidExample-0.7.3.jar"):
        os.chdir(grobidBibtexFolder)
        os.system("mvn install")
    os.chdir(wdir)


def runGrobid(pdffolder, teifolder):
    wdir = os.getcwd()
    if not isdir(teifolder):
        os.mkdir(teifolder)
    os.chdir(grobidBibtexFolder)
    os.system("mvn exec:exec -Pprocess_citation_bibtex -Dpdf=" + pdffolder + " -Dbib=" + teifolder)  #+ " -Dconsolidation=2")
    os.chdir(wdir)


def find_teibib(entries, references, bibfile, pdffolder, teifolder):
    installGrobid()
    runGrobid(abspath(pdffolder), abspath(teifolder))
    for e in entries:
        if bibKeyFile in e and bibKeyCheckedTei not in e:
            f = e[bibKeyFile]
            if f.startswith(":"):
                f = f[1:]
            if f.endswith(":PDF"):
                f = f[0:-4]
            if f.endswith(".pdf"):
                if isfile(f):
                    f = teifolder + "/" + f[0:-4] + ".bib"
                    if isfile(f):
                        bib_database = load_bib_helper(f)
                        for e3 in bib_database.entries:
                            found = None
                            for e2 in entries:
                                m = isMatchingEntry(e3, e2, False, entries, None, None, bibfile)
                                merge_entries(e2, e3, m)  # merge into e2 !!!!
                                if m > 0:
                                    found = e2
                                    break
                            if found is None:
                                entries.append(e3)
                                setReferenceKey(e3, entries, references)
                                e3[bibKeyID] = findABibKeyPrefix(e3)
                                found = e3
                            k = findABibKeyPrefix(found)
                            e[bibRefPrefix + k[len(bibKeyPrefix):]] = bibRefPrefix + k[len(bibKeyPrefix):]
                        e[bibKeyCheckedTei] = "True"
                        generate_bib(bibfile, entries)
                else:
                    del e[bibKeyFile]
