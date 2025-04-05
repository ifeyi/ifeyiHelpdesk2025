from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    # Article list views
    path('', views.ArticleListView.as_view(), name='article-list'),
    path('search/', views.search_articles, name='article-search'),
    path('drafts/', views.DraftArticleListView.as_view(), name='article-drafts'),
    
    # Category and tag filtered views
    path('category/<slug:category_slug>/', views.ArticleListView.as_view(), name='article-category'),
    path('tag/<slug:tag_slug>/', views.ArticleListView.as_view(), name='article-tag'),
    
    # CRUD operations
    path('new/', views.ArticleCreateView.as_view(), name='article-create'),
    path('<slug:slug>/', views.ArticleDetailView.as_view(), name='article-detail'),
    path('<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='article-update'),
    path('<slug:slug>/delete/', views.ArticleDeleteView.as_view(), name='article-delete'),
    
    # Category detail view
    path('categories/<slug:slug>/', views.CategoryArticleListView.as_view(), name='article-category-detail'),
]