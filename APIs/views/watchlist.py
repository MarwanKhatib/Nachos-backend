from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from APIs.models.movie_model import Movie
from APIs.serializers.movie_serializers import MovieSerializer


class WatchlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all watchlisted movies for the authenticated user."""
        user = request.user
        watchlist_movies = user.watchlist.all()
        serializer = MovieSerializer(watchlist_movies, many=True)
        return Response({
            "count": watchlist_movies.count(),
            "results": serializer.data
        }, status=status.HTTP_200_OK)


class WatchlistManageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, movie_id):
        """Add a movie to the authenticated user's watchlist."""
        user = request.user
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            return Response({"detail": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.watchlist.filter(id=movie_id).exists():
            return Response({"detail": "Movie already in watchlist."}, status=status.HTTP_200_OK)

        user.watchlist.add(movie)
        return Response({"detail": "Movie added to watchlist."}, status=status.HTTP_201_CREATED)

    def delete(self, request, movie_id):
        """Remove a movie from the authenticated user's watchlist."""
        user = request.user
        try:
            movie = user.watchlist.get(id=movie_id)
        except Movie.DoesNotExist:
            return Response({"detail": "Movie not found in watchlist."}, status=status.HTTP_404_NOT_FOUND)

        user.watchlist.remove(movie)
        return Response({"detail": "Movie removed from watchlist."}, status=status.HTTP_200_OK)
