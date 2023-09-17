import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # Replace "myproject.settings" with your actual settings module path
import django
django.setup()

import csv
from django.core.exceptions import ObjectDoesNotExist
from book.models import Book, Author

def import_books_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            isbn = row['ISBN']
            title = row['Book-Title']
            author_names = row['Book-Author'].split(',')
            # Validate and convert publication_year
            publication_year = row['Year-Of-Publication']
            if publication_year.isdigit():
                publication_year = int(publication_year)
            else:
                publication_year = 0
            publisher = row['Publisher']
            image_url = row['Image-URL-M']

            # Check if the book already exists based on ISBN
            try:
                book = Book.objects.get(isbn=isbn)
            except ObjectDoesNotExist:
                book = Book()

            book.isbn = isbn
            book.title = title
            book.publication_year = publication_year
            book.publisher = publisher
            book.image_url = image_url
            book.save()

            # Update authors for the book
            authors = []
            for author_name in author_names:
                author, _ = Author.objects.get_or_create(name=author_name.strip())
                authors.append(author)

            book.author.set(authors)

        print("Data transfer completed.")

file_path = 'data/Books.csv'
import_books_from_csv(file_path)
