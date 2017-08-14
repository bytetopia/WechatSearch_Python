from search.models import Passage
from search.es_models import EsPassage
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Index
from datetime import datetime

es = connections.create_connection(hosts=["localhost"], filter=["lowercase"])


def gen_suggests(index, info_tuple):
    # 根据输入的字符串，生成ES的搜索建议数组
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            # 调用ik切词
            words = es.indices.analyze(index=index, analyzer="ik_smart", params={"filter": ["lowercase"]}, body=text)
            analyzer_words = set([r['token'] for r in words['tokens'] if len(r['token']) > 1])
            new_words = analyzer_words - used_words
        else:
            new_words = set()
        if new_words:
            suggests.append({'input': list(new_words), 'weight': weight})
    return suggests


# 从mysql中读取出所有数据，并存入es
def update_es():
    try:
        EsPassage.init()
        original = Index('wechatsearch')
        original.delete()
        print('已删除es中原有数据。\n正在生成新数据...')
        EsPassage.init()
        passage_list = Passage.objects.all()
        count = 0
        for p in passage_list:
            ep = EsPassage()
            ep.cid = p.cid
            ep.ptitle = p.ptitle
            ep.ptext = p.ptext
            ep.pdate = datetime.utcfromtimestamp(round(p.pdate/1000))
            ep.plink = p.plink
            ep.suggest = gen_suggests(EsPassage._doc_type.index, ((p.ptitle, 5), (p.ptext, 1)))
            ep.meta.id = p.pid
            ep.save()
            count += 1
            print('成功保存  ' + p.ptitle)
        print('数据更新成功。')
        return 'ok', count
    except Exception as e:
        return 'fail', e


