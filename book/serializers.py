from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('isbn', 'title', 'author', 'publisher', 'publication_year', 'description', 'genres', 'page_count')
