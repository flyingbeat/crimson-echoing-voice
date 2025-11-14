from collections import Counter

from handlers.sparql_handler import SparqlHandler


class RecommendationHandler:
    def __init__(self, sparql_handler: SparqlHandler):
        self.sparql_handler = sparql_handler

    def get_recommendations(self, entity_ids: list[str]) -> list[str]:
        # First, get the common properties from the given movies
        common_properties = self.sparql_handler.count_common_properties_for_entities(
            entity_ids=entity_ids
        )

        print("found properties: ", common_properties)

        # Then, get movies that have these common properties
        movies_with_properties = (
            self.sparql_handler.get_entities_with_common_properties(common_properties)
        )

        # Now, we flatten the lists of movies to count the occurrences of each movie
        all_recommended_movies = []
        for relation in movies_with_properties.values():
            for movie_list in relation.values():
                all_recommended_movies.extend(movie_list)

        # Count how many times each movie was recommended
        movie_counts = Counter(all_recommended_movies)

        print("found movies: ", movie_counts.most_common()[0:10])

        # Remove the movies that were originally given as input
        for entity_id in entity_ids:
            if entity_id in movie_counts:
                del movie_counts[entity_id]

        # Sort the movies by the frequency of recommendation
        sorted_recommendations = [movie for movie, count in movie_counts.most_common()]

        return sorted_recommendations
