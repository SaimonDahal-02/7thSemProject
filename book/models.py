from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.db.models import Avg

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_reviewer = models.BooleanField(default=False)
    is_user = models.BooleanField(default=True)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(null=True, blank=True)
    reviews_written = models.PositiveIntegerField(default=0)
    total_pages_read = models.IntegerField(default=0)
    
    sex = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], null=True, blank=True)
    favorite_genre = models.CharField(max_length=255, null=True, blank=True)
    
    website_url = models.URLField(max_length=255, null=True, blank=True)
    facebook_url = models.URLField(max_length=255, null=True, blank=True)
    twitter_url = models.URLField(max_length=255, null=True, blank=True)
    instagram_url = models.URLField(max_length=255, null=True, blank=True)
       
    def __str__(self):
        return self.user.username
    
class Book(models.Model):
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True)   
    title = models.CharField(max_length=350)
    description = models.TextField(blank=True, null=True)
    publisher = models.CharField(max_length=200, blank=True, null=True)
    publication_year = models.IntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    favorites = models.ManyToManyField(UserProfile, related_name='favorite', default=None, blank=True)
    
    page_count = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=50, default="English")
    genres = models.ManyToManyField("Genre", related_name='books', blank=True)
    
    image_local = models.ImageField(upload_to='books/', blank=True, null=True)
    
    author = models.ManyToManyField("Author", blank=True, related_name="book_authors")
    
    
    def __str__(self):
        return f"{self.title}: {self.average_rating()}"
    
class Author(models.Model):
    name = models.CharField(max_length=350)
    
    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class BookProgress(models.Model):
    STATUS_CHOICES = [
        ('reading', 'Reading'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    page_number = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)


RATE_CHOICES = [
    (1, '1 - Terrible'),
    (2, '2 - Not Good'),
    (3, '3 - Average'),
    (4, '4 - Good'),
    (5, '5 - Loved it'),
]
        
class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    publish = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-publish']
        
    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the user's reviews_written count when a review is saved
        self.user.userprofile.reviews_written = Review.objects.filter(user=self.user).count()
        self.user.userprofile.save()
        
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
class BookNote(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='booknotes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    thoughts = models.TextField(blank=True, null=True)
    favorite_characters = models.TextField(blank=True, null=True)
    least_favorite_characters = models.TextField(blank=True, null=True)
    favorite_quote = models.TextField(blank=True, null=True)
    surprising_moment = models.TextField(blank=True, null=True)
    page_number_of_moment = models.PositiveIntegerField(blank=True, null=True)
    ending_opinion = models.TextField(blank=True, null=True)
    
    settings_rating = models.PositiveSmallIntegerField(choices=RATE_CHOICES, blank=True, null=True)
    plot_rating = models.PositiveSmallIntegerField(choices=RATE_CHOICES, blank=True, null=True)
    character_rating = models.PositiveSmallIntegerField(choices=RATE_CHOICES, blank=True, null=True)
    style_rating = models.PositiveSmallIntegerField(choices=RATE_CHOICES, blank=True, null=True)
    engagement_rating = models.PositiveSmallIntegerField(choices=RATE_CHOICES, blank=True, null=True)
    overall_rating = models.PositiveSmallIntegerField(choices=RATE_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    start_date = models.DateTimeField(blank=True, null=True)
    finish_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('book', 'user')

    def __str__(self):
        return f"Review for {self.book.title} by {self.user.username}"
    
def post_user_created_signal(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(post_user_created_signal, sender=User)