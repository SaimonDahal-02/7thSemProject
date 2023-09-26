from django.urls import path

from . views import (
    BookListView, 
    BookSearchView,
    BookshelfListView, 

                     
    UserProfileView, 
    UserProfileUpdateView,
    UserDetailView, 
                     
    BookCreateView, 
    BookUpdateView,
    BookDetailView, 
                     
    BookNoteCreateView, 
    BookNoteUpdateView,
    BookNoteDetailView, 
    BookNoteListView,
    
    BookRequestListView,
    BookRequestFormView,
    ReviewerBookRequestListView,
    
    NotificationListView,
    
    PDFViewerView,
    
    favorite_add, 
    change_role_to_reviewer,
    books_api,
    
    RecommendBooksView, 
)

app_name = "book"

urlpatterns = [
    path('', BookListView.as_view(), name="book-list"),
    path('search/', BookSearchView.as_view(), name="book-search"),
    path('book/<int:pk>/', BookDetailView.as_view(), name="book-detail"),
    path('book/update/<int:pk>/', BookUpdateView.as_view(), name="book-update"),
    
    path('bookshelf/', BookshelfListView.as_view(), name="book-shelf"),
    
    path('profile/', UserProfileView.as_view(), name="user-profile"),
    path('userprofile/update/', UserProfileUpdateView.as_view(), name='edit-profile'),
    path('profile/<str:username>/', UserDetailView.as_view(), name='user_detail'),
    
    path('books/<int:book_id>/create_note/', BookNoteCreateView.as_view(), name='create_booknote'),
    path('books/<int:book_id>/update_note/<int:pk>/', BookNoteUpdateView.as_view(), name='update_booknote'),
    path('books/<int:book_id>/view_note/<int:pk>/', BookNoteDetailView.as_view(), name='view_booknote'),
    path('booknotes/', BookNoteListView.as_view(), name='booknote_list'),
    
    path('change-role-to-reviewer/', change_role_to_reviewer, name='change_role_to_reviewer'),
    path('fav/<int:id>/', favorite_add, name='favorite_add'),
    path('add/', BookCreateView.as_view(), name='add_book'),
    
    path('book_request_list/', BookRequestListView.as_view(), name='request_list'),
    path('request/', BookRequestFormView.as_view(), name='request_form'),
    path('reviewer-requests/', ReviewerBookRequestListView.as_view(), name='reviewer_request_list'),  
    
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    
    path('pdf_viewer/<int:book_id>/', PDFViewerView.as_view(), name='pdf_viewer'),
    
    path('api/books/', books_api, name='books-api'),
    
    path('recommendations/', RecommendBooksView.as_view(), name='recommendations'),
    # path('review/edit/<int:review_id>/', edit_review, name='edit_review'),
    # path('review/delete/<int:review_id>/', delete_review, name='delete_review'),
]