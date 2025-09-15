from django.shortcuts import render
from news.models import Topic, Redactor, Newspaper


def index(request):
    number_of_topics = Topic.objects.count()
    number_of_redactors = Redactor.objects.count()
    number_of_newspapers = Newspaper.objects.count()
    last_published_newspaper = Newspaper.objects.order_by("-published_date").first()

    context = {
        "number_of_topics": number_of_topics,
        "number_of_redactors": number_of_redactors,
        "number_of_newspapers": number_of_newspapers,
        "last_newspaper": last_published_newspaper
    }

    return render(request, "news/index.html", context=context)
