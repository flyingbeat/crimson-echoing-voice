import json
from pathlib import Path
from typing import Any, Dict

from rdflib import RDFS, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

IMG = Namespace("https://files.ifi.uzh.ch/ddis/teaching/2025/ATAI/dataset/images/")
MV = Namespace("https://www.imdb.com/title/")
CAST = Namespace("https://www.imdb.com/name/")
SCHEMA = Namespace("http://schema.org/")


def to_resource(ns: Namespace, id_value: str) -> URIRef:
    safe = id_value.strip()
    return ns[safe]


def record_to_graph(rec: Dict[str, Any], predicates: dict) -> Graph:
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("img", IMG)
    g.bind("mv", MV)
    g.bind("cast", CAST)

    img_id = rec.get("img")
    if not img_id:
        return g

    img_res = to_resource(IMG, img_id)
    mv_res = None

    img_type = (rec.get("type") or "").strip()
    type_res = SCHEMA[img_type.capitalize()]  # ex:Poster
    if img_type not in predicates:
        g.add((type_res, RDFS.label, Literal(img_type, datatype=XSD.string)))
        predicates[img_type] = type_res

    movies = rec.get("movie")
    if movies is not None and len(movies) == 1:
        mv_res = to_resource(MV, movies[0])
        g.add((mv_res, type_res, img_res))
    elif len(movies) == 0:
        pass
    else:
        raise ValueError(f"Record must have exactly one movie. Found: {movies}")

    cast = rec.get("cast")
    if cast:
        cast_res = [to_resource(CAST, c) for c in cast]
        if mv_res is not None:
            for cr in cast_res:
                g.add((mv_res, SCHEMA.cast, cr))
        else:
            for cr in cast_res:
                g.add((cr, type_res, img_res))

    return g


def json_to_nt(json_path: str, output_nt_path: str) -> None:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        items = data.get("items") or data.get("images") or []
    elif isinstance(data, list):
        items = data
    else:
        items = []
    predicates = {}
    merged = Graph()
    merged.bind("schema", SCHEMA)
    merged.bind("img", IMG)
    merged.bind("mv", MV)
    merged.bind("cast", CAST)

    for rec in items:
        g = record_to_graph(rec, predicates)
        for triple in g:
            merged.add(triple)

    merged.serialize(destination=output_nt_path, format="nt", encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert image JSON to N-Triples file."
    )
    parser.add_argument("json_path", help="Path to input JSON file")
    parser.add_argument(
        "-o", "--output", default="images.nt", help="Output .nt file path"
    )
    args = parser.parse_args()

    json_to_nt(args.json_path, args.output)
