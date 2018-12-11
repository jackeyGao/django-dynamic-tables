django-dynamic-tables
=====================

动态创建table， 并通过 Django ORM 操作.


## 动态的创建表

动态的创建模型其实就是在运行时生成 Model 类， 这个可以通过函数实现， 通过传参(今天的日期, 如: 20181211)，然后生成新的模型类， Meta 中的 db\_table 为log\_20181211.

```python
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
```

可以看到， 通过函数生成不同的 Log Class. 注意LogMetaclass和\_\_metaclass\_\_  , 元类可以在运行时改变模型的名字，table 的名称我们可以通过db\_table定义, 类的名称可以通过覆盖元类的方法定义。

```python
print cls.__name__
Log_20181211
print cls._meta.db_table
log_20181211
```

## 使用

使用直接通过函数， 获取当前日期的 Log 模型， 然后通过is\_exists判读表是否创建， 没有创建则创建对应的表.


```python
def index(request):
    today = date.today().strftime("%Y%m%d")

    # RuntimeWarning: Model '__main__.logclasslog_' was already registered.
    # Reloading models is not advised as it can lead to inconsistencies
    # most notably with related models.
    # 如上述警告所述, Django 不建议重复加载 Model 的定义.
    # 作为 demo 可以直接通过get_log_model获取，无视警告.
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
```

上面获取 cls 部分， 这里的代码先通过apps的已经注册的 all_models 获取, 否则一个模型的第二次执行定义代码就会抛出RuntimeWarning警告, 在模型的初始化函数都会注册此模型, 最好不要重复注册. 先通过 apps.get_model 获取这个模型， 如果没有获取到则通过get_log_model初始化新的模型. 这样做更加稳妥一点.

