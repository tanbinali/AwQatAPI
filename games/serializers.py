from rest_framework import serializers
from .models import Category, Game, Review, GameImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Review
        # Changed 'comment' to 'text' to match your Review model
        fields = ['id', 'user', 'rating', 'text', 'created_at']
        read_only_fields = ['user', 'game']

class GameSerializer(serializers.ModelSerializer):
    # Read-only nested category for GET requests
    category = CategorySerializer(read_only=True)
    
    # Write-only ID field for POST/PUT requests
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        source='category', 
        write_only=True
    )
    
    # Computed field from the view's annotate() function
    average_rating = serializers.FloatField(read_only=True)
    
    # Custom field to retrieve image URLs
    images = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = [
            'id', 'title', 'description', 'category', 'category_id', 
            'price', 'discount', 'platforms', 'video', 'images', 'active', 
            'average_rating', 'created_at', 'updated_at'
        ]

    def get_images(self, obj):
        request = self.context.get('request')
        if not request:
            return []
            
        images = obj.images.all()
        return [request.build_absolute_uri(img.image.url) for img in images if img.image]