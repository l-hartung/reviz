#!/usr/bin/env python3
from utils.latex import build_all, compile_latex
import argparse
from modules.bibtex import load_bib, generate_bib
from modules.config import maxManualQueueLen, isInteractive
from modules.extractGraph import extractGraph, extractGraphI
from modules.mergeExisting import merge_existing_citations
from modules.mergeGrobid import find_teibib
from modules.updateByArxiv import updateByArxiv
from modules.updateByDoi import updateByDoi

from grobid.grobid import run_grobid
from model.graph_model import run_graph
from views.flow_diagram_view import run_flow
from views.bibliography_view import run_bib
import os
import json
from views.graph_view import view_sugiyama, view_sugiyama_summary
from utils.utils import bib_to_json
import sys

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(required=True)
parserDraw = subparsers.add_parser("draw", help='draw: generate pdf of citation graph')
parserDraw.add_argument("--bib-out", help="generation of a pdf bibliography for the citation graph", action="store_true")
parserDraw.add_argument("--tex", help="destination folder for generated tex-files, default: ./tex-files", default="./tex-files")
parserDraw.add_argument("--with-single-nodes", help="nodes without any edge are displayed in the graph", action="store_true")
parserDraw.add_argument("--without-dummy-nodes", help="avoid dummy nodes for better placement of nodes for long edges", action="store_true")
parserDraw_Group = parserDraw.add_mutually_exclusive_group(required=True)
parserDraw_Group.add_argument("--json", help="path for json-model")
parserDraw_Group.add_argument("--bib", help="path for bib file to visualize")
parserDraw.set_defaults(action="draw")
parserDrawSummary = subparsers.add_parser("draw-summary", help='draw-summary: include optimalisations for the citation graph')
parserDrawSummary.add_argument("--authors-colored", help="threshold for showing publications with same authors using colors, use a value between 0 and 1", type=float, default=-1)
parserDrawSummary.add_argument("--bib-out", help="generation of a pdf bibliography for the citation graph", action="store_true")
parserDrawSummary_Group = parserDrawSummary.add_mutually_exclusive_group(required=True)
parserDrawSummary_Group.add_argument("--json", help="path for json-model")
parserDrawSummary_Group.add_argument("--bib", help="path for bib file to visualize")
parserDrawSummary.add_argument("--citation-counts", help="show number of direct and indirect citations for every node", action="store_true")
parserDrawSummary.add_argument("--deviation", help="maximum number of edge deviations allowed for node summarization, default=0", type=float, default=0)
parserDrawSummary.add_argument("--dont-show-edge-corrections", help="do not show the list of edge corrections", action="store_true")
parserDrawSummary.add_argument("--minimum-citations", help="only nodes with the given minimum number of citations are displayed", type=float, default=0)
parserDrawSummary.add_argument("--tex", help="destination folder for generated tex-files, default: ./tex-files", default="./tex-files")
parserDrawSummary.add_argument("--transitivities", help="reduce number of edges by considering transitivities", action="store_true")
parserDrawSummary.add_argument("--transitivities-bold", help="adapt line width of transitive edges", action="store_true")
parserDrawSummary.add_argument("--with-single-nodes", help="nodes without any edge are displayed in the graph", action="store_true")
parserDrawSummary.add_argument("--without-dummy-nodes", help="avoid dummy nodes for better placement of nodes for long edges", action="store_true")
parserDrawSummary.add_argument("--y-factor", help="factor for spacing between boxes", type=float, default=1)
parserDrawSummary.set_defaults(action="draw-summary")
parserFlow = subparsers.add_parser("flow", help='flow: generate flow diagram, only possible if using parsifal export')
parserFlow.add_argument("--tex", help="destination folder for generated tex-files, default: ./tex-files", default="./tex-files")
parserFlow.add_argument("json", help="path for json file to use as input")
parserFlow.set_defaults(action="flow")
parserGraphModel = subparsers.add_parser("graph-model", help='graph-model: generate json model for the citation graph with nodes and edges')
parserGraphModel.add_argument("--original-bibtex-keys", help="the original bibtex keys are used instead of md5 hashes", action="store_true")
parserGraphModel.add_argument("--tei", help="destination folder for tei-files, default: ./tei-files", default="./tei-files")
parserGraphModel.add_argument("--tex", help="destination folder for generated tex-files, default: ./tex-files", default="./tex-files")
parserGraphModel.add_argument("--without-interactive-queries", help="with this option you are not asked for manual confirmation if our algorithm is not completely certain that a citation match was found", action="store_true")
parserGraphModel.add_argument("json", help="path for json file to use as input")
parserGraphModel.set_defaults(action="graph-model")
parserGrobid = subparsers.add_parser("grobid", help="grobid: convert all pdf files to tei files and merge them into the bib file")
parserGrobid.add_argument("--bib", help="bib file to store the added citations", required=True)
parserGrobid.add_argument("--pdf", help="the folder with the pdf files to analyze", default=".")
parserGrobid.set_defaults(action="grobid")
parserGrobid.add_argument("--tei", help="destination folder for tei-files, default: ./tei-files", default="./tei-files")
parserImproveBib = subparsers.add_parser("improve-bib", help="improve-bib: download the bibtex based on doi and eprint, and attempt to merge duplicates")
parserImproveBib.set_defaults(action="improve-bib")
parserImproveBib.add_argument("--bib", help="file to improve", required=True)
parserImproveBib.add_argument("--without-interactive-queries", help="with this option you are not asked for manual confirmation if our algorithm is not completely certain that a citation match was found", action="store_true")
parserImproveBib.add_argument("--queue-len", help="how many uncertain confirmations should be collected, before they are asked at once", type=int, default=100)

parserDraw.add_argument("--filterByID", help="specifies a comma-separated list of bib IDs, which should be included in the result. Only works when using bib file")
parserDraw.add_argument("--filterAddCited", help="adds all the cited articles on top of the filtered bib IDs. Requires that --filterByID is set", action="store_true")
parserDraw.add_argument("--filterAddCiting", help="adds all the articles that cite the specified list on top of the filtered bib IDs. Requires that --filterByID is set", action="store_true")
parserDrawSummary.add_argument("--filterByID", help="specifies a comma-separated list of bib IDs, which should be included in the result. Only works when using bib file")
parserDrawSummary.add_argument("--filterAddCited", help="adds all the cited articles on top of the filtered bib IDs. Requires that --filterByID is set", action="store_true")
parserDrawSummary.add_argument("--filterAddCiting", help="adds all the articles that cite the specified list on top of the filtered bib IDs. Requires that --filterByID is set", action="store_true")

args = parser.parse_args()

sys.setrecursionlimit(1000000000)

if args.action == "grobid":
    entries, references = load_bib(args.bib)
    generate_bib(args.bib, entries)
    find_teibib(entries, references, args.bib, args.pdf, args.tei)
    generate_bib(args.bib, entries)
if args.action == "improve-bib":
    global maxManualQueueLen
    maxManualQueueLen = args.queue_len
    global isInteractive
    isInteractive = not args.without_interactive_queries
    entries, references = load_bib(args.bib)
    generate_bib(args.bib, entries)
    updateByDoi(entries, args.bib)
    updateByArxiv(entries, args.bib)
    merge_existing_citations(entries, args.bib)
    generate_bib(args.bib, entries)
if args.action == "draw-summary":
#    compile_latex('graph_summary', args.tex)
#    exit()
    if args.json is not None:
        entries=None
        with open(args.json) as f:
            graph = json.load(f)
    else:
        entries, references = load_bib(args.bib)
        filter = None
        filterMode = 0
        if args.filterByID is not None:
            filter = set(args.filterByID.split(","))
            if args.filterAddCited:
                filterMode = filterMode + 1
            if args.filterAddCiting:
                filterMode = filterMode + 2
        generate_bib(args.bib, entries)
        graph = extractGraphI(entries, filter, filterMode)
    view_sugiyama_summary(graph, args.tex, args.deviation, args.transitivities, args.transitivities_bold, args.citation_counts, args.authors_colored, args.with_single_nodes, args.minimum_citations, args.without_dummy_nodes, args.dont_show_edge_corrections, args.y_factor,args.bib,entries)
    if args.bib_out:
        run_bib(args.tex, args.bib)
if args.action == "draw":
    if args.json is not None:
        with open(args.json) as f:
            graph = json.load(f)
    else:
        entries, references = load_bib(args.bib)
        filter = None
        filterMode = 0
        if args.filterByID is not None:
            filter = set(args.filterByID.split(","))
            if args.filterAddCited:
                filterMode = filterMode + 1
            if args.filterAddCiting:
                filterMode = filterMode + 2
        generate_bib(args.bib, entries)
        graph = extractGraphI(entries, filter, filterMode)
    view_sugiyama(graph, args.tex, args.with_single_nodes, args.without_dummy_nodes,args.bib)
    if args.bib_out:
        run_bib(args.tex, args.bib)
if args.action == "graph-model":
    if not os.path.exists(args.tex):
        os.makedirs(args.tex)
    run_graph(args.json, args.tei, args.tex, args.original_bibtex_keys, args.without_interactive_queries)
if args.action == "flow":
    if not os.path.exists(args.tex):
        os.makedirs(args.tex)
    run_flow(args.json, args.tex)
