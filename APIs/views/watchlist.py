from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from APIs.models.user_model import User
from APIs.models.movie_model import Movie
from APIs.serializers.movie_serializers import MovieSerializer

class WatchlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        watchlist_movies = user.watchlist.all()
        serializer = MovieSerializer(watchlist_movies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        movie_id = request.data.get('movie_id')
        if not movie_id:
            return Response({"detail": "Movie ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            return Response({"detail": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)
        
        user.watchlist.add(movie)
        return Response({"detail": "Movie added to watchlist."}, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        movie_id = request.data.get('movie_id')
        if not movie_id:
            return Response({"detail": "Movie ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            movie = user.watchlist.get(id=movie_id)
        except Movie.DoesNotExist:
            return Response({"detail": "Movie not found in watchlist."}, status=status.HTTP_404_NOT_FOUND)
        
        user.watchlist.remove(movie)
        return Response({"detail": "Movie removed from watchlist."}, status=status.HTTP_200_OK)
