from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import Article, ArticleCategory, ArticleTag
from .forms import ArticleForm, ArticleFeedbackForm
import markdown

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # Convert Markdown to HTML
    context['article_html'] = markdown.markdown(
        self.object.content,
        extensions=['extra', 'codehilite']
    )
    return context

class ArticleListView(ListView):
    """Display a list of published articles."""
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(status=Article.Status.PUBLISHED)
        
        # Filter by category if provided
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(ArticleCategory, slug=category_slug)
            queryset = queryset.filter(categories=category)
        
        # Filter by tag if provided
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(ArticleTag, slug=tag_slug)
            queryset = queryset.filter(tags=tag)
        
        # Handle search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query) | 
                Q(summary__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ArticleCategory.objects.filter(parent=None)
        context['tags'] = ArticleTag.objects.all()
        context['featured_articles'] = Article.objects.filter(
            is_featured=True, 
            status=Article.Status.PUBLISHED
        )[:5]
        
        # Add category and tag context if filtering
        if 'category_slug' in self.kwargs:
            context['current_category'] = get_object_or_404(
                ArticleCategory, 
                slug=self.kwargs['category_slug']
            )
            
        if 'tag_slug' in self.kwargs:
            context['current_tag'] = get_object_or_404(
                ArticleTag, 
                slug=self.kwargs['tag_slug']
            )
            
        return context


class ArticleDetailView(DetailView):
    """Display a single article with its details."""
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        # Increment view count
        obj.view_count += 1
        obj.save(update_fields=['view_count'])
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feedback_form'] = ArticleFeedbackForm()
        context['related_articles'] = self.object.related_articles.filter(
            status=Article.Status.PUBLISHED
        )[:3]
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle article feedback submission."""
        self.object = self.get_object()
        form = ArticleFeedbackForm(request.POST)
        
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.article = self.object
            feedback.ip_address = request.META.get('REMOTE_ADDR')
            
            if request.user.is_authenticated:
                feedback.user = request.user
                
            # Update article's helpful/not helpful counts
            if feedback.helpful:
                self.object.helpful_votes += 1
            else:
                self.object.not_helpful_votes += 1
                
            feedback.save()
            self.object.save()
            
            messages.success(request, "Thank you for your feedback!")
            return redirect(self.object.get_absolute_url())
        
        context = self.get_context_data(object=self.object)
        context['feedback_form'] = form
        return render(request, self.template_name, context)


class ArticleCreateView(LoginRequiredMixin, CreateView):
    """Create a new knowledge base article."""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        
        # Set published_at if status is published
        if form.instance.status == Article.Status.PUBLISHED:
            form.instance.published_at = timezone.now()
            
        messages.success(self.request, "Article created successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Article'
        return context


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing knowledge base article."""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'
    
    def test_func(self):
        """Only allow the author or staff to edit articles."""
        obj = self.get_object()
        return obj.author == self.request.user or self.request.user.is_staff
    
    def form_valid(self, form):
        # Set published_at if status changed to published
        if form.instance.status == Article.Status.PUBLISHED and not form.instance.published_at:
            form.instance.published_at = timezone.now()
            
        messages.success(self.request, "Article updated successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Article'
        return context


class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an existing knowledge base article."""
    model = Article
    template_name = 'articles/article_confirm_delete.html'
    success_url = reverse_lazy('articles:article-list')
    
    def test_func(self):
        """Only allow the author or staff to delete articles."""
        obj = self.get_object()
        return obj.author == self.request.user or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Article deleted successfully!")
        return super().delete(request, *args, **kwargs)


# Additional Views

class DraftArticleListView(LoginRequiredMixin, ListView):
    """View for authors to see their draft articles."""
    model = Article
    template_name = 'articles/draft_article_list.html'
    context_object_name = 'articles'
    
    def get_queryset(self):
        # Show only user's draft articles or all drafts for staff
        if self.request.user.is_staff:
            return Article.objects.filter(status=Article.Status.DRAFT)
        return Article.objects.filter(
            author=self.request.user,
            status=Article.Status.DRAFT
        )


class CategoryArticleListView(ListView):
    """Display articles filtered by category."""
    model = Article
    template_name = 'articles/category_article_list.html'
    context_object_name = 'articles'
    paginate_by = 10
    
    def get_queryset(self):
        self.category = get_object_or_404(ArticleCategory, slug=self.kwargs['slug'])
        return Article.objects.filter(
            categories=self.category,
            status=Article.Status.PUBLISHED
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


# Simple function view for searching articles
def search_articles(request):
    query = request.GET.get('q', '')
    
    articles = Article.objects.filter(
        status=Article.Status.PUBLISHED
    ).filter(
        Q(title__icontains=query) | 
        Q(content__icontains=query) |
        Q(summary__icontains=query) |
        Q(tags__name__icontains=query)
    ).distinct()
    
    return render(request, 'articles/search_results.html', {
        'articles': articles,
        'query': query
    })