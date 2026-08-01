from rest_framework import serializers
from .models import Category, Game, GameImage, Review


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.

    Fields:
    - id: Unique identifier of the category.
    - name: Name of the category.
    - description: Description of the category.
    - image: Optional image representing the category.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image']


class GameImageSerializer(serializers.ModelSerializer):
    """
    Serializer for GameImage model representing individual screenshots or gallery images.
    """
    class Meta:
        model = GameImage
        fields = ['id', 'image']


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model.
    """
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Review
        fields = ['id', 'game', 'user', 'rating', 'text', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']


class GameSerializer(serializers.ModelSerializer):
    """
    Serializer for Game model.

    Fields:
    - id: Unique identifier of the game.
    - title: Title of the game.
    - description: Description of the game.
    - category: Related category ID.
    - price: Base price of the game.
    - discount: Discount percentage or amount.
    - platforms: Supported platforms (e.g., PC, PS5, Xbox Series X).
    - video: Optional video trailer file.
    - active: Boolean indicating if the game is active for purchase.
    - images: List of associated product screenshots (read-only).
    - rating: Float value from the model's `average_rating` method (read-only).
    - created_at: Creation timestamp.
    - updated_at: Last update timestamp.
    """
    rating = serializers.FloatField(source='average_rating', read_only=True)
    images = GameImageSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = [
            'id', 'title', 'description', 'category', 'price', 'discount',
            'platforms', 'video', 'images', 'active', 'rating',
            'created_at', 'updated_at'
        ]