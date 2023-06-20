from fuzzywuzzy import fuzz, process
from .config import saveAfterElements, isInteractive, bibKeyAuthor, bibKeyType, bibKeyID, bibKeyTitle, bibKeyDoi, bibKeyEprint, bibKeyUrl, maxManualQueueLen
from .bibtex import generate_bib
import re
from termcolor import colored


def isMatchingAuthor(a, b):
    if a == b:
        return True
    minlen = 4
    while minlen > 0:
        a1 = sorted(set([s for s in re.split('[^a-zA-Z]', a) if len(s) > minlen]))
        b1 = sorted(set([s for s in re.split('[^a-zA-Z]', b) if len(s) > minlen]))
        ctra = 0
        for x in a1:
            if x in b1:
                ctra = ctra + 1
        ctrb = 0
        for x in b1:
            if x in a1:
                ctrb = ctrb + 1
        if len(a1) < 1 or len(b1) < 1:
            return False
        if ctra / len(a1) > 0.2 or ctrb / len(b1) > 0.2:
            return True
        minlen = minlen - 1
    return False


def isMatchingEntry(e, e2, manual_interaction, entries, queue, queueI, bibfile):
    if manual_interaction and not isInteractive:
        return 0
    if bibKeyAuthor not in e:
        e[bibKeyAuthor] = ""
    if bibKeyTitle not in e:
        e[bibKeyTitle] = ""
    if bibKeyAuthor not in e2:
        e2[bibKeyAuthor] = ""
    if bibKeyTitle not in e2:
        e2[bibKeyTitle] = ""
    if e[bibKeyTitle] == "" or e2[bibKeyTitle] == "":
        return 0
    if bibKeyDoi in e and bibKeyDoi in e2:
        if e[bibKeyDoi] == e2[bibKeyDoi]:
            return 1
        else:
            return 0
    if bibKeyEprint in e and bibKeyEprint in e2:
        if e[bibKeyEprint] == e2[bibKeyEprint]:
            return 1
        else:
            return 0
    if bibKeyUrl in e and bibKeyUrl in e2:
        if e[bibKeyUrl] == e2[bibKeyUrl]:
            return 1
        else:
            return 0
    if bibKeyTitle in e and bibKeyTitle in e2:
        v = fuzz.ratio(e[bibKeyTitle].upper(), e2[bibKeyTitle].upper())
        v2 = fuzz.partial_ratio(e[bibKeyTitle].upper(), e2[bibKeyTitle].upper())
        if v > 90 or (v2 > 95 and v > 70):
            if bibKeyAuthor in e and bibKeyAuthor in e2:
                if isMatchingAuthor(e[bibKeyAuthor], e2[bibKeyAuthor]):
                    return 1
            if manual_interaction:
                print("", flush=True)
                print(colored("Article(1): Title= ", "green"), colored(e2[bibKeyTitle], "red"), colored(" Authors = ", "green"), colored(e2[bibKeyAuthor], "red"))
                print(colored("Reference(2): Title= ", "green"), colored(e[bibKeyTitle], "red"), colored(" Authors = ", "green"), colored(e[bibKeyAuthor], "red"))
                print("", flush=True)
                i = "x"
                while True:
                    i = input('Do both entries belong to the same article? (Please enter \'y\' or \'n\' or \'1\' or \'2\') ')
                    if i == "y" or i == "1":
                        return 1
                    if i == "2":
                        return 2
                    if i == "n":
                        break
            else:
                if queue is not None and queueI is not None:
                    queue.append(queueI)
                    print("queue for manual", len(queue), maxManualQueueLen)
                    if len(queue) >= maxManualQueueLen:
                        work_on_queue(queue, entries, bibfile)
    return 0


def merge_entries(e, e2, m):
    #e2 into e
    if m == 2:
        if bibKeyTitle in e:
            e2[bibKeyTitle] = e[bibKeyTitle]
    if m > 0:
        if bibKeyAuthor in e and bibKeyAuthor in e2:
            if e[bibKeyType] != "misc":
                e2[bibKeyType] = e[bibKeyType]
            for k, v in e2.items():
                if k not in e or len(e[k]) < len(v):
                    if k != bibKeyID:
                        e[k] = v
            e2.clear()
            e2[bibKeyID] = ""


def work_on_queue(queue, entries, bibfile):
    idx = 0
    for ei, ei2 in queue:
        idx = idx + 1
        e = entries[ei]
        e2 = entries[ei2]
        if len(e) > 0 and len(e2) > 0:
            print("manual confirm", idx - 1, len(queue))
            m = isMatchingEntry(e, e2, False, entries, None, None, bibfile)
            if m == 0:
                m = isMatchingEntry(e, e2, True, entries, None, None, bibfile)
            merge_entries(e, e2, m)
    generate_bib(bibfile, entries)
    queue.clear()


def merge_existing_citations(entries, bibfile):
    ctr = 0
    queue = None
    if isInteractive:
        queue = []
    for ei in range(len(entries)):
        print("check", ei, len(entries), flush=True)
        if ctr > saveAfterElements:
            ctr = 0
            generate_bib(bibfile, entries)
        e = entries[ei]
        if len(e) > 0:
            for ei2 in range(len(entries) - ei - 1):
                e2 = entries[ei + ei2 + 1]
                if len(e2) > 0:
                    m = isMatchingEntry(e, e2, False, entries, queue, (ei, ei + ei2 + 1), bibfile)
                    merge_entries(e, e2, m)
                    if m > 0:
                        ctr = ctr + 1
    generate_bib(bibfile, entries)
    work_on_queue(queue, entries, bibfile)

    print("merged existing citations", flush=True)
