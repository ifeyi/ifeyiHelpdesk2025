from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse


class ArticleCategory(models.Model):
    """
    Categories for organizing knowledge base articles.
    """
    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('Parent category')
    )
    icon = models.CharField(_('Icon class'), max_length=50, blank=True)
    order = models.PositiveIntegerField(_('Display order'), default=0)
    
    class Meta:
        verbose_name = _('Article Category')
        verbose_name_plural = _('Article Categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('articles:article-category-detail', kwargs={'slug': self.slug})


class Article(models.Model):
    """
    Knowledge base articles for the helpdesk.
    """
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')
    
    title = models.CharField(_('Title'), max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, unique=True)
    content = models.TextField(_('Content'))
    summary = models.CharField(_('Summary'), max_length=255, blank=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    
    # Relationships
    categories = models.ManyToManyField(
        ArticleCategory,
        related_name='articles',
        verbose_name=_('Categories')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='articles',
        verbose_name=_('Author')
    )
    related_articles = models.ManyToManyField(
        'self',
        blank=True,
        verbose_name=_('Related articles')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    published_at = models.DateTimeField(_('Published at'), null=True, blank=True)
    
    # Additional Fields
    tags = models.ManyToManyField('ArticleTag', blank=True, related_name='articles')
    is_featured = models.BooleanField(_('Featured article'), default=False)
    view_count = models.PositiveIntegerField(_('View count'), default=0)
    helpful_votes = models.PositiveIntegerField(_('Helpful votes'), default=0)
    not_helpful_votes = models.PositiveIntegerField(_('Not helpful votes'), default=0)
    
    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['published_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('articles:article-detail', kwargs={'slug': self.slug})


class ArticleAttachment(models.Model):
    """
    Files attached to articles.
    """
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Article')
    )
    file = models.FileField(_('File'), upload_to='article_attachments/%Y/%m/')
    title = models.CharField(_('Title'), max_length=255)
    description = models.CharField(_('Description'), max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='article_attachments',
        verbose_name=_('Uploaded by')
    )
    uploaded_at = models.DateTimeField(_('Uploaded at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Article Attachment')
        verbose_name_plural = _('Article Attachments')
    
    def __str__(self):
        return self.title


class ArticleTag(models.Model):
    """
    Tags for articles to facilitate searching and categorization.
    """
    name = models.CharField(_('Name'), max_length=50, unique=True)
    slug = models.SlugField(_('Slug'), max_length=50, unique=True)
    color = models.CharField(_('Color'), max_length=20, blank=True)
    
    class Meta:
        verbose_name = _('Article Tag')
        verbose_name_plural = _('Article Tags')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ArticleFeedback(models.Model):
    """
    User feedback on articles.
    """
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='feedback',
        verbose_name=_('Article')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='article_feedback',
        verbose_name=_('User'),
        null=True,
        blank=True
    )
    helpful = models.BooleanField(_('Was helpful'), null=True)
    comment = models.TextField(_('Comment'), blank=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Article Feedback')
        verbose_name_plural = _('Article Feedback')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.article.title} - {'Helpful' if self.helpful else 'Not helpful'}"