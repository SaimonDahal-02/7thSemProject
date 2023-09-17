from django.contrib import admin
from . import models

admin.site.register(models.User)
admin.site.register(models.UserProfile)
admin.site.register(models.Book)

admin.site.register(models.Review)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = ("book", "user", "publish", "status")
#     list_filter = ("status", "pubish")
#     search_fields = ("book", "user", "content")