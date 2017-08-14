from elasticsearch_dsl import DocType, Keyword, Text, Date, Completion
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer


# 注：必须按以下方式为Completion定义ik_analyzer 不可以直接传文字 否则在init时会报错
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}

ik_analyzer = CustomAnalyzer("ik_smart", filter=["lowercase"])


class EsPassage(DocType):
    suggest = Completion(analyzer=ik_analyzer)
    cid = Keyword()
    ptitle = Text(analyzer="ik_smart")
    ptext = Text(analyzer="ik_smart")
    pdate = Date()
    plink = Keyword()

    class Meta:
        index = 'wechatsearch'
        doc_type = 'passage'


if __name__ == '__main__':
    EsPassage.init()
