
from celery import Celery
from django.core.management.base import BaseCommand
import requests
from celery import shared_task
from django.conf import settings
from book.models import Book
from book.serializers import BookSerializer

@shared_task
def update_book_details(isbn):
    api_key = settings.GOOGLE_BOOKS_API_KEY
    book = Book.objects.get(isbn=isbn)
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        book_data = response.json()
        serializer = BookSerializer(instance=book, data=book_data['items'][0]['volumeInfo'], partial=True)
        if serializer.is_valid():
            serializer.save()
    else:
        # Handle API response errors
        pass

class Command(BaseCommand):
    help = 'Update book details from Google Books API'

    def handle(self, *args, **options):
        book_isbns = Book.objects.values_list('isbn', flat=True)

        for isbn in book_isbns:
            update_book_details.delay(isbn)
            self.stdout.write(self.style.SUCCESS(f"Update task queued for ISBN {isbn}"))