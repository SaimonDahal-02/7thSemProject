import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

import csv
from django.core.exceptions import ObjectDoesNotExist
from book.models import Book, Author, Genre

def import_books_from_csv(file_path):
    with open(file_path, 'r', encoding='latin1') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            isbn = row['ISBN']
            title = row['Book-Title']
            author_names = row['Book-Author'].split(',')
            publication_year = int(row['Year-Of-Publication'])
            publisher = row['Publisher']
            image_url = row['Image']
            description = row['Description']
            page_count_str = row['Page-Count']
            page_count = int(page_count_str.replace(',', ''))
            language = row['Language']
            genre_names = row['Genre'].split(',')

            try:
                book = Book.objects.get(isbn=isbn)
            except ObjectDoesNotExist:
                book = Book()

            book.isbn = isbn
            book.title = title
            book.description = description
            book.publication_year = publication_year
            book.publisher = publisher
            book.image_url = image_url
            book.page_count = page_count
            book.language = language
            book.save()

            authors = []
            for author_name in author_names:
                author, _ = Author.objects.get_or_create(name=author_name.strip())
                authors.append(author)

            book.author.set(authors)

            genres = []
            for genre_name in genre_names:
                genre, _ = Genre.objects.get_or_create(name=genre_name.strip())
                genres.append(genre)

            book.genres.set(genres)

        print("Data transfer completed.")

file_path = 'data/finalyeardata.csv'  # Replace with the path to your CSV file
import_books_from_csv(file_path)
