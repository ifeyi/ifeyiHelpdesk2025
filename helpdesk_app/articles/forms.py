from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Article, ArticleFeedback


class ArticleForm(forms.ModelForm):
    """Form for creating and updating articles."""
    
    class Meta:
        model = Article
        fields = [
            'title', 'content', 'summary', 'status', 
            'categories', 'tags', 'related_articles', 'is_featured'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'class': 'rich-text-editor'}),
            'summary': forms.Textarea(attrs={'rows': 3}),
            'categories': forms.CheckboxSelectMultiple(),
            'tags': forms.CheckboxSelectMultiple(),
            'related_articles': forms.SelectMultiple(),
        }
        help_texts = {
            'summary': _('A brief description of the article that will appear in search results.'),
            'is_featured': _('Featured articles appear prominently on the knowledge base homepage.'),
            'related_articles': _('Select other articles that are related to this one.'),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        
        # Validate that article has at least one category if being published
        if status == Article.Status.PUBLISHED:
            categories = cleaned_data.get('categories')
            if not categories or categories.count() == 0:
                self.add_error('categories', _('At least one category is required for published articles.'))
        
        return cleaned_data
    
    def save(self, commit=True):
        article = super().save(commit=False)
        
        # Set published_at when publishing for the first time
        if article.status == Article.Status.PUBLISHED and not article.published_at:
            article.published_at = timezone.now()
        
        if commit:
            article.save()
            self.save_m2m()
        
        return article


class ArticleFeedbackForm(forms.ModelForm):
    """Form for collecting user feedback on articles."""
    
    class Meta:
        model = ArticleFeedback
        fields = ['helpful', 'comment']
        widgets = {
            'helpful': forms.RadioSelect(choices=[(True, _('Yes')), (False, _('No'))]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Tell us why this was or wasn\'t helpful...')}),
        }
        labels = {
            'helpful': _('Was this article helpful?'),
            'comment': _('Comments (optional)'),
        }