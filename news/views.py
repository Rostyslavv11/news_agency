from lib2to3.fixes.fix_input import context

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

from news.models import Topic, Redactor, Newspaper
from .forms import NewspaperForm, NewspaperTopicFormSet, TopicSearchForm, NewspaperSearchForm, RedactorSearchForm


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
    context_object_name = "topic_list"

    def get_queryset(self):
        qs = Topic.objects.all()
        name = self.request.GET.get("name")
        if name:
            return qs.filter(name__icontains=name)
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_form"] = TopicSearchForm(
            self.request.GET
        )
        return context

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
    template_name = "news/topic_form.html"


class TopicUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Topic
    fields = "__all__"
    template_name = "news/topic_form.html"
    success_url = reverse_lazy("news:topic-list")


class TopicDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Topic
    template_name = "news/topic_confirm_delete.html"
    success_url = reverse_lazy("news:topic-list")


class NewspaperListView(LoginRequiredMixin, generic.ListView):
    model = Newspaper
    paginate_by = 5
    template_name = "news/newspaper_list.html"

    def get_queryset(self):
        qs = Newspaper.objects.all()
        title = self.request.GET.get("title")
        if title:
            return qs.filter(title__icontains=title)
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_form"] = NewspaperSearchForm(
            self.request.GET or None
        )
        return context

class NewspaperDetailView(LoginRequiredMixin, generic.DetailView):
    model = Newspaper

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["can_edit"] = (
                user.is_authenticated
                and self.object.publishers.filter(pk=user.pk).exists()
        )
        return context


class NewspaperCreateView(LoginRequiredMixin, generic.CreateView):
    model = Newspaper
    form_class = NewspaperForm
    success_url = reverse_lazy("news:newspaper-list")
    template_name = "news/newspaper_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = NewspaperTopicFormSet(self.request.POST or None)
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return redirect(self.get_success_url())
        return self.form_invalid(form)

class NewspaperUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Newspaper
    form_class = NewspaperForm
    template_name = "news/newspaper_form.html"
    success_url = reverse_lazy("news:newspaper-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = NewspaperTopicFormSet(self.request.POST or None, instance=self.object)
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        if formset.is_valid():
            self.object = form.save()
            formset.save()
            return redirect(self.get_success_url())
        return self.form_invalid(form)


class NewspaperDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Newspaper
    template_name = "news/newspaper_confirm_delete.html"
    success_url = reverse_lazy("news:newspaper-list")


class RedactorListView(LoginRequiredMixin, generic.ListView):
    model = Redactor
    paginate_by = 5
    template_name = "news/redactor_list.html"
    ordering = ["username"]

    def get_queryset(self):
        qs = Redactor.objects.all()
        username = self.request.GET.get("username")
        if username:
            return qs.filter(username__icontains=username)
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_form"] = RedactorSearchForm(
            self.request.GET or None
        )
        return context


class RedactorDetailView(LoginRequiredMixin, generic.DetailView):
    model = Redactor
