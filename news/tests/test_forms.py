from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from news.forms import NewspaperForm, NewspaperTopicForm, NewspaperTopicFormSet
from news.models import Newspaper, Topic, NewspaperTopic


class NewspaperFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.u1 = cls.User.objects.create_user(username="alice", password="x")
        cls.u2 = cls.User.objects.create_user(username="bob", password="x")

    def test_fields_present(self):
        form = NewspaperForm()
        self.assertEqual(list(form.fields.keys()), ["title", "content", "publishers"])

    def test_title_is_required(self):
        form = NewspaperForm(data={"title": "", "content": "text", "publishers": [self.u1.id]})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_publishers_allows_multiple_users_and_saves_m2m(self):
        form = NewspaperForm(
            data={
                "title": "My Paper",
                "content": "Hello",
                "publishers": [self.u1.id, self.u2.id],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save(commit=False)
        instance.save()
        form.save_m2m()
        self.assertEqual(instance.title, "My Paper")
        self.assertEqual(instance.content, "Hello")
        self.assertSetEqual(set(instance.publishers.values_list("id", flat=True)), {self.u1.id, self.u2.id})


class NewspaperTopicFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.topic = Topic.objects.create(name="Politics")
        cls.paper = Newspaper.objects.create(title="Daily", content="c")

    def test_fields_present(self):
        form = NewspaperTopicForm()
        self.assertEqual(list(form.fields.keys()), ["content", "topic"])

    def test_both_fields_required(self):
        form = NewspaperTopicForm(data={"content": "", "topic": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)
        self.assertIn("topic", form.errors)

    def test_valid_and_save(self):
        form = NewspaperTopicForm(data={"content": "Section text", "topic": self.topic.id})
        self.assertTrue(form.is_valid(), form.errors)
        nt = form.save(commit=False)
        nt.newspaper = self.paper
        nt.save()
        self.assertEqual(nt.content, "Section text")
        self.assertEqual(nt.topic, self.topic)
        self.assertEqual(nt.newspaper, self.paper)


class NewspaperTopicFormSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.paper = Newspaper.objects.create(title="Weekly", content="")
        cls.t1 = Topic.objects.create(name="Science")
        cls.t2 = Topic.objects.create(name="Economy")
        cls.t3 = Topic.objects.create(name="Sport")

    def _management_data(self, prefix, total, initial=0):
        return {
            f"{prefix}-TOTAL_FORMS": str(total),
            f"{prefix}-INITIAL_FORMS": str(initial),
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }

    def test_create_multiple_children(self):
        prefix = NewspaperTopicFormSet.get_default_prefix()
        data = {
            **self._management_data(prefix, total=2, initial=0),
            f"{prefix}-0-content": "Sci section",
            f"{prefix}-0-topic": str(self.t1.id),
            f"{prefix}-1-content": "Eco section",
            f"{prefix}-1-topic": str(self.t2.id),
        }
        formset = NewspaperTopicFormSet(data=data, instance=self.paper)
        self.assertTrue(formset.is_valid(), formset.errors)
        saved = formset.save()
        self.assertEqual(len(saved), 2)
        self.assertSetEqual(
            set(self.paper.topics.values_list("id", flat=True)),
            {self.t1.id, self.t2.id},
        )

    def test_empty_extra_forms_are_ignored(self):
        prefix = NewspaperTopicFormSet.get_default_prefix()
        data = {
            **self._management_data(prefix, total=2, initial=0),
            f"{prefix}-0-content": "",
            f"{prefix}-0-topic": "",
            f"{prefix}-1-content": "",
            f"{prefix}-1-topic": "",
        }
        formset = NewspaperTopicFormSet(data=data, instance=self.paper)
        self.assertTrue(formset.is_valid(), formset.errors)
        saved = formset.save()
        self.assertEqual(len(saved), 0)
        self.assertEqual(NewspaperTopic.objects.filter(newspaper=self.paper).count(), 0)

    def test_partial_filled_extra_form_is_invalid(self):
        prefix = NewspaperTopicFormSet.get_default_prefix()
        data = {
            **self._management_data(prefix, total=1, initial=0),
            f"{prefix}-0-content": "",
            f"{prefix}-0-topic": str(self.t1.id),
        }
        formset = NewspaperTopicFormSet(data=data, instance=self.paper)
        self.assertFalse(formset.is_valid())
        self.assertIn(0, formset._errors)
        self.assertIn("content", formset._errors[0])

    def test_can_delete_child(self):
        nt1 = NewspaperTopic.objects.create(newspaper=self.paper, topic=self.t1, content="A")
        nt2 = NewspaperTopic.objects.create(newspaper=self.paper, topic=self.t2, content="B")

        prefix = NewspaperTopicFormSet.get_default_prefix()
        data = {
            **self._management_data(prefix, total=2, initial=2),
            f"{prefix}-0-id": str(nt1.id),
            f"{prefix}-0-content": nt1.content,
            f"{prefix}-0-topic": str(nt1.topic_id),
            f"{prefix}-0-DELETE": "on",
            f"{prefix}-1-id": str(nt2.id),
            f"{prefix}-1-content": nt2.content,
            f"{prefix}-1-topic": str(nt2.topic_id),
        }
        formset = NewspaperTopicFormSet(data=data, instance=self.paper)
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()
        self.assertFalse(NewspaperTopic.objects.filter(id=nt1.id).exists())
        self.assertTrue(NewspaperTopic.objects.filter(id=nt2.id).exists())

    def test_unique_together_violation_raises_on_save(self):
        prefix = NewspaperTopicFormSet.get_default_prefix()
        data = {
            **self._management_data(prefix, total=2, initial=0),
            f"{prefix}-0-content": "First",
            f"{prefix}-0-topic": str(self.t3.id),
            f"{prefix}-1-content": "Second duplicate",
            f"{prefix}-1-topic": str(self.t3.id),
        }
        formset = NewspaperTopicFormSet(data=data, instance=self.paper)
        self.assertTrue(formset.is_valid(), formset.errors)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                formset.save()

    def test_edit_existing_child(self):
        nt = NewspaperTopic.objects.create(newspaper=self.paper, topic=self.t1, content="Old")
        prefix = NewspaperTopicFormSet.get_default_prefix()
        data = {
            **self._management_data(prefix, total=1, initial=1),
            f"{prefix}-0-id": str(nt.id),
            f"{prefix}-0-content": "Updated content",
            f"{prefix}-0-topic": str(self.t1.id),
        }
        formset = NewspaperTopicFormSet(data=data, instance=self.paper)
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()
        nt.refresh_from_db()
        self.assertEqual(nt.content, "Updated content")