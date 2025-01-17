import os
import sys

from green.config import default_args, mergeConfig
from green.loader import loadTargets
from green.output import GreenStream
from green.runner import GreenTestRunner

# If we're not being run from an actual django project, set up django config
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'green.djangorunner')
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SECRET_KEY = ')9^_e(=cisybdt4m4+fs+_wb%d$!9mpcoy0um^alvx%gexj#jv'
DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = []
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
)
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
ROOT_URLCONF = 'myproj.urls'
WSGI_APPLICATION = 'myproj.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
# End of django fake config stuff


DjangoRunner = None

try:
    import django
    if django.VERSION[:2] < (1, 6):
        raise ImportError("Green integration supports Django 1.6+")
    from django.test.runner import DiscoverRunner

    class DjangoRunner(DiscoverRunner):
        def run_tests(self, test_labels, extra_tests=None, **kwargs):
            """
            Run the unit tests for all the test labels in the provided list.

            Test labels should be dotted Python paths to test modules, test
            classes, or test methods.

            A list of 'extra' tests may also be provided; these tests
            will be added to the test suite.

            Returns the number of tests that failed.
            """
            # Django setup
            self.setup_test_environment()

            # Green
            if test_labels:
                test_labels = list(test_labels)
            else:
                test_labels = ['.']
            suite = loadTargets(test_labels)
            old_config = self.setup_databases()

            args = mergeConfig(default_args, default_args)
            stream = GreenStream(sys.stderr, html = args.html)
            runner = GreenTestRunner(verbosity = args.verbose, stream = stream,
                termcolor=args.termcolor, subprocesses=args.subprocesses,
                run_coverage=args.run_coverage, omit=args.omit)
            result = runner.run(suite)

            # Django teardown
            self.teardown_databases(old_config)
            self.teardown_test_environment()
            return self.suite_result(suite, result)

except ImportError:
    pass
