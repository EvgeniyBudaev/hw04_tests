from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Evgeniy')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        """Создание авторизованного пользователя."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_form_create_new_post(self):
        """Форма создаёт пост в базе и перенаправляет пользователя
        на главную страницу."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый пост из формы', 'group': self.group.id}
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с нашим текстом
        self.assertTrue(Post.objects.filter(
            text='Тестовый пост из формы',
            group=self.group.id
        ).exists())
        # Проверяем, сработал ли редирект на главную страницу
        self.assertRedirects(response, reverse('index'))

    def test_edit_post_in_form(self):
        """проверка редактирования поста."""
        form_data = {'text': 'Новый текст', 'group': self.group.id}
        self.authorized_client.post(
            reverse('post_edit',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}),
            data=form_data
        )
        response = self.authorized_client.get(
            reverse('post',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'].text, 'Новый текст')
        self.assertTrue(Post.objects.filter(
            text='Новый текст',
            group=self.group.id
        ).exists())
