from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from news.models import Topic, Newspaper, NewspaperTopic


class BaseViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.password = "pass12345"
        cls.user = cls.User.objects.create_user(
            username="john",
            password=cls.password,
            first_name="John",
            last_name="Doe",
        )

        cls.t1 = Topic.objects.create(name="Politics")
        cls.t2 = Topic.objects.create(name="Science")

        cls.n1 = Newspaper.objects.create(title="Alpha", content="A")
        cls.n2 = Newspaper.objects.create(title="Beta", content="B")
        cls.n3 = Newspaper.objects.create(title="Gamma", content="C")
        cls.n1.publishers.add(cls.user)

        NewspaperTopic.objects.create(newspaper=cls.n1, topic=cls.t1, content="politics part")
        NewspaperTopic.objects.create(newspaper=cls.n2, topic=cls.t2, content="science part")

    def login(self):
        self.client.login(username=self.user.username, password=self.password)

    def _mgmt(self, prefix, total, initial=0):
        return {
            f"{prefix}-TOTAL_FORMS": str(total),
            f"{prefix}-INITIAL_FORMS": str(initial),
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }


class IndexViewTest(BaseViewTest):
    def test_index_context_counts_and_last_newspaper(self):
        url = reverse("news:index")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["number_of_topics"], Topic.objects.count())
        self.assertEqual(resp.context["number_of_redactors"], get_user_model().objects.count())
        self.assertEqual(resp.context["number_of_newspapers"], Newspaper.objects.count())
        self.assertEqual(resp.context["last_newspaper"], Newspaper.objects.order_by("-published_date").first())


class AuthRequiredTest(BaseViewTest):
    def test_anonymous_redirected_to_login_for_protected_views(self):
        protected_urls = [
            reverse("news:topic-list"),
            reverse("news:topic-detail", args=[self.t1.id]),
            reverse("news:topic-create"),
            reverse("news:topic-update", args=[self.t1.id]),
            reverse("news:topic-delete", args=[self.t1.id]),
            reverse("news:newspaper-list"),
            reverse("news:newspaper-detail", args=[self.n1.id]),
            reverse("news:newspaper-create"),
            reverse("news:newspaper-update", args=[self.n1.id]),
            reverse("news:newspaper-delete", args=[self.n1.id]),
            reverse("news:redactor-list"),
            reverse("news:redactor-detail", args=[self.user.id]),
        ]
        for url in protected_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(settings.LOGIN_URL, resp.url)


class TopicViewsTest(BaseViewTest):
    def test_topic_list_paginates_by_5(self):
        for i in range(6):
            Topic.objects.create(name=f"T{i}")
        self.login()
        url = reverse("news:topic-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["is_paginated"])
        self.assertLessEqual(len(resp.context["object_list"]), 5)

    def test_topic_detail_includes_newspapers_of_topic(self):
        self.login()
        url = reverse("news:topic-detail", args=[self.t1.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("newspapers_of_topic", resp.context)
        self.assertIn(self.n1, resp.context["newspapers_of_topic"])

    def test_topic_create_update_delete(self):
        self.login()
        # create
        create_url = reverse("news:topic-create")
        resp = self.client.post(create_url, data={"name": "Economy"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        created = Topic.objects.get(name="Economy")

        # update
        update_url = reverse("news:topic-update", args=[created.id])
        resp = self.client.post(update_url, data={"name": "Business"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        created.refresh_from_db()
        self.assertEqual(created.name, "Business")

        # delete
        delete_url = reverse("news:topic-delete", args=[created.id])
        resp = self.client.post(delete_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Topic.objects.filter(id=created.id).exists())


class NewspaperViewsTest(BaseViewTest):
    def test_newspaper_list_paginates_by_5(self):
        for i in range(7):
            Newspaper.objects.create(title=f"N{i}", content="x")
        self.login()
        url = reverse("news:newspaper-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["is_paginated"])
        self.assertLessEqual(len(resp.context["object_list"]), 5)

    def test_newspaper_detail_ok(self):
        self.login()
        url = reverse("news:newspaper-detail", args=[self.n1.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["object"], self.n1)

    def test_newspaper_create_with_formset(self):
        self.login()
        url = reverse("news:newspaper-create")
        prefix = "newspapertopic_set"
        post_data = {
            "title": "Daily News",
            "content": "Body",
            "publishers": [self.user.id],
            **self._mgmt(prefix, total=2, initial=0),
            f"{prefix}-0-content": "Politics part",
            f"{prefix}-0-topic": str(self.t1.id),
            f"{prefix}-1-content": "Science part",
            f"{prefix}-1-topic": str(self.t2.id),
        }
        resp = self.client.post(url, data=post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        created = Newspaper.objects.get(title="Daily News")
        self.assertSetEqual(set(created.publishers.values_list("id", flat=True)), {self.user.id})
        self.assertSetEqual(set(created.topics.values_list("id", flat=True)), {self.t1.id, self.t2.id})

    def test_newspaper_create_with_invalid_formset_returns_form(self):
        self.login()
        url = reverse("news:newspaper-create")
        prefix = "newspapertopic_set"
        post_data = {
            "title": "Broken",
            "content": "X",
            "publishers": [self.user.id],
            **self._mgmt(prefix, total=1, initial=0),
            f"{prefix}-0-content": "",
            f"{prefix}-0-topic": str(self.t1.id),
        }
        resp = self.client.post(url, data=post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "news/newspaper_form.html")
        self.assertFalse(Newspaper.objects.filter(title="Broken").exists())

    def test_newspaper_update_with_formset_add_and_delete(self):
        self.login()
        url = reverse("news:newspaper-update", args=[self.n1.id])
        existing = NewspaperTopic.objects.get(newspaper=self.n1, topic=self.t1)
        prefix = "newspapertopic_set"
        post_data = {
            "title": self.n1.title,
            "content": "Updated A",
            "publishers": [self.user.id],
            **self._mgmt(prefix, total=2, initial=1),

            f"{prefix}-0-id": str(existing.id),
            f"{prefix}-0-content": existing.content,
            f"{prefix}-0-topic": str(existing.topic_id),
            f"{prefix}-0-DELETE": "on",

            f"{prefix}-1-content": "New science part",
            f"{prefix}-1-topic": str(self.t2.id),
        }
        resp = self.client.post(url, data=post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.n1.refresh_from_db()
        self.assertEqual(self.n1.content, "Updated A")
        self.assertFalse(NewspaperTopic.objects.filter(id=existing.id).exists())
        self.assertTrue(NewspaperTopic.objects.filter(newspaper=self.n1, topic=self.t2).exists())

    def test_newspaper_delete(self):
        self.login()
        url = reverse("news:newspaper-delete", args=[self.n2.id])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Newspaper.objects.filter(id=self.n2.id).exists())


class RedactorViewsTest(BaseViewTest):
    def test_redactor_list_and_detail(self):
        self.login()
        list_url = reverse("news:redactor-list")
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.user, resp.context["object_list"])

        detail_url = reverse("news:redactor-detail", args=[self.user.id])
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["object"], self.user)