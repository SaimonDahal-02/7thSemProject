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
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin


from .models import (
    Book, 
    UserProfile, 
    Review, 
    Author, 
    Genre, 
    BookProgress, 
    BookNote,
)
from .forms import (
    CustomUserCreationForm, 
    NewReviewForm, 
    UserProfileForm, 
    BookForm, 
    BookNoteForm,
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
    


class BookshelfListView(generic.ListView):
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

class BookDetailView(BookActionMixin, generic.DetailView):
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
    
class UserProfileView(generic.ListView):
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

class UserProfileUpdateView(generic.UpdateView):
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

class BookCreateView( generic.CreateView):
    model = Book
    form_class = BookForm
    template_name = 'book/create_book.html'
    
    success_url = '/'
    def form_valid(self, form):
        # Pass both request.POST and request.FILES to the form
        form.instance.image_local = self.request.FILES.get('image_local')
        return super().form_valid(form)

class BookUpdateView(generic.UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'book/book_update.html'
    
    def get_success_url(self):
        return reverse_lazy('book:book-detail', args=[self.object.pk])

    def form_valid(self, form):
            # Set the 'image_local' field of the form instance
            form.instance.image_local = self.request.FILES.get('image_local')
            return super().form_valid(form)
    
    

class BookNoteCreateView(generic.CreateView):
    model = BookNote
    form_class = BookNoteForm
    template_name = 'book/booknote_form.html'
    success_url = reverse_lazy('book:user-profile')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.book = Book.objects.get(pk=self.kwargs['book_id'])
        return super().form_valid(form)

    def get_success_url(self):
    # Get the book_id and pk from the URL parameters
        book_id = self.kwargs['book_id']
        pk = self.object.pk
        return reverse_lazy('book:view_booknote', kwargs={'book_id': book_id, 'pk': pk})

class BookNoteUpdateView(generic.UpdateView):
    model = BookNote
    form_class = BookNoteForm
    template_name = 'book/booknote_form.html'
    
    def get_success_url(self):
        # Get the book_id and pk from the URL parameters
        book_id = self.kwargs['book_id']
        pk = self.kwargs['pk']
        return reverse_lazy('book:view_booknote', kwargs={'book_id': book_id, 'pk': pk})

class BookNoteDetailView(generic.DetailView):
    model = BookNote
    template_name = 'book/booknote_detail.html'
    context_object_name = 'booknote'
    
class BookNoteListView(generic.ListView):
    model = BookNote
    template_name = 'book/user_notes.html'  # Create this template
    context_object_name = 'booknotes'