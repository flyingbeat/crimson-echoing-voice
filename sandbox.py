def get_similar_entities(entity_ids: list[str]) -> list[str]:
    relation_whitelist = [
        "wdt:P31",  # instance of
        "wdt:P57",  # director
        "wdt:P162",  # producer
        "wdt:P272",  # production company
        "wdt:P58",  # screenwriter
        "wdt:P166",  # award received
        "wdt:P577",  # release date
        "wdt:P136",  # genre
    ]

    similar_entities = []
    if not entity_ids:
        return []
    for entity_id in entity_ids:
        for relation_id in relation_whitelist:
            object_query = f"""
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX schema: <http://schema.org/>
                    PREFIX wd: <http://www.wikidata.org/entity/>
                    REFIX wdt: <http://www.wikidata.org/prop/direct/>

                    SELECT (COALESCE(?objLabel, STR(?obj)) AS ?result) (COALESCE(?objDesc, "") AS ?description) {{
                        <{entity_id}> <{relation_id}> ?obj .
                        OPTIONAL {{
                            ?obj rdfs:label ?objLabel .
                        }}
                        OPTIONAL {{
                            ?obj schema:description ?objDesc .
                        }}
                    }}
                """
            results = _execute_sparql_query(object_query)
            if results:
                similar_entities.append(results)

    print(similar_entities)
    return similar_entities


if __name__ == "__main__":
    ids = [
        "Q329434",
        "Q1243029",
        "Q221103",
    ]
    res = get_similar_entities(ids)
