import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters # Import filters
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
from typing import cast
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from drf_yasg import openapi # Import openapi
from drf_yasg.utils import swagger_auto_schema # Import swagger_auto_schema

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class DashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        path = request.path
        logger.info(f"Request by user {user_id} to {path}")
        try:
            movie_count = cast(Manager, Movie.objects).count() # type: ignore
            user_count = cast(CustomUserManager, User.objects).count() # type: ignore
            group_count = cast(Manager, Group.objects).count() # type: ignore
            genre_count = cast(Manager, Genre.objects).count() # type: ignore # Add genre count

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

class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    username = django_filters.CharFilter(field_name='username', lookup_expr='icontains')
    first_name = django_filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(field_name='last_name', lookup_expr='icontains')

    # Date fields for range filtering
    birth_date_after = django_filters.DateFilter(field_name='birth_date', lookup_expr='gte')
    birth_date_before = django_filters.DateFilter(field_name='birth_date', lookup_expr='lte')

    join_date_after = django_filters.DateFilter(field_name='join_date', lookup_expr='gte')
    join_date_before = django_filters.DateFilter(field_name='join_date', lookup_expr='lte')

    last_login_after = django_filters.DateFilter(field_name='last_login', lookup_expr='gte')
    last_login_before = django_filters.DateFilter(field_name='last_login', lookup_expr='lte')

    date_joined_after = django_filters.DateFilter(field_name='date_joined', lookup_expr='gte')
    date_joined_before = django_filters.DateFilter(field_name='date_joined', lookup_expr='lte')

    # Number fields for range filtering
    watched_no_min = django_filters.NumberFilter(field_name='watched_no', lookup_expr='gte')
    watched_no_max = django_filters.NumberFilter(field_name='watched_no', lookup_expr='lte')

    # Related fields (Many-to-Many)
    groups = django_filters.CharFilter(field_name='groups__id', lookup_expr='in', distinct=True)
    user_permissions = django_filters.CharFilter(field_name='user_permissions__id', lookup_expr='in', distinct=True)

    class Meta:
        model = User
        fields = [
            'id',
            'is_active',
            'is_email_verified',
            'is_staff',
            'is_superuser',
            'email',
            'username',
            'first_name',
            'last_name',
            'birth_date',
            'join_date',
            'last_login',
            'date_joined',
            'watched_no',
            'groups',
            'user_permissions',
        ]

class UserListAPIView(ListAPIView):
    queryset = cast(CustomUserManager, User.objects).all().order_by('id') # type: ignore
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminUser]
    pagination_class = UserPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = UserFilter
    search_fields = ['id', 'username', 'email', 'first_name', 'last_name']

    @swagger_auto_schema(
        operation_description="List all users with optional search and filtering.",
        operation_summary="List users",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search by user ID, username, email, first name, or last name (case-insensitive)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "id",
                openapi.IN_QUERY,
                description="Filter by user ID",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "is_active",
                openapi.IN_QUERY,
                description="Filter by active status (true/false)",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "is_email_verified",
                openapi.IN_QUERY,
                description="Filter by email verification status (true/false)",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "is_staff",
                openapi.IN_QUERY,
                description="Filter by staff status (true/false)",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "is_superuser",
                openapi.IN_QUERY,
                description="Filter by superuser status (true/false)",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "email",
                openapi.IN_QUERY,
                description="Search by email (case-insensitive contains)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "username",
                openapi.IN_QUERY,
                description="Search by username (case-insensitive contains)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "first_name",
                openapi.IN_QUERY,
                description="Search by first name (case-insensitive contains)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "last_name",
                openapi.IN_QUERY,
                description="Search by last name (case-insensitive contains)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "birth_date",
                openapi.IN_QUERY,
                description="Filter by exact birth date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "birth_date_after",
                openapi.IN_QUERY,
                description="Filter by birth date greater than or equal to (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "birth_date_before",
                openapi.IN_QUERY,
                description="Filter by birth date less than or equal to (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "join_date",
                openapi.IN_QUERY,
                description="Filter by exact join date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "join_date_after",
                openapi.IN_QUERY,
                description="Filter by join date greater than or equal to (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "join_date_before",
                openapi.IN_QUERY,
                description="Filter by join date less than or equal to (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "last_login_after",
                openapi.IN_QUERY,
                description="Filter by last login date greater than or equal to (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "last_login_before",
                openapi.IN_QUERY,
                description="Filter by last login date less than or equal to (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "date_joined_after",
                openapi.IN_QUERY,
                description="Filter by date joined greater than or equal to (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "date_joined_before",
                openapi.IN_QUERY,
                description="Filter by date joined less than or equal to (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "watched_no",
                openapi.IN_QUERY,
                description="Filter by exact number of watched movies",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "watched_no_min",
                openapi.IN_QUERY,
                description="Filter by minimum number of watched movies",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "watched_no_max",
                openapi.IN_QUERY,
                description="Filter by maximum number of watched movies",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "groups",
                openapi.IN_QUERY,
                description="Filter by group ID (e.g., ?groups=1,2)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "user_permissions",
                openapi.IN_QUERY,
                description="Filter by user permission ID (e.g., ?user_permissions=1,2)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: UserAdminSerializer(many=True),
            500: "Internal Server Error",
        },
        tags=["Admin Users"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class UserDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = cast(CustomUserManager, User.objects).all() # type: ignore
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
        except User.DoesNotExist: # type: ignore # Use User.DoesNotExist directly
            logger.warning(f"Attempt to delete non-existent user by admin {user_id} from {path}.")
            return Response({"detail": "User not found."}, status=HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting user by admin {user_id} from {path}: {e}", exc_info=True)
            return Response({"error": "Internal server error."}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class UserCreateAPIView(CreateAPIView):
    queryset = cast(CustomUserManager, User.objects).all() # type: ignore
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
    queryset = cast(CustomUserManager, User.objects).all() # type: ignore
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
    queryset = cast(CustomUserManager, User.objects).all() # type: ignore
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
