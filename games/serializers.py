from rest_framework import serializers
from .models import Category, Studio, Game, GameImage, Review
from drf_yasg import openapi

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image']


class StudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Studio
        fields = ['id', 'name']


class GameImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = GameImage
        fields = ['id', 'game', 'image']

    def validate(self, attrs):
        if not self.instance and attrs.get('game'):
            if attrs['game'].images.count() >= 4:
                raise serializers.ValidationError({"game": "Maximum 4 images allowed per game."})
        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    game_title = serializers.ReadOnlyField(source='game.title')
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'game', 'game_title', 'user', 'user_avatar', 
            'rating', 'text', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_user_avatar(self, obj):
        request = self.context.get('request')
        profile = getattr(obj.user, 'profile', None)
        
        if profile and profile.avatar:
            if request:
                return request.build_absolute_uri(profile.avatar.url)
            return profile.avatar.url
        return None


class MultipleImageField(serializers.ListField):
    swagger_schema_fields = {
        "type": openapi.TYPE_ARRAY,
        "items": {
            "type": openapi.TYPE_STRING,
            "format": openapi.FORMAT_BINARY,
        }
    }

    def get_value(self, dictionary):
        if hasattr(dictionary, 'getlist'):
            return dictionary.getlist(self.field_name)
        return dictionary.get(self.field_name, [])


class GameSerializer(serializers.ModelSerializer):
    rating = serializers.FloatField(source='average_rating', read_only=True)
    images = GameImageSerializer(many=True, read_only=True)

    description = serializers.CharField(required=False, allow_blank=True, default="")
    developer = serializers.CharField(required=False, allow_blank=True, default="")
    platforms = serializers.CharField(required=False, allow_blank=True, default="")
    system_requirements = serializers.JSONField(required=False, default=dict)
    video = serializers.CharField(required=False, allow_blank=True, default="")
    
    uploaded_images = MultipleImageField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    class Meta:
        model = Game
        fields = [
            'id', 'title', 'description', 'category', 'studio', 'developer', 'price', 'discount',
            'platforms', 'system_requirements', 'video', 'images', 'uploaded_images', 
            'active', 'rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'rating', 'created_at', 'updated_at', 'images']

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        valid_images = [img for img in uploaded_images if img and hasattr(img, 'size') and img.size > 0]
        
        if len(valid_images) > 4:
            raise serializers.ValidationError({"uploaded_images": "Maximum 4 images allowed per game."})

        for key in ['description', 'developer', 'platforms', 'video']:
            if key in validated_data and isinstance(validated_data[key], str):
                validated_data[key] = validated_data[key].strip()

        game = Game.objects.create(**validated_data)
        for image in valid_images:
            GameImage.objects.create(game=game, image=image)
                
        return game

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        valid_images = [img for img in uploaded_images if img and hasattr(img, 'size') and img.size > 0]
        
        if instance.images.count() + len(valid_images) > 4:
            raise serializers.ValidationError({"uploaded_images": "Maximum 4 images allowed per game."})

        for key in ['description', 'developer', 'platforms', 'video']:
            if key in validated_data and isinstance(validated_data[key], str):
                validated_data[key] = validated_data[key].strip()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        for image in valid_images:
            GameImage.objects.create(game=instance, image=image)
                
        return instance