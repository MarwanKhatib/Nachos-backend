from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import * 
from .serializers import *


def hello_world(request):
    return HttpResponse("Hello, world!")


class RegisterUserView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "User registered successfully. Check your email for the verification code."
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    def post(self, request):

        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.filter(email=email).first()
            user.is_active = True
            user.save()


            movies = Movie.objects.all()
            movies_list = list(movies)
            for movie in movies_list:
                suggestion = UserSuggestionList(
                    user=user, movie=movie, total=0, is_watched=False
                )
                suggestion.save()

            return Response(
                {"message": "Email verified successfully."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SelectGenresView(APIView):
    def post(self, request):
        serializer = SelectGenresSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data["user_id"]
            genre_ids = serializer.validated_data["genre_ids"]

            # erase points of old genres
            user_old_genres = UserGenre.objects.filter(user_id=user_id)
            user_suggestion_list = list(
                UserSuggestionList.objects.filter(user_id=user_id)
            )
            for suggestion in user_suggestion_list:
                cur_suggestion = MovieGenre.objects.filter(movie_id=suggestion.movie_id)
                suggestion.total += -self.genres_delta(user_old_genres, cur_suggestion)
                suggestion.save()

            # Clear existing genre preferences
            UserGenre.objects.filter(user_id=user_id).delete()

            # Add new genre preferences and adjust genres delta
            for genre_id in genre_ids:
                UserGenre.objects.create(user_id=user_id, genre_id=genre_id)
            for suggestion in user_suggestion_list:
                cur_suggestion = MovieGenre.objects.filter(movie_id=suggestion.movie_id)
                suggestion.total = self.genres_delta(genre_ids, list(cur_suggestion))
                suggestion.save()
            return Response(
                {"message": "Genre preferences updated successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def genres_delta(self, list1, list2):
        le = max(len(list1), len(list2))
        if le == 0:
            return 0
        qu = le * (le + 1) / 2
        tot = 1000
        tot /= qu
        val = 0
        for i in range(len(list1)):
            for j in range(len(list2)):
                if list1[i] == list2[j].genre_id:
                    val += int(((le - max(i, j)) * tot) + 0.5)
        return val


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class GetUserGenresView(APIView):
    def get(self, request, user_id):
        try:
            # Get the user
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Get the user's genres
        user_genres = UserGenre.objects.filter(user_id=user).select_related("genre")
        genre_names = [ug.genre.name for ug in user_genres]

        # Serialize the response
        response_data = {"genres": genre_names}
        return Response(response_data, status=status.HTTP_200_OK)


class GetTop10Suggestion(APIView):
    def get(self, request, user_id):
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )


        user_suggestion = UserSuggestionList.objects.filter(
            user_id=user, is_watched=False
        ).order_by("-total")

        if len(user_suggestion) == 0 :
           
           UserSuggestionList.objects.filter( user_id = user ).update( is_watched = False )
           user_suggestion = UserSuggestionList.objects.filter(
            user_id=user, is_watched=False
            ).order_by("-total")
            
        
        if len(user_suggestion) > 10 :
            user_suggestion = user_suggestion[:10]
        
        for suggestion in user_suggestion:
            suggestion.is_watched = True
            suggestion.save()
        movies_names = [us.movie_id for us in user_suggestion]
        # Serialize the response
        response_data = {"movie_ids": movies_names}
        return Response(response_data, status=status.HTTP_200_OK)



class GetMovie (APIView) :
    
    def get(self, request, movie_id):
        
        try:
            movie = Movie.objects.get(id=movie_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND
            )

        movie_actors = MovieActor.objects.filter ( movie_id = movie.id )
        movie_genres = MovieGenre.objects.filter ( movie_id = movie.id )
        movie_producers = MovieProducer.objects.filter ( movie_id = movie.id )
        movie_writers = MovieWriter.objects.filter ( movie_id = movie.id )
        movie_directors = MovieDirector.objects.filter ( movie_id = movie.id )

        actors = Actor.objects.filter( id__in = movie_actors.values_list('actor_id'))
        writers = Writer.objects.filter( id__in = movie_writers.values_list('writer_id'))
        producers = Producer.objects.filter( id__in = movie_producers.values_list('producer_id'))
        directors = Director.objects.filter( id__in = movie_directors.values_list('director_id'))
        genres = Genre.objects.filter( id__in = movie_genres.values_list('genre_id'))



        actors_names = self.setup_pairs(actors)
        writers_names = self.setup_pairs(writers)
        producers_names = self.setup_pairs(producers)
        directors_names = self.setup_pairs(directors)
        genres_names = self.setup_pairs(genres)
        
        movie_data = {
            "name": movie.name,
            "description": movie.description,
            "trailer": movie.trailer,
            "poster": movie.poster,
            "language": movie.language.name,

            "actors": actors_names,
            "writers": writers_names,
            "producers":producers_names, 
            "directors": directors_names,
            "genres": genres_names,
        }

        serializer = MovieInfosSerializer(data=movie_data)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    def setup_pairs ( self , tmp_list ) :
        tmp_names = [ tmp.name for tmp in tmp_list ]
        return tmp_names