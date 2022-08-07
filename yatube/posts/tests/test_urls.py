from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_test1')
        cls.not_autor = User.objects.create_user(username='auth_test2')
        cls.group = Group.objects.create(
            title='Тестовая группа1',
            slug='test_slug1',
            description='Тестовое описание1',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост1',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа2',
            slug='test_slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост2',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists(self):
        url_names_codes = [
            (False, reverse('posts:index'), 200),
            (False, reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ), 200),
            (False, reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ), 200),
            (False, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ), 200),
            (False, '/unexisting_page/', 404),
            (True, reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ), 200),
            (True, reverse('posts:post_create'), 200)
        ]
        for items in url_names_codes:
            need_auth, address, code = items
            with self.subTest(address=address):
                if need_auth:
                    response = self.authorized_client.get(address)
                else:
                    response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_pages_uses_correct_template(self):
        templates_pages_names = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ), 'posts/group_list.html'),
            (reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ), 'posts/profile.html'),
            (reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ), 'posts/post_detail.html'),
            (reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ), 'posts/create_post.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
        ]
        for items in templates_pages_names:
            reverse_name, template = items
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_urls_equal_reverse_url(self):
        url_names_reverse_url = {
            '/': reverse('posts:index'),
            f'/group/{self.group.slug}/': reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            f'/profile/{self.user.username}/': reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
            f'/posts/{self.post.id}/': reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ),
            f'/posts/{self.post.id}/edit/': reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ),
            '/create/': reverse('posts:post_create'),
        }
        for address, reverse_url in url_names_reverse_url.items():
            with self.subTest(address=address):
                self.assertEqual(address, reverse_url)

    def test_redirect_unauthorized_client(self):
        redirect_url = [
            (reverse('posts:post_create'),
                (reverse('users:login') + '?next=/create/')),
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
                (reverse('users:login') + '?next=/posts/' + str(self.post.id)
                    + '/edit/')),
        ]
        for items in redirect_url:
            url_to_check, redir_url = items
            with self.subTest(url_to_check=url_to_check):
                response = self.guest_client.get(url_to_check)
                self.assertRedirects(response, redir_url)

    def test_redirect_not_author(self):
        self.authorized_client.force_login(self.not_autor)
        redirect_url = (
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        )
        url_to_check, redir_url = redirect_url
        response = self.authorized_client.get(url_to_check)
        self.assertRedirects(response, redir_url)
