from search.es_models import EsPassage
from elasticsearch_dsl.connections import connections


es = connections.create_connection(hosts=["localhost"], filter=["lowercase"])
EsPassage.init()




