from math import ceil

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings

from ..models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_test2')
        cls.group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание 2',
        )
        cls.NUM_POSTS_TEST = 13
        cls.page = ceil(cls.NUM_POSTS_TEST / settings.NUM_POSTS)
        cls.last_page_posts = (
            cls.NUM_POSTS_TEST - (cls.page - 1) * settings.NUM_POSTS
        )
        for number in range(cls.NUM_POSTS_TEST):
            Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'Тестовый пост {number}',
            )

    def setUp(self):
        self.guest_client = Client()

    def test_first_last_page_contains(self):
        pages_context = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        )
        for reverse_name in pages_context:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), settings.NUM_POSTS
                )
                response = self.guest_client.get(
                    f'{reverse_name}?page={self.page}'
                )
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.last_page_posts
                )
