from typing import Any
import random
import json
from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, reverse, redirect
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.edit import FormView
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import (
    Book, 
    BookRequest,
    UserProfile, 
    Review, 
    Author, 
    Genre, 
    BookProgress, 
    BookNote,
    Notification,
)
from .forms import (
    CustomUserCreationForm, 
    NewReviewForm, 
    UserProfileForm, 
    BookForm, 
    BookNoteForm,
    BookRequestForm,
    BookRequestApprovalForm,
)

class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse("login")

class BookSearchView(generic.ListView):
    model = Book
    template_name = "book/search_results.html"
    context_object_name = 'books'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('search_query')
        if query:
            # Use Q objects to search in both title and author fields
            return Book.objects.filter(Q(title__icontains=query) | Q(author__name__icontains=query))
        return Book.objects.none()
        
    
class BookListView(generic.ListView):
    model = Book
    template_name = 'book/book_list.html'
    context_object_name = 'books'
    paginate_by = 21
    
    def get_queryset(self):
        # Get the total number of books in the database
        total_books = Book.objects.count()

        # Initialize an empty list to store unique random indexes
        random_indexes = []

        # Generate random indexes until we have 21 unique ones
        while len(random_indexes) < 21:
            random_index = random.randint(1, total_books)
            if random_index not in random_indexes:
                random_indexes.append(random_index)

        # Fetch the books corresponding to the random indexes
        random_books = Book.objects.filter(pk__in=random_indexes)

        return random_books
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_reviews'] = Review.objects.order_by('-publish')[:5]
        
        all_genres = Genre.objects.all()
        random_genres = random.sample(list(all_genres), 5)
        genre_books = {} 
        for genre in random_genres:
            genre_books[genre] = Book.objects.filter(genres=genre)[:10]

        context['genre_books'] = genre_books
        return context

class BookActionMixin:
    def update_book_progress(self, progress, new_page_number, book):
        if new_page_number >= 0 and new_page_number <= book.page_count:
            user_profile = UserProfile.objects.get(user=progress.user)
            user_profile.total_pages_read -= progress.page_number
            progress.page_number = new_page_number
            user_profile.total_pages_read += progress.page_number
            if new_page_number == book.page_count:
                progress.status = 'completed'
            else:
                progress.status = 'reading'
            progress.save()
            user_profile.save()
            
    def mark_completed(self, progress, book):
        user_profile = UserProfile.objects.get(user=progress.user)
        user_profile.total_pages_read -= progress.page_number
        progress.page_number = book.page_count
        user_profile.total_pages_read += book.page_count
        progress.status = 'completed'
        progress.save()
        user_profile.save()

    def mark_dropped(self, progress):
        progress.status = 'dropped'
        progress.save()
                
    def calculate_book_progress(self, user, book):
        if user.is_authenticated:
            reading_progress = user.bookprogress_set.filter(book=book).first()
            if reading_progress:
                return reading_progress
        return None    
    


class BookshelfListView(LoginRequiredMixin, generic.ListView):
    model = BookProgress
    template_name = 'book/book_shelf.html'
    context_object_name = 'bookshelf_list'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reading_books = context['bookshelf_list'].filter(status='reading')
        completed_books = context['bookshelf_list'].filter(status='completed')
        dropped_books = context['bookshelf_list'].filter(status='dropped')
        
        context = {
            'reading_books': reading_books,
            'completed_books': completed_books,
            'dropped_books': dropped_books,
        }
        return context
    
    def get_queryset(self):
        user = self.request.user
        return BookProgress.objects.filter(user=user)

class BookDetailView(LoginRequiredMixin, BookActionMixin, generic.DetailView):
    model=Book
    template_name = "book/book_detail.html"
    context_object_name = "book"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = NewReviewForm()
        
        if self.request.user.is_authenticated:
            user = self.request.user
            progress = self.calculate_book_progress(user, context['book'])
            if progress is None:
                progress = BookProgress.objects.create(user=user, book=context['book'], page_number=0)
            context['progress'] = progress
            
            completion_percentage = (progress.page_number / context['book'].page_count) * 100
            context['completion_percentage'] = completion_percentage
            context['is_favorite'] = context['book'].favorites.filter(id=user.userprofile.pk).exists()
            
        return context
    
    def post(self, request, *args, **kwargs):
        book_id = kwargs['pk']
        user = request.user
        
        if not user.is_authenticated:
            return redirect(reverse('login'))
        
        # if 'rating' in request.POST:
        #     if user.is_authenticated:
        #         rating_value = int(request.POST['rating'])
        #         rating, created = Rating.objects.update_or_create(book_id=book_id, user=user, defaults={'rating': rating_value})
        #         if created:
        #             rating.rating = rating_value
        #         else:
        #             rating.rating = rating_value
        #             rating.save()
            
        if 'content' in request.POST:
            form = NewReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.book_id = book_id
                review.user = user
                review.save()
                
                review_html = render_to_string("book/review_item.html", {"review": review})
                        
                return JsonResponse({"review_html": review_html}) 
        
        new_page_number = int(request.POST.get('new_page_number', 0))
        book = get_object_or_404(Book, id=book_id)
        progress, created = BookProgress.objects.get_or_create(book=book, user=user)
        
        if 'update_page_number' in request.POST:
            self.update_book_progress(progress, new_page_number, book)

        elif 'mark_completed' in request.POST:
            self.mark_completed(progress, book)

        elif 'mark_dropped' in request.POST:
            self.mark_dropped(progress)
        
        return redirect('book:book-detail', pk=book_id)
            
    # def get_user_rating(self, user, book):
    #     try:
    #         rating = Rating.objects.get(book=book, user=user)
    #         return rating.rating
    #     except Rating.DoesNotExist:
    #         return None   
    
class UserProfileView(LoginRequiredMixin, generic.ListView):
    model = UserProfile
    template_name = 'book/user_profile.html'
    context_object_name = 'user_profile'

    def get_object(self, queryset=None):
        return self.request.user.userprofile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.get_object()
        user = self.request.user
        context['user_favorite_books'] = user_profile.favorite.all()
        
        reading_count = BookProgress.objects.filter(user=user, status='reading').count()
        completed_count = BookProgress.objects.filter(user=user, status='completed').count()
        dropped_count = BookProgress.objects.filter(user=user, status='dropped').count()

        context['reading_count'] = reading_count
        context['completed_count'] = completed_count
        context['dropped_count'] = dropped_count
        
        context['status_counts'] = f"{reading_count},{completed_count},{dropped_count}"
        return context

class UserDetailView(generic.DetailView):
    model = UserProfile
    template_name = 'book/user_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        username = self.kwargs['username']
        user = get_object_or_404(User, username=username)
        return user.userprofile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = context['profile']

        # Fetch additional data here
        user_favorite_books = user_profile.favorite.all()

    # Fetch reading, completed, and dropped counts for the user_profile
        reading_count = BookProgress.objects.filter(user=user_profile.user, status='reading').count()
        completed_count = BookProgress.objects.filter(user=user_profile.user, status='completed').count()
        dropped_count = BookProgress.objects.filter(user=user_profile.user, status='dropped').count()

        context['user_favorite_books'] = user_favorite_books
        context['reading_count'] = reading_count
        context['completed_count'] = completed_count
        context['dropped_count'] = dropped_count
        context['status_counts'] = f"{reading_count},{completed_count},{dropped_count}"

        return context

class UserProfileUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'book/user_settings.html'
    success_url = reverse_lazy('book:user-profile')
    
    
    def get_object(self, queryset=None):
        return self.request.user.userprofile

@csrf_exempt
@login_required
def favorite_add(request, id):
    book = get_object_or_404(Book, id=id)
    
    user_profile = UserProfile.objects.get(user=request.user)
    
    if book.favorites.filter(id=user_profile.pk).exists():
        book.favorites.remove(user_profile)
        is_favorite = False
    else:
        book.favorites.add(user_profile)
        is_favorite=True
        
    return JsonResponse({"is_favorite": is_favorite})


@login_required
def change_role_to_reviewer(request):
    user = request.user
    user_profile = user.userprofile

    # Check if the user has met the threshold (e.g., written at least 2 reviews)
    if user_profile.reviews_written >= 2:
        user.is_reviewer = True
        user.save()  # Save the updated profile
        return JsonResponse({'message': 'Congratulations! You are now a reviewer.', 'hideForm': True})
    else:
        remaining_reviews = 2 - user_profile.reviews_written
        message = f'Sorry, you need to write {remaining_reviews} more reviews to become a reviewer.'
        return JsonResponse({'message': message, 'hideForm': False})

class BookCreateView(LoginRequiredMixin, generic.CreateView):
    model = Book
    form_class = BookForm
    template_name = 'book/create_book.html'
    
    success_url = '/'
    def form_valid(self, form):
        title = form.cleaned_data.get('title')
        author = form.cleaned_data.get('author')

        # Check if both title and author are not None
        if title is not None:
    # Normalize the input title for case-insensitive search
            normalized_title = title.lower()

            # Check if a book with the same normalized title exists
            existing_book = Book.objects.filter(title__iexact=normalized_title).first()

            if existing_book:
                # Redirect the user to the existing book's detail page
                return redirect('book:book-detail', pk=existing_book.pk)
        
# If title or author is None or a matching book doesn't exist, create a new book
        form.instance.image_local = self.request.FILES.get('image_local')
        response = super().form_valid(form)
        # Create a notification for the newly created book
        Notification.objects.create(book=self.object)
        return response

class BookUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'book/book_update.html'
    
    def get_success_url(self):
        return reverse_lazy('book:book-detail', args=[self.object.pk])

    def form_valid(self, form):
        new_image = self.request.FILES.get('image_local')
        new_pdf = self.request.FILES.get('pdf_file')

        # Set the 'image_local' field of the form instance
        if new_image:
            form.instance.image_local = new_image
        else:
            existing_book = Book.objects.get(pk=self.object.pk)
            form.instance.image_local = existing_book.image_local

        # Set the 'pdf_file' field of the form instance
        if new_pdf:
            form.instance.pdf_file = new_pdf
        else:
            existing_book = Book.objects.get(pk=self.object.pk)
            form.instance.pdf_file = existing_book.pdf_file

        return super().form_valid(form)
    
    
class BookNoteCreateView(LoginRequiredMixin, generic.CreateView):
    model = BookNote
    form_class = BookNoteForm
    template_name = 'book/booknote_form.html'
    success_url = reverse_lazy('book:user-profile')

    def form_valid(self, form):
        # Get the book_id from the URL parameters
        book_id = self.kwargs['book_id']
        
        # Ensure that the book with the given book_id exists
        book = get_object_or_404(Book, pk=book_id)

        # Set the user and book fields for the BookNote
        form.instance.user = self.request.user
        form.instance.book = book

        return super().form_valid(form)

    def get_success_url(self):
    # Get the book_id and pk from the URL parameters
        book_id = self.kwargs['book_id']
        pk = self.object.pk
        return reverse_lazy('book:view_booknote', kwargs={'book_id': book_id, 'pk': pk})

class BookNoteUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = BookNote
    form_class = BookNoteForm
    template_name = 'book/booknote_form.html'
    
    def get_success_url(self):
        # Get the book_id and pk from the URL parameters
        book_id = self.kwargs['book_id']
        pk = self.kwargs['pk']
        return reverse_lazy('book:view_booknote', kwargs={'book_id': book_id, 'pk': pk})

class BookNoteDetailView(LoginRequiredMixin, generic.DetailView):
    model = BookNote
    template_name = 'book/booknote_detail.html'
    context_object_name = 'booknote'
    
class BookNoteListView(LoginRequiredMixin, generic.ListView):
    model = BookNote
    template_name = 'book/user_notes.html'  # Create this template
    context_object_name = 'booknotes'
    
    def get_queryset(self):
        # Filter BookNotes by the currently logged-in user
        return BookNote.objects.filter(user=self.request.user)

#################################################
class BookRequestListView(LoginRequiredMixin, generic.ListView):
    model = BookRequest
    template_name = 'book/book_request_list.html'
    context_object_name = 'book_requests'

    def get_queryset(self):
        return BookRequest.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class BookRequestFormView(LoginRequiredMixin, FormView):
    form_class = BookRequestForm
    template_name = 'book/book_request_form.html'  # Replace with your actual template name
    success_url = reverse_lazy('book:request_list')  # Redirect back to the list after form submission

    def form_valid(self, form):
        book_request = form.save(commit=False)
        book_request.user = self.request.user
        book_request.save()
        return super().form_valid(form)

class ReviewerBookRequestListView(LoginRequiredMixin, generic.ListView):
    model = BookRequest
    template_name = 'book/reviewer_book_request_list.html'
    context_object_name = 'book_requests'

    def get_queryset(self):
        # Filter requests with a "pending" status
        return BookRequest.objects.filter(status='pending')

    def get_queryset(self):
        # Filter requests with a "pending" status
        return BookRequest.objects.filter(status='pending')

    def post(self, request, *args, **kwargs):
        request_id = request.POST.get('request_id')
        if request_id:
            book_request = BookRequest.objects.filter(id=request_id, status='pending').first()
            if book_request:
                # Check if the request is for approval or denial
                if 'approve' in request.POST:
                    book_request.status = 'approved'
                    book_request.approval_message = f'Request for {book_request.title} has been approved.'  # Get the approval message from the form  # Set the approval message
                    book_request.approval_message_timestamp = timezone.now()
                    messages.success(request, f'Request for "{book_request.title}" has been approved.')
                elif 'deny' in request.POST:
                    book_request.status = 'denied'
                    
                    book_request.denial_message = f'Request for {book_request.title} has been denied.'   # Set the denial message
                    book_request.denial_message_timestamp = timezone.now()
                    messages.success(request, f'Request for "{book_request.title}" has been denied.')

                book_request.save()
        return redirect('book:reviewer_request_list')
#############################################################
class NotificationListView(LoginRequiredMixin, generic.ListView):
    model = Notification
    template_name = 'book/notification_list.html'
    context_object_name = 'notifications'
    
    def get_queryset(self):
        # Retrieve and order notifications by creation time (newest first)
        return Notification.objects.all().order_by('-created_at')

class PDFViewerView(generic.TemplateView):
    template_name = 'book/pdf_viewer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book_id = kwargs.get('book_id')
        book = Book.objects.get(pk=book_id)
        context['book'] = book
        return context