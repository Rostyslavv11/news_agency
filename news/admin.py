from django.contrib import admin
from news.models import Topic, Newspaper, Redactor, NewspaperTopic


@admin.register(Topic)
class AdminTopic(admin.ModelAdmin):
    search_fields = ("name",)
    pass


class NewspaperTopicInlineAdmin(admin.TabularInline):
    model = NewspaperTopic
    extra = 1
    autocomplete_fields = ("topic",)
    fields = ("topic", "content")


@admin.register(Newspaper)
class NewspaperAdmin(admin.ModelAdmin):
    list_display = ["title", "published_date"]
    inlines = [NewspaperTopicInlineAdmin]


@admin.register(Redactor)
class RedactorAdmin(admin.ModelAdmin):
    list_display = ["username", "last_name"]
