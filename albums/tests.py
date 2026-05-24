import cloudinary
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from photoalbum import settings as app_settings

from .models import Album, Photo


class DatabaseUrlParsingTests(SimpleTestCase):
    def test_postgres_scheme_is_supported_case_insensitively(self):
        self.assertTrue(app_settings._is_postgres_scheme('POSTGRES'))

    def test_driver_qualified_postgresql_scheme_is_supported(self):
        self.assertTrue(app_settings._is_postgres_scheme('postgresql+psycopg'))


class AlbumWorkflowTests(TestCase):
    def setUp(self):
        self.standard_user = User.objects.create_user(username='alice', password='password123')
        self.other_user = User.objects.create_user(username='bob', password='password123')
        self.admin_user = User.objects.create_user(username='admin', password='password123')

        group, _ = Group.objects.get_or_create(name='Album Administrator')
        group.user_set.add(self.admin_user)

    def test_standard_user_can_create_album(self):
        self.client.force_login(self.standard_user)
        response = self.client.post(
            reverse('album_create'),
            {'title': 'Spring Memories', 'description': 'A collection of spring shots', 'is_public': True},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Album.objects.filter(owner=self.standard_user, title='Spring Memories').exists())

    def test_standard_user_cannot_access_admin_dashboard(self):
        self.client.force_login(self.standard_user)
        response = self.client.get(reverse('admin_dashboard'))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_admin_dashboard(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_dashboard'))

        self.assertEqual(response.status_code, 200)

    def test_owner_can_edit_album(self):
        album = Album.objects.create(title='Personal album', description='Owned album', owner=self.standard_user, is_public=True)
        self.client.force_login(self.standard_user)

        response = self.client.get(reverse('album_update', args=[album.pk]))

        self.assertEqual(response.status_code, 200)

    def test_non_owner_cannot_edit_album(self):
        album = Album.objects.create(title='Private album', description='Other user album', owner=self.other_user, is_public=False)
        self.client.force_login(self.standard_user)

        response = self.client.get(reverse('album_update', args=[album.pk]))

        self.assertEqual(response.status_code, 403)

    def test_upload_photo_falls_back_when_cloudinary_is_unconfigured(self):
        cloudinary.config(api_key=None, api_secret=None, cloud_name=None)

        album = Album.objects.create(
            title='Fallback album',
            description='Upload should still work without Cloudinary credentials.',
            owner=self.standard_user,
            is_public=True,
        )
        self.client.force_login(self.standard_user)

        image = SimpleUploadedFile(
            'fallback.png',
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
            content_type='image/png',
        )

        response = self.client.post(
            reverse('photo_upload', args=[album.pk]),
            {
                'album': album.pk,
                'image': image,
                'caption': 'Fallback upload',
                'is_public': 'on',
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        photo = Photo.objects.get(album=album, uploaded_by=self.standard_user, caption='Fallback upload')
        self.assertTrue(photo.image.url.startswith('/media/photo-album-app/'))
        self.assertTrue(photo.image.url.endswith('.png'))
