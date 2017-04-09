"""extensions fields."""
import os
import time
import hashlib

from datetime import datetime

from uuid import uuid4

import six

from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.crypto import get_random_string

from server.settings import MEDIA_ROOT

MAX_UNIQUE_QUERY_ATTEMPTS = 100


class FixedCharField(models.CharField):
    """Fixed length char field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'char(%s) BINARY' % self.max_length


class RandomFixedCharField(FixedCharField):
    """Random fixed length char field.

    By default, sets editable=False, unique=False.

    Required arguments:

    max_length
        Specifies the max length of the field

    Optional arguments:

    unique
        If set to True, duplicate entries are not allowed (default: False)
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        super().__init__(*args, **kwargs)

    def random_char_generator(self, chars):
        for i in range(MAX_UNIQUE_QUERY_ATTEMPTS):      # pylint: disable=W0612
            yield ''.join(get_random_string(self.max_length, chars))
        raise RuntimeError(
            'max random character attempts exceeded (%s)' %
            MAX_UNIQUE_QUERY_ATTEMPTS)

    def pre_save(self, model_instance, add):
        if not add and getattr(model_instance, self.attname) != '':
            return getattr(model_instance, self.attname)

        population = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

        random_chars = self.random_char_generator(population)
        if not self.unique:
            new = six.next(random_chars)
            setattr(model_instance, self.attname, new)
            return new

        return self.find_unique(model_instance, random_chars)

    def find_unique(self, model_instance, iterator):
        """exclude the current model instance from the queryset used in finding
        next valid hash
        """
        queryset = model_instance.__class__.objects.all()
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        # form a kwarg dict used to impliment any unique_together contraints
        kwargs = {}
        # pylint: disable=W0212
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                for param in params:
                    kwargs[param] = getattr(model_instance, param, None)

        new = six.next(iterator)
        kwargs[self.attname] = new
        while not new or queryset.filter(**kwargs):
            new = six.next(iterator)
            kwargs[self.attname] = new
        setattr(model_instance, self.attname, new)
        return new


def generate_filename(origin_filename):
    ext = origin_filename.split('.')[-1]

    salt = '{}{}'.format(time.time(), uuid4().hex)

    file_prefix = hashlib.md5(salt.encode()).hexdigest()
    return '{}.{}'.format(file_prefix, ext)


@deconstructible    # pylint: disable=R0903
class PathAndRename(object):
    """Path and rename."""

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, origin_filename):
        filename = generate_filename(origin_filename)

        datestr = datetime.today().strftime('%Y%m%d')
        fullpath = os.path.join(self.path, datestr)

        abspath = os.path.join(MEDIA_ROOT, fullpath)
        if not os.path.exists(abspath):
            os.makedirs(abspath)

        return os.path.join(fullpath, filename)
