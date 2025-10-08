from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from news.models import Topic, Newspaper, NewspaperTopic


class TopicModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.topic = Topic.objects.create(name="TestTopic")

    def test_name_label(self):
        self.assertEqual(
            self.topic._meta.get_field("name").verbose_name, "name"
        )

    def test_name_max_length(self):
        self.assertEqual(
            self.topic._meta.get_field("name").max_length, 255
        )

    def test_name_unique(self):
        with self.assertRaises(IntegrityError):
            Topic.objects.create(name="TestTopic")

    def test_str(self):
        self.assertEqual(str(self.topic), "TestTopic")

    def test_default_ordering_by_name_asc(self):
        Topic.objects.create(name="AAA")
        Topic.objects.create(name="ZZZ")
        names = list(Topic.objects.values_list("name", flat=True))
        self.assertEqual(names, ["AAA", "TestTopic", "ZZZ"])


class NewspaperModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.topic1 = Topic.objects.create(name="Politics")
        cls.topic2 = Topic.objects.create(name="Science")

        cls.publisher1 = get_user_model().objects.create_user(
            username="alice", password="pass", first_name="Alice", last_name="A"
        )
        cls.publisher2 = get_user_model().objects.create_user(
            username="bob", password="pass", first_name="Bob", last_name="B"
        )

        cls.newspaper = Newspaper.objects.create(
            title="TestTitle", content="This is the test content"
        )
        # through-relations
        NewspaperTopic.objects.create(
            content="Politics section", topic=cls.topic1, newspaper=cls.newspaper
        )
        NewspaperTopic.objects.create(
            content="Science section", topic=cls.topic2, newspaper=cls.newspaper
        )
        cls.newspaper.publishers.add(cls.publisher1, cls.publisher2)

    def test_title_label(self):
        self.assertEqual(
            self.newspaper._meta.get_field("title").verbose_name, "title"
        )

    def test_content_label(self):
        self.assertEqual(
            self.newspaper._meta.get_field("content").verbose_name, "content"
        )

    def test_published_date_label(self):
        self.assertEqual(
            self.newspaper._meta.get_field("published_date").verbose_name, "published date"
        )

    def test_published_date_auto_now_add_sets_today(self):
        self.assertEqual(self.newspaper.published_date, timezone.localdate())

    def test_topics_m2m_through(self):
        topic_names = set(self.newspaper.topics.values_list("name", flat=True))
        self.assertEqual(topic_names, {"Politics", "Science"})

    def test_publishers_m2m(self):
        usernames = set(self.newspaper.publishers.values_list("username", flat=True))
        self.assertEqual(usernames, {"alice", "bob"})

    def test_reverse_related_names_exist(self):
        self.assertIn(self.newspaper, self.topic1.newspapers.all())
        self.assertIn(self.newspaper, self.publisher1.newspapers.all())

    def test_str(self):
        self.assertEqual(str(self.newspaper), "TestTitle")

    def test_default_ordering_by_date_desc_then_title(self):
        n1 = Newspaper.objects.create(title="Alpha")
        n2 = Newspaper.objects.create(title="Charlie")
        n3 = Newspaper.objects.create(title="Bravo")

        titles = list(Newspaper.objects.values_list("title", flat=True))
        self.assertEqual(titles, ["Alpha", "Bravo", "Charlie", "TestTitle"])


class NewspaperTopicModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.topic = Topic.objects.create(name="Economy")
        cls.newspaper = Newspaper.objects.create(title="Daily Post")
        cls.nt = NewspaperTopic.objects.create(
            content="Economy section body",
            topic=cls.topic,
            newspaper=cls.newspaper,
        )

    def test_fields_exist(self):
        self.assertEqual(
            self.nt._meta.get_field("content").get_internal_type(), "TextField"
        )
        self.assertEqual(
            self.nt._meta.get_field("topic").remote_field.model, Topic
        )
        self.assertEqual(
            self.nt._meta.get_field("newspaper").remote_field.model, Newspaper
        )

    def test_unique_together_topic_newspaper(self):
        with self.assertRaises(IntegrityError):
            NewspaperTopic.objects.create(
                content="Duplicate", topic=self.topic, newspaper=self.newspaper
            )

    def test_str(self):
        self.assertEqual(str(self.nt), "Daily Post - Economy")


class RedactorModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            username="jdoe",
            password="password1234",
            first_name="John",
            last_name="Doe",
        )

    def test_model_is_custom_user(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "news.Redactor")
        self.assertTrue(hasattr(self.user, "email"))
        self.assertTrue(hasattr(self.user, "first_name"))
        self.assertTrue(hasattr(self.user, "last_name"))
        self.assertTrue(hasattr(self.user, "username"))

    def test_years_of_experience_default_0(self):
        self.assertEqual(self.user.years_of_experience, 0)

    def test_years_of_experience_min_validator(self):
        user = self.User(
            username="TestName",
            first_name="Test",
            last_name="Name",
            years_of_experience=-1,
        )
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_set_valid_years_of_experience(self):
        self.user.years_of_experience = 5
        self.user.full_clean()
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.years_of_experience, 5)

    def test_str(self):
        self.assertEqual(str(self.user), "(John Doe)")

    def test_reverse_relation_newspapers_related_name(self):
        paper = Newspaper.objects.create(title="Weekly Times")
        paper.publishers.add(self.user)
        self.assertIn(paper, self.user.newspapers.all())