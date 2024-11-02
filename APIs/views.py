import logging
from rest_framework import status
from .serializers import UserSerializer
from django.contrib.auth.models import User
from rest_framework.response import Response
from django.middleware.csrf import get_token
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate


logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def get_csrf_token(request):
    csrf_token = get_token(request)
    return Response({"csrfToken": csrf_token})


@api_view(["POST"])
@permission_classes([IsAdminUser])
def get_users(request):
    try:
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Error fetching users: %s", str(e))
        return Response(
            {"error": "An error occurred while fetching users."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def create_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {"user": serializer.data, "token": token.key},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error creating token: {str(e)}")
            return Response(
                {"error": "An error occurred while creating the user token."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        logger.error(f"Validation errors: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_user(request):
    user_id = request.data.get("user_id")
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        logger.error("Validation errors: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def delete_user(request):
    user_id = request.data.get("user_id")
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return Response(
            {"message": "User deleted successfully."}, status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("Error deleting user: %s", str(e))
        return Response(
            {"error": "An error occurred while deleting the user."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def fetch_user_token(request):
    user_id = request.data.get("user_id")
    try:
        user = User.objects.get(id=user_id)
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("Error fetching token: %s", str(e))
        return Response(
            {"error": "An error occurred while fetching the token."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")
    
    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Use authenticate to verify the username and password
    user = authenticate(username=username, password=password)
    if user is not None:
        logger.info(f"User {username} logged in successfully.")
        return Response(
            {
                "username": user.username,
                "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
            },
            status=status.HTTP_200_OK,
        )
    else:
        logger.warning(f"Invalid login attempt for user {username}.")
    
    return Response(
        {"error": "Invalid username or password."},
        status=status.HTTP_401_UNAUTHORIZED,
    )
