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
    
# Add these methods to your Article model class

def get_rendered_content(self):
    """
    Renders content based on its format (Markdown or HTML from TinyMCE)
    """
    from django.utils.safestring import mark_safe
    import re
    import bleach
    import markdown
    
    # Check if content appears to be HTML (from TinyMCE)
    if re.search(r'<[^>]*>', self.content):
        # Clean the HTML to prevent XSS
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'p',
            'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'hr', 'br',
            'table', 'thead', 'tbody', 'tr', 'th', 'td', 'img', 'figure', 'figcaption',
            'pre', 'cite', 'dl', 'dt', 'dd', 'del', 'ins', 'sup', 'sub', 'small'
        ]
        allowed_attrs = {
            '*': ['class', 'style'],
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'width', 'height', 'style'],
            'table': ['border', 'cellpadding', 'cellspacing', 'width']
        }
        allowed_styles = [
            'font-family', 'font-size', 'font-weight', 'text-align', 'text-decoration',
            'color', 'background-color', 'width', 'height', 'margin', 'padding', 'border'
        ]
        
        cleaned_content = bleach.clean(
            self.content,
            tags=allowed_tags,
            attributes=allowed_attrs,
            styles=allowed_styles,
            strip=True
        )
        return mark_safe(cleaned_content)
    else:
        # Handle as Markdown for backward compatibility
        return mark_safe(markdown.markdown(
            self.content,
            extensions=['extra', 'codehilite', 'nl2br', 'tables']
        ))

def get_excerpt(self, length=150):
    """
    Returns a plain-text excerpt for display in listings
    """
    import re
    from django.utils.html import strip_tags
    
    # Use summary if available
    if self.summary:
        return self.summary
    
    # Otherwise create from content
    # First, strip all HTML tags
    plain_content = strip_tags(self.content)
    
    # Remove multiple spaces and newlines
    plain_content = re.sub(r'\s+', ' ', plain_content).strip()
    
    # Truncate to desired length
    if len(plain_content) > length:
        return plain_content[:length] + '...'
    return plain_content

def save(self, *args, **kwargs):
    """
    Override save method to handle special cases
    """
    # If not set already, generate slug from title
    if not self.slug:
        from django.utils.text import slugify
        self.slug = slugify(self.title)
    
    # Set published date when status changes to published
    from django.utils import timezone
    if self.status == self.Status.PUBLISHED and not self.published_at:
        self.published_at = timezone.now()
    
    # Clean content before saving (optional)
    # self.content = self.clean_html_content()
    
    super().save(*args, **kwargs)

def clean_html_content(self):
    """
    Cleans HTML content to ensure it's safe and consistent
    For additional security beyond bleach in get_rendered_content
    """
    import bleach
    import re
    
    # Skip if content doesn't appear to be HTML
    if not re.search(r'<[^>]*>', self.content):
        return self.content
    
    # Additional HTML cleaning logic if needed
    # For example, fix common HTML issues, normalize styles, etc.
    
    # Fix common issues with copy-pasted content
    content = re.sub(r'<o:p>.*?</o:p>', '', self.content)  # Remove Office XML tags
    content = re.sub(r'style="[^"]*mso-[^"]*"', '', content)  # Remove MSO styles
    
    return content