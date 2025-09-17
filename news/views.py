from lib2to3.fixes.fix_input import context
from pydoc_data.topics import topics

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

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


class TopicListView(LoginRequiredMixin, generic.ListView):
    model = Topic
    paginate_by = 5
    template_name = "news/topic_list.html"


class TopicDetailView(LoginRequiredMixin, generic.DetailView):
    model = Topic

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["newspapers_of_topic"] = self.object.newspapers.all()
        return context


class TopicCreateView(LoginRequiredMixin, generic.CreateView):
    model = Topic
    fields = "__all__"
    success_url = reverse_lazy("news:topic-list")


class NewspaperListView(LoginRequiredMixin, generic.ListView):
    model = Newspaper
    paginate_by = 5
    template_name = "news/newspaper_list.html"


class NewspaperDetailView(LoginRequiredMixin, generic.DetailView):
    model = Newspaper


class NewspaperCreateView(LoginRequiredMixin, generic.CreateView):
    model = Newspaper
    fields = "all"
    success_url = reverse_lazy("news:newspaper-list")


class RedactorListView(LoginRequiredMixin, generic.ListView):
    model = Redactor
    paginate_by = 5
    template_name = "news/redactor_list.html"


class RedactorDetailView(LoginRequiredMixin, generic.DetailView):
    model = Redactor


class RedactorCreateView(LoginRequiredMixin, generic.CreateView):
    model = Redactor
    fields = "__all__"
    success_url = reverse_lazy("news:redactor-list")
