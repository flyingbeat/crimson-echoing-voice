#!/usr/bin/env python3

import math
import sys
import time
from pathlib import Path
from typing import Callable, List, Set

import requests
from rdflib import Graph, Literal, Namespace, URIRef

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
WD = Namespace("http://www.wikidata.org/entity/")
WIKIDATA_ENTITY_PREFIX = "http://www.wikidata.org/entity/"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "AltLabelFetcher/1.0 (GitHub Copilot) rdflib; +https://www.wikidata.org"


def load_entities_from_nt(
    nt_path: Path, instance_of_filter: list[URIRef]
) -> Set[URIRef]:
    g = Graph()
    g.parse(str(nt_path), format="nt")
    entities: Set[URIRef] = set()

    # Collect subjects and objects that are Wikidata entities
    for s, p, o in g.triples((None, WDT.P31, None)):
        if (
            isinstance(s, URIRef)
            and str(s).startswith(WIKIDATA_ENTITY_PREFIX)
            and o in instance_of_filter
        ):
            entities.add(s)
    return entities


def chunked(iterable: List[URIRef], size: int):
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def get_properties_of_this_type(type: URIRef = WD.Q11424) -> Set[URIRef]:
    wikidata_id = wikidata_ids_from_uris([type])[0]
    query = f"""
    SELECT ?property WHERE {{
        wd:{wikidata_id} wdt:P1963 ?property .
    }}
    """
    r = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/sparql-results+json",
        },
    )
    r.raise_for_status()
    data = r.json()
    properties = []
    for b in data.get("results", {}).get("bindings", []):
        property_uri = b["property"]["value"]
        properties.append(URIRef(property_uri))
    return set(properties)


def build_altlabel_query(entity_ids: List[str]) -> str:
    # Query altLabel for a batch of entities by VALUES
    # Only English altLabels
    values = " ".join(f"wd:{eid}" for eid in entity_ids)
    return f"""
    SELECT ?entity ?altLabel WHERE {{
      VALUES ?entity {{ {values} }}
      ?entity skos:altLabel ?altLabel .
      FILTER (lang(?altLabel) = "en")
    }}
    """


def wikidata_ids_from_uris(uris: List[URIRef]) -> List[str]:
    ids = []
    for u in uris:
        s = str(u)
        if s.startswith(WIKIDATA_ENTITY_PREFIX):
            ids.append(s.split("/")[-1])
    return ids


def print_progress(current: int, total: int):
    if total == 0:
        return
    width = 40  # progress bar width
    filled = int((current / total) * width)
    bar = "[" + "#" * filled + "-" * (width - filled) + "]"
    msg = f"\rFetching altLabels: {bar} {current}/{total} batches"
    print(msg, end="", flush=True)
    if current == total:
        print()  # newline at completion


def fetch_altlabels(
    entity_uris: List[URIRef],
    timeout: int = 120,
    sleep_seconds: float = 0.1,
    on_progress: Callable[[int, int], None] | None = None,
) -> List[tuple[URIRef, Literal]]:
    alt_triples: List[tuple[URIRef, Literal]] = []
    ids = wikidata_ids_from_uris(entity_uris)

    batch_size = 250
    total_batches = math.ceil(len(ids) / batch_size) if ids else 0

    # Query in chunks to respect endpoint limits
    for i, batch in enumerate(chunked(ids, batch_size), start=1):
        q = build_altlabel_query(batch)
        r = requests.get(
            SPARQL_ENDPOINT,
            params={"query": q, "format": "json"},
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/sparql-results+json",
            },
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        for b in data.get("results", {}).get("bindings", []):
            entity_uri = b["entity"][
                "value"
            ]  # e.g., https://www.wikidata.org/entity/Q123
            alt = b["altLabel"]["value"]
            eid = wikidata_ids_from_uris([URIRef(entity_uri)])[0]
            uri = WD[eid] if eid.startswith("Q") else WDT[eid]
            alt_triples.append((uri, Literal(alt)))
        # Update progress after executing this batch
        if on_progress:
            on_progress(i, total_batches)

        # Be polite to the endpoint
        time.sleep(sleep_seconds)

    return alt_triples


def write_nt(alt_triples: List[tuple[URIRef, Literal]], out_path: Path):
    out_graph = Graph()
    for uri, alt in alt_triples:
        out_graph.add((uri, SKOS.altLabel, alt))
    # Serialize to N-Triples
    out_graph.serialize(destination=str(out_path), format="nt", encoding="utf-8")


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_alt_label_graph.py <input.nt> <output.nt>")
        sys.exit(1)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    if not in_path.exists():
        print(f"Input file not found: {in_path}")
        sys.exit(1)

    print(f"Loading entities from {in_path} ...")
    film_properties = get_properties_of_this_type(WD.Q11424)  # film
    entities = sorted(
        load_entities_from_nt(
            in_path,
            instance_of_filter=[
                URIRef("http://www.wikidata.org/entity/Q201658"),  # 'film genre'
                URIRef("http://www.wikidata.org/entity/Q6256"),  # 'country'
                # URIRef("http://www.wikidata.org/entity/Q5"),  # 'human'
                URIRef(
                    "http://www.wikidata.org/entity/Q1762059"
                ),  # 'film production company'
                URIRef(
                    "http://www.wikidata.org/entity/Q10689397"
                ),  # 'television production company'
                URIRef("http://www.wikidata.org/entity/Q375336"),  # 'film studio'
                URIRef("http://www.wikidata.org/entity/Q19020"),  # 'Academy Awards'
                URIRef("http://www.wikidata.org/entity/Q38033430"),  # 'class of award'
                URIRef("http://www.wikidata.org/entity/Q618779"),  # 'award'
                URIRef("http://www.wikidata.org/entity/Q4220917"),  # 'film award'
                URIRef("http://www.wikidata.org/entity/Q1407225"),  # 'television award'
                URIRef(
                    "http://www.wikidata.org/entity/Q1011547"
                ),  # 'Golden Globe Award'
                URIRef(
                    "http://www.wikidata.org/entity/Q559618"
                ),  # 'fictional universe'
                URIRef(
                    "http://www.wikidata.org/entity/Q23660208"
                ),  # 'MPA classification category'
            ],
        )
    )
    entities = entities + list(film_properties)
    print(entities[-1])
    print(f"Found {len(entities)} Wikidata entities.")
    print("Fetching altLabels from Wikidata ...")
    alt_triples = fetch_altlabels(entities, on_progress=print_progress)
    print(f"Found {len(alt_triples)} altLabel triples.")

    print(f"Writing altLabel graph to {out_path} ...")
    write_nt(alt_triples, out_path)
    print("Done.")


if __name__ == "__main__":
    main()
