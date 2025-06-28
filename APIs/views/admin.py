import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.pagination import PageNumberPagination
from APIs.models.movie_model import Movie
from APIs.models.user_model import User
from APIs.models.group_model import Group
from APIs.models.genre_model import Genre # Import Genre model
from typing import cast
from rest_framework.decorators import action
from APIs.serializers.user_serializers import UserAdminSerializer, RegisterUserSerializer
from APIs.views.user import IsSuperUser, IsStaffOrSuperUser # Import from APIs.views.user
from django.db.models import Manager # Import Manager
from APIs.managers import CustomUserManager # Import CustomUserManager
from typing import cast # Ensure cast is imported

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class DashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        path = request.path
        logger.info(f"Request by user {user_id} to {path}")
        try:
            movie_count = cast(Manager, Movie.objects).count()
            user_count = cast(CustomUserManager, User.objects).count()
            group_count = cast(Manager, Group.objects).count()
            genre_count = cast(Manager, Genre.objects).count() # Add genre count

            data = {
                'movie_count': movie_count,
                'user_count': user_count,
                'group_count': group_count,
                'genre_count': genre_count, # Include genre count in data
            }
            logger.info(f"Request by user {user_id} to {path} successful.")
            return Response(data, status=HTTP_200_OK)
        except Exception as e:
            logger.error(f"Request by user {user_id} to {path} failed: {e}", exc_info=True)
            return Response({"error": "Internal server error."}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserListAPIView(ListAPIView):
    queryset = cast(CustomUserManager, User.objects).all().order_by('id')
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminUser]
    pagination_class = UserPagination

class UserDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = cast(CustomUserManager, User.objects).all()
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id' # Use 'id' as the lookup field for user detail

    def delete(self, request, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        path = request.path
        try:
            instance = self.get_object()
            instance.delete()
            logger.info(f"User {instance.id} deleted by admin {user_id} from {path}.")
            return Response(status=HTTP_204_NO_CONTENT)
        except User.DoesNotExist: # Use User.DoesNotExist directly
            logger.warning(f"Attempt to delete non-existent user by admin {user_id} from {path}.")
            return Response({"detail": "User not found."}, status=HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting user by admin {user_id} from {path}: {e}", exc_info=True)
            return Response({"error": "Internal server error."}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class UserCreateAPIView(CreateAPIView):
    queryset = cast(CustomUserManager, User.objects).all()
    serializer_class = UserAdminSerializer # Use UserAdminSerializer for admin-created users
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        path = request.path
        
        # For normal user creation by admin, ensure flags are set to False/True for active/verified
        serializer = self.get_serializer(data=request.data, context={
            'is_superuser_creation': False,
            'is_staff_creation': False,
            'is_active': True, # Auto-activate account
            'is_email_verified': True # Auto-verify email
        })
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        logger.info(f"New normal user created by admin {user_id} from {path}.")
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

class SuperuserCreateAPIView(CreateAPIView):
    queryset = cast(CustomUserManager, User.objects).all()
    serializer_class = UserAdminSerializer
    permission_classes = [IsSuperUser] # Only superusers can create other superusers

    def create(self, request, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        path = request.path
        serializer = self.get_serializer(data=request.data, context={
            'is_superuser_creation': True,
            'is_staff_creation': True, # Superusers are also staff
            'is_active': True,
            'is_email_verified': True
        })
        serializer.is_valid(raise_exception=True)
        user = serializer.save() # The serializer's create method handles setting flags
        logger.info(f"New superuser created by admin {user_id} from {path}.")
        return Response(UserAdminSerializer(user).data, status=HTTP_201_CREATED)

class StaffUserCreateAPIView(CreateAPIView):
    queryset = cast(CustomUserManager, User.objects).all()
    serializer_class = UserAdminSerializer
    permission_classes = [IsStaffOrSuperUser] # Staff or superuser can create staff users

    def create(self, request, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        path = request.path
        serializer = self.get_serializer(data=request.data, context={
            'is_staff_creation': True,
            'is_superuser_creation': False, # Explicitly ensure staff user is not superuser
            'is_active': True,
            'is_email_verified': True
        })
        serializer.is_valid(raise_exception=True)
        user = serializer.save() # The serializer's create method handles setting flags
        logger.info(f"New staff user created by admin {user_id} from {path}.")
        return Response(UserAdminSerializer(user).data, status=HTTP_201_CREATED)
