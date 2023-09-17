import os
import requests
from django.core.files import File
from book.models import Book  # Import your Book model

def save_images_locally():
    books_with_images = Book.objects.exclude(image_url__isnull=True).exclude(image_url__exact='')

    for book in books_with_images:
        try:
            # Fetch the image from the URL
            response = requests.get(book.image_url, stream=True)
            if response.status_code == 200:
                # Define the path where you want to save the image locally using the title
                image_filename = f'{book.title}.jpg'
                image_path = os.path.join('media', 'books', image_filename)

                # Save the image to the local path
                with open(image_path, 'wb') as local_image:
                    for chunk in response.iter_content(1024):
                        local_image.write(chunk)

                # Update the book's image field to point to the local image
                book.image.name = f'books/{image_filename}'
                book.save()

        except Exception as e:
            # Handle any exceptions that may occur during the process
            print(f"Error downloading image for book {book.title}: {str(e)}")

# Run the function to save images locally
save_images_locally()
