# coding=utf-8
import json
import time
from django.http import HttpResponse
from django.shortcuts import render
from django.db import connection
from . import es_util
from . import es_models
from .models import Category, Passage, Log
from elasticsearch import Elasticsearch
from datetime import datetime


client = Elasticsearch(hosts=['127.0.0.1'])


# 获取分类cname与分类cid的对应
cate_map = {}
cates = Category.objects.all()
for c in cates:
    cate_map[c.cid] = c.cname


# 获取搜索建议
def suggest(request):
    key_words = request.GET.get('s', '')
    resp_data = []
    if key_words:
        s = es_models.EsPassage.search()
        s = s.suggest("my_suggest", key_words, completion={
            "field": "suggest", "fuzzy": {
                "fuzziness": 1
            },
            "size": 10
        })
        suggestions = s.execute_suggest()
        for match in suggestions.my_suggest[0].options:
            source = match._source
            resp_data.append(source['ptitle'])
    return HttpResponse(json.dumps(resp_data), content_type="application/json")


# 调用es util，从mysql数据库中读取数据，并更新到es索引库中
def update(request):
    status, data = es_util.update_es()
    if status == 'ok':
        msg = '成功更新了 %d 条数据' % data
    else:
        msg = '更新过程中出错，错误信息：' + data.message
    context = {'msg': msg}
    return render(request, 'updateok.html', context)


def search(request):
    key_words = request.POST.get('queryString', '')
    page = request.POST.get('currentPage', '1')
    try:
        page = int(page)
    except:
        page = 1
    start_time = datetime.now()
    response = client.search(
        index="wechatsearch",
        body={
            "query": {
                "multi_match": {
                    "query": key_words,
                    "fields": ['ptitle', 'ptext']
                }
            },
            "from": (page - 1) * 10,
            "size": 10,
            "highlight": {
                "pre_tags": ["<span>"],
                "post_tags": ["</span>"],
                "fields": {
                    "ptitle": {},
                    "ptext": {}
                }
            }
        }
    )
    end_time = datetime.now()
    time_span = round((end_time - start_time).total_seconds(), 3)
    total_nums = response['hits']['total']
    hit_list = []
    for hit in response['hits']['hits']:
        hit_dict = {}
        if "ptitle" in hit['highlight']:
            hit_dict['ptitle'] = "".join(hit['highlight']['ptitle'])
        else:
            hit_dict['ptitle'] = "".join(hit['_source']['ptitle'])
        if "ptext" in hit['highlight']:
            hit_dict['ptext'] = "".join(hit['highlight']['ptext'])
        else:
            hit_dict['ptext'] = "".join(hit['_source']['ptext'])
        hit_dict['pdate'] = hit['_source']['pdate'][:10]
        hit_dict['plink'] = hit['_source']['plink']
        hit_dict['cid'] = hit['_source']['cid']
        hit_dict['cname'] = cate_map[hit_dict['cid']]

        hit_list.append(hit_dict)

    context = {
        "all_hits": hit_list,
        "keyword": key_words,
        "currentPage": page,
        "total_nums": total_nums,
        "time_span": time_span
    }
    # 进行日志记录
    if page == 1:
        log = Log.create(key_words, time_span, total_nums)
        log.save()
    return render(request, "result.html", context)


# 显示某分类下的列表
def category(request):
    cid = request.GET.get('cid', '1')
    page = request.GET.get('page', '1')
    try:
        page = int(page)
    except:
        page = 1
    start_time = datetime.now()
    total_num = Passage.objects.filter(cid=cid).order_by('-pdate').count()
    # 限制 page 不能超过最大页数，不能少于1
    if total_num % 10 == 0:
        max_page = int(total_num / 10)
    else:
        max_page = int(total_num / 10) + 1
    if page > max_page:
        page = max_page
    elif page < 1:
        page = 1
    # 限制查询下标不能超过最大数量
    start_index = 10 * (page - 1)
    end_index = start_index + 10
    if end_index > total_num:
        end_index = total_num
    hit_list = Passage.objects.filter(cid=cid).order_by('-pdate')[start_index:end_index]
    end_time = datetime.now()
    time_span = round((end_time - start_time).total_seconds(), 3)
    for h in hit_list:
        h.readable_date = str(datetime.utcfromtimestamp(round(h.pdate/1000)))[0:10]
    context = {
        "cname": cate_map[cid],
        "page": page,
        "total_num": total_num,
        "cid": cid,
        "time_span": time_span,
        "all_hits": hit_list
    }
    # 进行日志记录
    if page == 1:
        log = Log.create('分类:'+cid, time_span, total_num)
        log.save()
    return render(request, "result2.html", context)


# 热搜词统计
def hot(request):
    type = request.GET.get('type', 'week')
    end_time = int(time.time()*1000)
    if type == 'week':
        start_time = end_time - 7*24*60*60*1000
        type = '最近一周'
    elif type == 'month':
        start_time = end_time - 30*24*60*60*1000
        type = '最近一月'
    else:
        start_time = 0
        type = '全部数据'

    # 统计 总查询次数、平均用时、平均命中
    # 统计 关键词、查询数量、平均查询耗时，平均hits，排序按数量降序
    with connection.cursor() as cursor:
        cursor.execute("SELECT keyword,COUNT(keyword),ROUND(AVG(timespan),1),ROUND(AVG(hits),1) FROM log WHERE time< %s AND time> %s GROUP BY keyword ORDER BY COUNT(keyword) desc", [end_time, start_time])
        detail_data = cursor.fetchall()
        cursor.execute("SELECT COUNT(keyword),ROUND(AVG(timespan),1),ROUND(AVG(hits),1) FROM log WHERE time< %s AND time> %s", [end_time, start_time])
        stat_data = cursor.fetchall()
        stat_str = '共有 %s 次查询，平均用时 %d ms，平均结果数 %d' % (stat_data[0])
    context = {
        "stat_data": stat_str,
        "detail_data": detail_data,
        "type": type
    }
    return render(request, 'stat.html', context)







