# -*- coding: utf-8 -*-
import sys, os

from datetime import date
from django.db import models
from django.db import connection
from django.apps import apps
from django.conf import settings
from django.conf.urls import url
from django.core.management import execute_from_command_line
from django.http import HttpResponse

settings.configure(
    DEBUG=True,
    SECRET_KEY='A-random-secret-key!',
    ROOT_URLCONF=sys.modules[__name__],
    INSTALLED_APPS=['__main__', ],
    DATABASES= {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join('./', 'db.sqlite3'),
        }
    }
)


def get_log_model(prefix):
    table_name = 'log_%s' % str(prefix)

    LOG_LEVELS = (
        (0, 'DEBUG'),
        (10, 'INFO'),
        (20, 'WARNING'),
    )

    class LogMetaclass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += '_' + prefix  # 这是Model的name.
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class Log(models.Model):
        __metaclass__ = LogMetaclass
        level = models.IntegerField(choices=LOG_LEVELS)
        msg = models.TextField()
        time = models.DateTimeField(auto_now=True, auto_now_add=True)

        @staticmethod
        def is_exists():
            return table_name in connection.introspection.table_names()

        class Meta:
            db_table = table_name

    return Log


def index(request):
    today = date.today().strftime("%Y%m%d")

    # RuntimeWarning: Model '__main__.logclasslog_' was already registered.
    # Reloading models is not advised as it can lead to inconsistencies
    # most notably with related models.
    # 如上述错误所述, Django 不建议重复加载 Model 的定义.
    # 所以这里先通过 all_models 获取已经注册的 Model,
    # 如果获取不到， 再生成新的模型.
    try:
        cls = apps.get_model('__main__', 'Log_%s' % today)
    except LookupError:
        cls = get_log_model(today)

    if not cls.is_exists():
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(cls)

    log = cls(level=10, msg="Hello")
    log.save()

    return HttpResponse('<h1>%s</h1>' % cls._meta.db_table)


urlpatterns = [
    url(r'^$', index),
]


if __name__ == '__main__':
    execute_from_command_line(sys.argv)
