from django.contrib import admin
from models import Topic, Newspaper, Redactor


@admin.register(Topic)
class AdminTopic(admin.ModelAdmin):
    pass


@admin.register(Newspaper)
class AdminNewspaper(admin.ModelAdmin):
    list_display = ["title", "published_date"]


@admin.register(Redactor)
class RedactorAdmin(admin.ModelAdmin):
    list_display = ["username", "last_name"]


