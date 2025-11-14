from handlers.sparql_hanlder import SparqlHandler
from collections import Counter

class RecommendationHandler:
    def __init__(self, sparql_handler: SparqlHandler):
        self.sparql_handler = sparql_handler
        self.relation_whitelist = [
            "P31",  # instance of
            "P57",  # director
            "P162",  # producer
            "P272",  # production company
            "P58",  # screenwriter
            "P166",  # award received
            "P577",  # release date
            "P136",  # genre
        ]

    def get_recommendations(self, entity_ids: list[str]) -> list[str]:
        # First, get the common properties from the given movies
        common_properties = self.sparql_handler.get_properties_for_entities(
            entity_ids=entity_ids,
            relation_ids=self.relation_whitelist
        )

        print("found properties: ", common_properties)

        # Then, get movies that have these common properties
        movies_with_properties = self.sparql_handler.get_movies_with_properties(common_properties)

        # Now, we flatten the lists of movies to count the occurrences of each movie
        all_recommended_movies = []
        for relation in movies_with_properties.values():
            for movie_list in relation.values():
                all_recommended_movies.extend(movie_list)

        # Count how many times each movie was recommended
        movie_counts = Counter(all_recommended_movies)

        print("found movies: ", movies_with_properties)

        # Remove the movies that were originally given as input
        for entity_id in entity_ids:
            if entity_id in movie_counts:
                del movie_counts[entity_id]

        # Sort the movies by the frequency of recommendation
        sorted_recommendations = [movie for movie, count in movie_counts.most_common()]

        return sorted_recommendations
