from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Укажите название группы'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Часть ссылки на группу',
        help_text='Укажите часть url'
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Заполниите описание группы'
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    LEN_POST = 15
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Напишите пост'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата поста',
        help_text='Укажите дату'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор поста',
        help_text='Назовите автора'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        help_text='Загрузите картинку',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:self.LEN_POST]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментируемый пост',
        help_text='Комментируемый пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
        help_text='Назовите автора комментария'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Напишите комментарий к посту'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата поста',
        help_text='Укажите дату или она добавится автоматически'
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор подписки',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='author_user_unique',
                fields=['author', 'user'],
            ),
            models.CheckConstraint(
                name="author_not_user",
                check=models.Q(author=models.F('user')),
            ),
        ]
