# deals/tests/test_views.py
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Post, Group

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание',
            slug='test-slug',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )

        cls.post2 = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.form_fields_new_post = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        self.pages_with_posts = [
            reverse('index'),
            reverse('group_posts', kwargs={'slug': 'test-slug'})
        ]

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/index.html': reverse('index'),
            'posts/new_post.html': reverse('new_post'),
            'posts/group.html': reverse('group_posts',
                                        kwargs={'slug': 'test-slug'}),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста главной страницы
    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.context.get('page').object_list[-1],
                         self.post)

    # Проверка словаря context страницы group
    # и созданный пост в этой группе
    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'group_posts', kwargs={'slug': 'test-slug'}
        ))
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(response.context.get('page').object_list[-1],
                         self.post2)

    # Проверка словаря context и страницы создания поста
    def test_new_page_shows_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        for value, expected in self.form_fields_new_post.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    # Проверка на отсутствие на страницы group другой группы созданного поста
    def test_group_pages_not_show_new_post(self):
        """Шаблон group не содержит искомый контекст."""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test-slug'}))
        self.assertTrue(self.post not in response.context['page'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test User')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(15):
            cls.post = Post.objects.create(
                text=f'Тестовый пост номер {count}',
                author=cls.user)

    def test_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse('index') + '?page=2'
        )
        self.assertEqual(len(response.context.get('page').object_list), 5)
