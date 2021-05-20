import argparse
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
parser.add_argument("action", help="""
(1) bib2json: convert bib-file with included publications to required format, required if not using parsifal export
(2) grobid: gather citations from included papers using grobid
(3) graph-model: generate json model for the citation graph with nodes and edges
(4) draw: generate pdf of citation graph
(5) draw-summary: include optimalisations for the citation graph
(6) flow: generate flow diagram, only possible if using parsifal export
""", choices=["bib2json", "grobid", "flow", "graph-model", "draw", "draw-summary"])
parser.add_argument("json", help="path for json-file")

parser.add_argument("--bib-file", help="path for input bib-file, will be written to parameter 'json'", type=str, default=None)
parser.add_argument("--pdf", help="destination folder for pdf-files, default: ./pdf-files", default="./pdf-files")
parser.add_argument("--tei", help="destination folder for tei-files, default: ./tei-files", default="./tei-files")
parser.add_argument("--tex", help="destination folder for generated tex-files, default: ./tex-files", default="./tex-files")
parser.add_argument("--bibliography", dest='bib', help="generation of a pdf bibliography for the citation graph", action="store_true")
parser.add_argument("--deviation", help="maximum number of edge deviations allowed for node summarization, default=0", type=float, default=0)
parser.add_argument("--transitivities", help="reduce number of edges by considering transitivities", action="store_true")
parser.add_argument("--transitivities-bold", help="adapt line width of transitive edges", action="store_true")
parser.add_argument("--citation-counts", help="show number of direct and indirect citations for every node", action="store_true")
parser.add_argument("--authors-colored", help="threshold for showing publications with same authors using colors, use a value between 0 and 1", type=float, default=-1 )
parser.add_argument("--with-single-nodes", help="nodes without any edge are displayed in the graph", action="store_true")
parser.add_argument("--minimum-citations", help="only nodes with the given minimum number of citations are displayed", type=float, default=0)
parser.add_argument("--original-bibtex-keys", help="the original bibtex keys are used instead of md5 hashes", action="store_true")
parser.add_argument("--without-dummy-nodes", help="avoid dummy nodes for better placement of nodes for long edges", action="store_true")
parser.add_argument("--dont-show-edge-corrections", help="do not show the list of edge corrections", action="store_true")
parser.add_argument("--y-factor", help="factor for spacing between boxes", type=float, default=1)
parser.add_argument("--without-interactive-queries", help="with this option you are not asked for manual confirmation if our algorithm is not completely certain that a citation match was found", action="store_true")

args = parser.parse_args()

sys.setrecursionlimit(1000000000)
if args.action == "bib2json":
    if args.bib_file is None:
        raise argparse.ArgumentError("argument bib-file is missing")
    bib_to_json(args.json, args.bib_file)

if args.action == "grobid":
    if not os.path.exists(args.pdf):
        os.makedirs(args.pdf)
    if not os.path.exists(args.tei):
        os.makedirs(args.tei)
    run_grobid(args.json, args.pdf, args.tei)

if args.action == "graph-model":
    if not os.path.exists(args.tex):
        os.makedirs(args.tex)
    run_graph(args.json, args.tei, args.tex, args.original_bibtex_keys, args.without_interactive_queries)

if args.action == "flow":
    if not os.path.exists(args.tex):
        os.makedirs(args.tex)
    run_flow(args.json, args.tex)

if 'draw' in args.action:
    with open(os.path.join(args.tex, 'graph-model.json')) as f:
        graph = json.load(f)
    if args.action == "draw":
        view_sugiyama(graph, args.tex, args.with_single_nodes, args.without_dummy_nodes)
    if args.action == "draw-summary":
        view_sugiyama_summary(graph, args.tex, args.deviation, args.transitivities, args.transitivities_bold,
                              args.citation_counts, args.authors_colored, args.with_single_nodes, args.minimum_citations, args.without_dummy_nodes, args.dont_show_edge_corrections, args.y_factor)
    if args.bib:
        run_bib(args.tex)