import os
import requests
from django.core.management.base import BaseCommand
from book.models import Book  # Import your Book model
from django.conf import settings

class Command(BaseCommand):
    help = 'Save book images locally'

    def handle(self, *args, **options):
        books_with_images = Book.objects.exclude(image_url__isnull=True).exclude(image_url__exact='')

        for book in books_with_images:
            try:
                # Fetch the image from the URL
                response = requests.get(book.image_url, stream=True)
                if response.status_code == 200:
                    # Define the path where you want to save the image locally using the title
                    image_filename = f'{book.title}.jpg'
                    image_path = os.path.join(settings.MEDIA_ROOT, 'books', image_filename)

                    # Save the image to the local path
                    with open(image_path, 'wb') as local_image:
                        for chunk in response.iter_content(1024):
                            local_image.write(chunk)

                    # Update the book's image field to point to the local image
                    book.image.name = os.path.relpath(image_path, settings.MEDIA_ROOT)
                    book.save()

                    self.stdout.write(self.style.SUCCESS(f'Successfully saved image for book: {book.title}'))
                else:
                    self.stdout.write(self.style.ERROR(f'Failed to download image for book: {book.title}'))

            except Exception as e:
                # Handle any exceptions that may occur during the process
                self.stdout.write(self.style.ERROR(f"Error downloading image for book {book.title}: {str(e)}"))
