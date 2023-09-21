from django import forms
from .models import (
    User, 
    Review, 
    UserProfile, 
    Book, 
    Author, 
    Genre, 
    BookNote,
    BookRequest,
)
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username","email")
        field_classes = {'username': UsernameField}

class NewReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(attrs={'rows': 4}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "bio",
            "profile_pic",
            "sex",
            "favorite_genre",
            "favorite_author",
            "profession",
            "facebook_url",
            "instagram_url",
            "website_url",
            "twitter_url",
            ]
        
class BookForm(forms.ModelForm):
    new_author = forms.CharField(max_length=100, label="Add Author", required=False)
    new_genre = forms.CharField(max_length=100, label="Add Genre", required=False)

    class Meta:
        model = Book
        fields = [
            'isbn',
            'title',
            'description',
            'publisher',
            'publication_year',
            'image_local',
            'pdf_file',
            'page_count',
            'language',
        ]
        widgets = {
            'image_local': forms.FileInput(attrs={'accept': 'image/*'}),
            'pdf_file': forms.FileInput(attrs={'accept': 'application/pdf'}),
        }
        enctype = 'multipart/form-data'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image_local'].required = False
        self.fields['pdf_file'].required = False


    def save(self, commit=True):
        instance = super(BookForm, self).save(commit=False)

        new_author = self.cleaned_data.get('new_author')
        new_genre = self.cleaned_data.get('new_genre')

        if commit:
            instance.save()  # Save the instance to the database first

        if new_author:
            authors = [author.strip() for author in new_author.split(',')]
            for author_name in authors:
                author, created = Author.objects.get_or_create(name=author_name)
                instance.author.add(author)

        if new_genre:
            genres = [genre.strip() for genre in new_genre.split(',')]
            for genre_name in genres:
                genre, created = Genre.objects.get_or_create(name=genre_name)
                instance.genres.add(genre)

        return instance

class BookNoteForm(forms.ModelForm):
    class Meta:
        model = BookNote
        fields = [
            'thoughts', 
            'favorite_characters', 
            'least_favorite_characters', 
            'favorite_quote', 
            'surprising_moment', 
            'page_number_of_moment', 
            'ending_opinion', 
            'start_date', 
            'settings_rating',
            'plot_rating',
            'character_rating',
            'style_rating',
            'engagement_rating',
            'overall_rating',
            'finish_date'
            ]


class BookRequestForm(forms.ModelForm):
    class Meta:
        model = BookRequest
        fields = ['title', 'author','additional_info']  # Include any additional fields you need

    # Additional fields not present in the model
    additional_info = forms.CharField(widget=forms.Textarea, required=False)  # You can add any additional fields as needed
    
class BookRequestApprovalForm(forms.Form):
    DECISION_CHOICES = (
        ('add', 'Add'),
        ('deny', 'Deny'),
    )

    request_id = forms.IntegerField(widget=forms.HiddenInput)
    decision = forms.ChoiceField(choices=DECISION_CHOICES)





