import shutil
import tempfile

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..models import Group, Post, Follow
from ..forms import PostForm, CommentForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_test1')
        cls.author = User.objects.create_user(username='author1')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug1',
            description='Тестовое описание 1',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост 1',
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_show_correct_context(self):
        pages_context = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
        ]
        for items in pages_context:
            with self.subTest(items=items):
                response = self.guest_client.get(items)
                self.assertIn(self.post, response.context['page_obj'])

    def test_post_detail_show_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'], self.post)

    def test_post_edit_show_correct_form(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form = response.context['form']
        self.assertIsInstance(form, PostForm)
        self.assertEqual(form.instance, self.post)

    def test_post_create_show_correct_form(self):
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_detail_show_comment_form(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIsInstance(response.context['form'], CommentForm)

    def test_create_follow(self):
        follow_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author,
            ).exists()
        )

    def test_user_unfollow(self):
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        follow_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author,
            ).exists()
        )

    def test_cache(self):
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        Post.objects.all().delete()
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        self.assertEqual(posts, old_posts)

        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(posts, new_posts)
