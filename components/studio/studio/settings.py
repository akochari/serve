"""
Django settings for studio project.

Generated by 'django-admin startproject' using Django 2.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

AUTHENTICATION_BACKENDS = [
    'social_core.backends.github.GithubOAuth2',
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Crispy Forms
CRISPY_TEMPLATE_PACK="bootstrap4"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'pyey3^@n)$id1tc3_g7xcb55n7ii1989jy#&%!yk^z(u1us4@*'


if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['localhost']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Application definition
DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
 ]

THIRD_PARTY_APPS = [
    # add apps which you install using pip
    "crispy_forms",            
    'corsheaders',
    'django_celery_beat',
    'django_extensions',    # for executing runscript among others
    'django_filters',
    'oauth2_provider',
    'rest_framework',
    'rest_framework.authtoken',
    'social_django',
    'tagulous',
    'guardian',
]

LOCAL_APPS =[
    # add local apps which you create using startapp
    'api',
    'apps',
    'common',
    'deployments',
    'monitor',
    'models',
    'projects',
    'portal',
]

# # Application definition
INSTALLED_APPS = DEFAULT_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Related to oauth2_provider third-party apps
OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'groups': 'Access to your groups'}
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',   # Add
]

# https://www.django-rest-framework.org/api-guide/authentication/#setting-the-authentication-scheme
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ],
}

#Django guardian 403 templates
GUARDIAN_RENDER_403 = True
GUARDIAN_TEMPLATE_403 = '403.html'


# Main Url conf for loading all the routing path in Studio
ROOT_URLCONF = 'studio.urls'

# IMPORTANT: Must be encrypted as secrets in K8S
# Github
SOCIAL_AUTH_GITHUB_KEY = '<your-github-key>'
SOCIAL_AUTH_GITHUB_SECRET = '<your-github-secret>'
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']   # Ask for the user's email

# Google
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '<your-google-oauth2-key>'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '<your-google-oauth2-secret>'

# Tagulous serialization settings
SERIALIZATION_MODULES = {
    'xml':    'tagulous.serializers.xml_serializer',
    'json':   'tagulous.serializers.json',
    'python': 'tagulous.serializers.python',
    'yaml':   'tagulous.serializers.pyyaml',
}

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders
    'compressor.finders.CompressorFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'common/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',  # Add
                'social_django.context_processors.login_redirect', # Add
            ],
            'libraries': {
                'custom_tags': 'models.templatetags.custom_tags',
            }
        },
    },
]

WSGI_APPLICATION = 'studio.wsgi.application'
ASGI_APPLICATION = 'studio.asgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
# Dummy backend here to allow for local development with docker-compose!
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
#STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
# Media Files for Studio apps
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Related to user registration and authetication workflow
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'

# Specific to Studio stack:
# Redis settings
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_HOST = os.environ.get('REDIS_PORT_6379_TCP_ADDR', 'redis')
# Celery settings
CELERY_BROKER_URL = 'amqp://admin:LJqEG9RE4FdZbVWoJzZIOQEI@rabbit:5672//'
CELERY_RESULT_BACKEND = 'redis://%s:%d/%d' % (REDIS_HOST, REDIS_PORT, REDIS_DB)
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
# For Model Objects creation (check models/models.py, pre_save_model() )
VERSION_BACKEND = 'studio.version.Version'

# Other Helm/k8s deployment settings
CHART_CONTROLLER_URL = 'http://stack-chart-controller'
CHART_FOLDER="/app/charts/apps"
EXTERNAL_KUBECONF = True
KUBECONFIG = "/root/.kube/config"
NAMESPACE = 'default'
REGISTRY_SVC = 'stack-docker-registry'
STORAGECLASS = 'microk8s-hostpath'
# This can be simply "localhost", but it's better to test with a wildcard dns such as nip.io
DOMAIN = '127.0.0.1.nip.io'
STUDIO_URL = 'http://studio.127.0.0.1.nip.io:8080'
#To enable sticky sessions for k8s ingress  
SESSION_COOKIE_DOMAIN=".127.0.0.1.nip.io"

#Local dependecies Models
PROJECTS_MODEL = 'projects.Project'
APPINSTANCE_MODEL = 'apps.AppInstance'
APPS_MODEL = 'apps.Apps'
APPCATEGORIES_MODEL = 'apps.AppCategories'
MODELS_MODEL = 'models.Model'

#App statuses
APPS_STATUS_SUCCESS = ['Running', 'Succeeded', 'Success']
APPS_STATUS_WARNING = ['Pending', 'Installed', 'Waiting', 'Installing', 'Created']
