import uuid
import time

from django.db import models

# Create your models here.


class Category(models.Model):
    cid = models.CharField(max_length=100, primary_key=True)
    cname = models.CharField(max_length=1000)

    class Meta:
        db_table = 'category'


class Log(models.Model):
    logid = models.CharField(max_length=100, primary_key=True)
    time = models.BigIntegerField()
    keyword = models.CharField(max_length=1000)
    timespan = models.BigIntegerField()
    hits = models.IntegerField()

    class Meta:
        db_table = 'log'

    @classmethod
    def create(cls, keyword, timespan, hits):
        log = cls(keyword=keyword, timespan=int(timespan*1000), hits=hits)
        log.logid = uuid.uuid4()
        log.time = int(time.time()*1000)
        return log


class Passage(models.Model):
    pid = models.CharField(max_length=100, primary_key=True)
    cid = models.CharField(max_length=1000)
    ptitle = models.CharField(max_length=1000)
    ptext = models.TextField()
    plink = models.CharField(max_length=1000)
    pdate = models.BigIntegerField()

    class Meta:
        db_table = 'passage'


