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
        cls.test_user = User.objects.create(
            username='test_user'
        )
        cls.test_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='test-group',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        # Создание авторизованного пользователя.
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_post_form_create_new_post(self):
        """Форма создаёт пост в базе и перенаправляет пользователя
        на главную страницу."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый пост из формы', 'group': self.group.id}
        new_text_form = 'Тестовый пост из формы'
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        # Проверим, что ничего не упало и страница отдаёт код 200
        self.assertEqual(response.status_code, 200)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с нашим текстом
        self.assertTrue(Post.objects.filter(
            text=new_text_form,
            group=self.group.id,
            author=self.author
        ).exists())
        # Проверяем текст у добавленного поста
        last_object = Post.objects.filter().order_by('-id')[0]
        self.assertEqual(last_object.text, form_data['text'])
        # Проверяем, сработал ли редирект на главную страницу
        self.assertRedirects(response, reverse('index'))

    def test_edit_post_in_form(self):
        """проверка редактирования поста."""
        new_text = 'Новый текст'
        form_data = {'text': new_text, 'group': self.group.id}
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
        self.assertEqual(response.context['post'].text, new_text)
        self.assertTrue(Post.objects.filter(
            text=new_text,
            group=self.group.id
        ).exists())

    def test_create_post_guest(self):
        """Проверка создания поста неавторизованным пользователем."""
        form_data = {
            'text': 'Гость пытается создать новую запись в группе',
            'group': self.test_group.id,
        }

        posts_count = Post.objects.count()

        response = self.guest_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        # Убедимся, что запись в базе данных не создалась:
        # сравним количество записей в Post до и после отправки формы
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, 200)

    def test_edit_post_not_author(self):
        """Проверка на то, что авторизованный пользователь не может
        отредактировать чужой пост. """
        form_data_edit = {
            'text': 'Исправленный не автором текст записи',
            'group': self.test_group.id,
        }
        test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=self.test_user,
            group=self.test_group,
        )

        not_author_user = User.objects.create(
            username='not_author'
        )
        not_author_client = Client()
        not_author_client.force_login(not_author_user)

        kwargs = {'username': 'test_user', 'post_id': test_post.id}

        response = not_author_client.post(
            reverse('post_edit', kwargs=kwargs),
            data=form_data_edit,
            follow=True
        )
        test_post.refresh_from_db()
        self.assertNotEqual(test_post.text, form_data_edit['text'])
        self.assertEqual(test_post.group, self.test_group)
        self.assertEqual(test_post.author, self.test_user)
        self.assertEqual(response.status_code, 200)
