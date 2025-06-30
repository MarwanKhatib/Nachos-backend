from rest_framework import serializers
from django.apps import apps
from APIs.models import User, Group, UserGroup

# Manually import models to ensure they are loaded
Group = apps.get_model('APIs', 'Group')
UserGroup = apps.get_model('APIs', 'UserGroup')
class CreateGroupSerializer(serializers.Serializer):
    group_name = serializers.CharField(max_length=50)
    description = serializers.CharField()
    
    def validate_group_name(self, value):
        if Group.objects.filter(name=value).exists():
            raise serializers.ValidationError("Group name must be unique.")
        return value


class BlockUserSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    blocked_user_id = serializers.IntegerField()

    def validate(self, attrs):
        group_id = attrs.get("group_id")
        blocked_user_id = attrs.get("blocked_user_id")

        if not UserGroup.objects.filter(user_id=blocked_user_id, group_id=group_id).exists():
            raise serializers.ValidationError({"blocked_user_id": "User is not in the group."})

        return attrs

class UnblockUserSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    unblocked_user_id = serializers.IntegerField()

    def validate(self, attrs):
        group_id = attrs.get("group_id")
        unblocked_user_id = attrs.get("unblocked_user_id")

        user_group = UserGroup.objects.filter(user_id=unblocked_user_id, group_id=group_id, is_blocked=True).first()
        if not user_group:
            raise serializers.ValidationError({"unblocked_user_id": "User is not blocked in this group."})

        return attrs

class WritePostSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=255)

class CommentPostSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=255)

class EditCommentSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=255)

class EditPostSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=255, help_text='New content for the post')

class EditGroupSerializer(serializers.Serializer):
    group_name = serializers.CharField(max_length=50, required=False, help_text='New name for the group (optional)')
    description = serializers.CharField(required=False, help_text='New description for the group (optional)')

    def validate(self, attrs):
        if not (attrs.get('group_name') or attrs.get('description')):
            raise serializers.ValidationError("At least one of 'group_name' or 'description' must be provided for editing.")
        return attrs

    def validate_group_name(self, value):
        if Group.objects.filter(name=value).exists():
            raise serializers.ValidationError("Group name must be unique.")
        return value

class GroupSerializer(serializers.ModelSerializer):
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'create_date', 'is_member']

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return UserGroup.objects.filter(user=request.user, group=obj).exists()
        return False

class AdminPostSerializer(serializers.ModelSerializer):
    post_id = serializers.IntegerField(source='id')
    group_id = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    group_owner_id = serializers.SerializerMethodField()
    group_owner_username = serializers.SerializerMethodField()
    post_owner_id = serializers.SerializerMethodField()
    post_owner_username = serializers.SerializerMethodField()
    is_editable = serializers.SerializerMethodField()
    created_at_date = serializers.DateTimeField(source='add_date')

    class Meta:
        model = apps.get_model('APIs', 'Post')
        fields = [
            'post_id', 'content', 'reaction_no', 'comment_no', 'is_editable',
            'group_id', 'group_name', 'group_owner_id', 'group_owner_username',
            'post_owner_id', 'post_owner_username', 'created_at_date'
        ]

    def get_group_id(self, obj):
        user_post = apps.get_model('APIs', 'UserPost').objects.filter(post=obj).first()
        return user_post.group.id if user_post else None

    def get_group_name(self, obj):
        user_post = apps.get_model('APIs', 'UserPost').objects.filter(post=obj).first()
        return user_post.group.name if user_post else None

    def get_group_owner_id(self, obj):
        user_post = apps.get_model('APIs', 'UserPost').objects.filter(post=obj).first()
        if user_post:
            group_admin = apps.get_model('APIs', 'UserGroup').objects.filter(group=user_post.group, is_admin=True).first()
            return group_admin.user.id if group_admin else None
        return None

    def get_group_owner_username(self, obj):
        user_post = apps.get_model('APIs', 'UserPost').objects.filter(post=obj).first()
        if user_post:
            group_admin = apps.get_model('APIs', 'UserGroup').objects.filter(group=user_post.group, is_admin=True).first()
            return group_admin.user.username if group_admin else None
        return None

    def get_post_owner_id(self, obj):
        user_post = apps.get_model('APIs', 'UserPost').objects.filter(post=obj).first()
        return user_post.user.id if user_post else None

    def get_post_owner_username(self, obj):
        user_post = apps.get_model('APIs', 'UserPost').objects.filter(post=obj).first()
        return user_post.user.username if user_post else None

    def get_is_editable(self, obj):
        return False
