from rest_framework import serializers
from APIs.models import User, Group, UserGroup

class CreateGroupSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    group_name = serializers.CharField(max_length=50)
    description = serializers.CharField()
    
    def validate_group_name(self, value):
        if Group.objects.filter(name=value).exists():
            raise serializers.ValidationError("Group name must be unique.")
        return value

class JoinGroupSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()

    def validate(self, data):
        user_id = data.get("user_id")
        group_id = data.get("group_id")

        if not User.objects.filter(id=user_id).exists():
            raise serializers.ValidationError({"user_id": "User does not exist."})

        if not Group.objects.filter(id=group_id).exists():
            raise serializers.ValidationError({"group_id": "Group does not exist."})

        if UserGroup.objects.filter(user_id=user_id, group_id=group_id).exists():
            raise serializers.ValidationError({"error": "User is already in the group."})

        return data

class BlockUserSerializer(serializers.Serializer):
    admin_user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    blocked_user_id = serializers.IntegerField()

    def validate(self, data):
        admin_user_id = data.get("admin_user_id")
        group_id = data.get("group_id")
        blocked_user_id = data.get("blocked_user_id")

        admin_group = UserGroup.objects.filter(user_id=admin_user_id, group_id=group_id, is_admin=True).first()
        if not admin_group:
            raise serializers.ValidationError({"admin_user_id": "User is not an admin of the group."})

        if not UserGroup.objects.filter(user_id=blocked_user_id, group_id=group_id).exists():
            raise serializers.ValidationError({"blocked_user_id": "User is not in the group."})

        return data

class UnblockUserSerializer(serializers.Serializer):
    admin_user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    unblocked_user_id = serializers.IntegerField()

    def validate(self, data):
        admin_user_id = data.get("admin_user_id")
        group_id = data.get("group_id")
        unblocked_user_id = data.get("unblocked_user_id")

        admin_group = UserGroup.objects.filter(user_id=admin_user_id, group_id=group_id, is_admin=True).first()
        if not admin_group:
            raise serializers.ValidationError({"admin_user_id": "User is not an admin of the group."})

        user_group = UserGroup.objects.filter(user_id=unblocked_user_id, group_id=group_id, is_blocked=True).first()
        if not user_group:
            raise serializers.ValidationError({"unblocked_user_id": "User is not blocked in this group."})

        return data

class WritePostSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    content = serializers.CharField(max_length=255)

    def validate(self, data):
        user_id = data.get("user_id")
        group_id = data.get("group_id")

        if not User.objects.filter(id=user_id).exists():
            raise serializers.ValidationError({"user_id": "User does not exist."})

        if not Group.objects.filter(id=group_id).exists():
            raise serializers.ValidationError({"group_id": "Group does not exist."})

        if not UserGroup.objects.filter(user_id=user_id, group_id=group_id, is_blocked=False).exists():
            raise serializers.ValidationError({"error": "You are not a member of this group or you are blocked."})

        return data

class CommentPostSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    post_id = serializers.IntegerField()
    content = serializers.CharField(max_length=255)

class EditCommentSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    comment_id = serializers.IntegerField()
    content = serializers.CharField(max_length=255)