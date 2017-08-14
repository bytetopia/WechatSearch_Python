from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'suggest', views.suggest, name="suggest"),
    url(r'update$', views.update, name="update"),
    url(r'search', views.search, name="search"),
    url(r'category', views.category, name="category"),
    url(r'hot', views.hot, name="hot")
]