
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import (
    LoginView,
    LogoutView, 
)
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from book.views import SignupView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('book.urls', 'book'), namespace="books")),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'), 
    
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="registration/password_reset.html"), 
         name="reset_password"),
    
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_sent.html"), 
         name="password_reset_done"),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_form.html"), 
         name="password_reset_confirm"),
    
    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_done.html"), 
         name="password_reset_complete"),
  
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
