from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.utils.safestring import mark_safe
import os
import uuid
import bleach
import markdown

from .models import Article, ArticleCategory, ArticleTag, ArticleAttachment, ArticleFeedback
from .forms import ArticleForm, ArticleFeedbackForm


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
        
        # Process articles to include excerpts for cleaner display
        articles_with_excerpts = []
        for article in context['articles']:
            articles_with_excerpts.append({
                'article': article,
                'excerpt': article.get_excerpt(200) if hasattr(article, 'get_excerpt') else (
                    article.summary or article.content[:200] + ('...' if len(article.content) > 200 else '')
                )
            })
        
        context['articles_with_excerpts'] = articles_with_excerpts
        
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
        
        # Convert content to HTML based on format (support both TinyMCE and Markdown)
        if hasattr(self.object, 'get_rendered_content'):
            context['article_html'] = self.object.get_rendered_content()
        else:
            # Fallback to basic markdown rendering
            import re
            if re.search(r'<[^>]*>', self.object.content):
                # Content appears to be HTML, sanitize it
                allowed_tags = [
                    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'p',
                    'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'hr', 'br', 
                    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'img'
                ]
                allowed_attrs = {
                    '*': ['class'],
                    'a': ['href', 'title', 'target'],
                    'img': ['src', 'alt', 'width', 'height']
                }
                
                context['article_html'] = mark_safe(
                    bleach.clean(
                        self.object.content,
                        tags=allowed_tags,
                        attributes=allowed_attrs,
                        strip=True
                    )
                )
            else:
                # Assume it's markdown
                context['article_html'] = mark_safe(markdown.markdown(
                    self.object.content,
                    extensions=['extra', 'codehilite']
                ))
        
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
            
        # Save the article first to get an ID if it's new
        response = super().form_valid(form)
        
        # Handle file uploads
        files = self.request.FILES.getlist('attachments')
        for uploaded_file in files:
            # Create attachment
            attachment = ArticleAttachment(
                article=self.object,
                file=uploaded_file,
                title=uploaded_file.name,
                uploaded_by=self.request.user
            )
            attachment.save()
        
        messages.success(self.request, "Article created successfully!")
        return response
    
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
        
        # Save the article first
        response = super().form_valid(form)
        
        # Handle file uploads
        files = self.request.FILES.getlist('attachments')
        for uploaded_file in files:
            # Create attachment
            attachment = ArticleAttachment(
                article=self.object,
                file=uploaded_file,
                title=uploaded_file.name,
                uploaded_by=self.request.user
            )
            attachment.save()
        
        # Handle attachment deletions
        attachment_ids_to_delete = self.request.POST.getlist('delete_attachment')
        if attachment_ids_to_delete:
            ArticleAttachment.objects.filter(
                id__in=attachment_ids_to_delete, 
                article=self.object
            ).delete()
            
        messages.success(self.request, "Article updated successfully!")
        return response
    
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
        
        # Process articles to include excerpts
        articles_with_excerpts = []
        for article in context['articles']:
            articles_with_excerpts.append({
                'article': article,
                'excerpt': article.get_excerpt(200) if hasattr(article, 'get_excerpt') else (
                    article.summary or article.content[:200] + ('...' if len(article.content) > 200 else '')
                )
            })
        
        context['articles_with_excerpts'] = articles_with_excerpts
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
    
    # Process articles to include excerpts
    articles_with_excerpts = []
    for article in articles:
        articles_with_excerpts.append({
            'article': article,
            'excerpt': article.get_excerpt(200) if hasattr(article, 'get_excerpt') else (
                article.summary or article.content[:200] + ('...' if len(article.content) > 200 else '')
            )
        })
    
    return render(request, 'articles/search_results.html', {
        'articles': articles,
        'articles_with_excerpts': articles_with_excerpts,
        'query': query
    })


@login_required
@require_POST
def upload_file(request):
    """
    Handler for TinyMCE file uploads.
    Supports PDF, images, and other document types.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method is allowed'})
    
    # Check if file is present
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'})
    
    uploaded_file = request.FILES['file']
    
    # Validate file size (10MB max)
    if uploaded_file.size > 10 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'File too large. Maximum size is 10MB'})
    
    # Get file extension and validate
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    # List of allowed extensions
    allowed_extensions = [
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
    ]
    
    if file_extension not in allowed_extensions:
        return JsonResponse({
            'success': False, 
            'error': f'Unsupported file type. Allowed types: {", ".join(allowed_extensions)}'
        })
    
    # Create a unique filename to avoid collisions
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    
    # Determine upload directory based on file type
    if file_extension in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']:
        upload_dir = 'article_attachments/documents'
    else:
        upload_dir = 'article_attachments/images'
    
    # Full path relative to MEDIA_ROOT
    from django.conf import settings
    relative_path = os.path.join(upload_dir, unique_filename)
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    # Save the file
    try:
        with open(full_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error saving file: {str(e)}'})
    
    # Create attachment record
    try:
        article_id = request.POST.get('article_id')
        article = None
        
        if article_id and article_id != 'undefined' and article_id != 'null':
            try:
                article = Article.objects.get(pk=article_id)
            except (Article.DoesNotExist, ValueError):
                pass
        
        attachment = ArticleAttachment(
            file=relative_path,
            title=uploaded_file.name,
            uploaded_by=request.user
        )
        
        if article:
            attachment.article = article
            
        attachment.save()
    except Exception as e:
        # If we can't save to the database, we can still return the URL
        # The file is already saved on disk
        pass
    
    # Generate the URL to the uploaded file
    url = f"{settings.MEDIA_URL}{relative_path}"
    
    # Return success response with file URL
    return JsonResponse({
        'success': True,
        'url': url,
        'title': uploaded_file.name
    })