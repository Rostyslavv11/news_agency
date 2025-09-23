from django import forms
from django.forms import inlineformset_factory

from news.models import NewspaperTopic, Newspaper


class NewspaperForm(forms.ModelForm):
    class Meta:
        model = Newspaper
        fields = ["title", "content", "publishers"]


class NewspaperTopicForm(forms.ModelForm):
    class Meta:
        model = NewspaperTopic
        fields = ["content", "topic"]


NewspaperTopicFormSet = inlineformset_factory(
    parent_model=Newspaper,
    model=NewspaperTopic,
    form=NewspaperTopicForm,
    fk_name="newspaper",
    extra=2,
    can_delete=True,
)
