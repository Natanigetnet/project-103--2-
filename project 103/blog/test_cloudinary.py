import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.conf import settings

print('=== Cloudinary Configuration ===')
cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'NOT SET')
api_key = os.environ.get('CLOUDINARY_API_KEY', 'NOT SET')
api_secret = 'SET' if os.environ.get('CLOUDINARY_API_SECRET') else 'NOT SET'

print(f'CLOUDINARY_CLOUD_NAME: {cloud_name}')
print(f'CLOUDINARY_API_KEY: {api_key}')
print(f'CLOUDINARY_API_SECRET: {api_secret}')
print()

print('=== Django Settings ===')
storage = getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT SET')
storages = getattr(settings, 'STORAGES', 'NOT SET')
print(f'DEFAULT_FILE_STORAGE: {storage}')
print(f'STORAGES: {storages}')
print(f'MEDIA_URL: {settings.MEDIA_URL}')
print()

# Test if cloudinary is configured
try:
    import cloudinary
    config = cloudinary.config()
    print(f'Cloudinary cloud_name: {config.cloud_name}')
    print(f'Cloudinary api_key: {config.api_key}')
    print('Cloudinary is configured')
except Exception as e:
    print(f'Cloudinary error: {e}')
