from rest_framework import serializers
from .models import CustomUser, SharedImage, Notification, UserRelationship
from .skills_config import AVAILABLE_SKILLS


class UserProfileSerializer(serializers.ModelSerializer):
    guild_name = serializers.CharField(source='guild.name', read_only=True, default=None)
    skills_detailed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'bio', 'avatar', 'dobroty', 'experience', 'level',
            'reputation', 'skill_points', 'guild', 'guild_name', 'guild_role',
            'skills', 'skills_detailed', 'last_active'
        ]
        read_only_fields = [
            'dobroty', 'experience', 'level', 'reputation', 'skill_points',
            'guild', 'guild_role', 'skills', 'last_active'
        ]

    def get_skills_detailed(self, obj):
        detailed = []
        for key, level in obj.skills.items():
            if key in AVAILABLE_SKILLS:
                skill_info = AVAILABLE_SKILLS[key].copy()
                skill_info['current_level'] = level
                skill_info['key'] = key
                detailed.append(skill_info)
        return detailed


class ChangePasswordSerializer(serializers.Serializer):
    """ Walidator do bezpiecznej zmiany hasła """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'title', 'message', 'created_at']


class SharedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedImage
        fields = ['id', 'image', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at']