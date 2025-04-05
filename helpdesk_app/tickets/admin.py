from django.contrib import admin
from .models import Category, Ticket, Tag, TicketAttachment, TicketHistory, SLA
from modeltranslation.admin import TranslationAdmin

class CategoryAdmin(TranslationAdmin):
    list_display = ('name', 'parent', 'description')
    list_filter = ('parent',)
    search_fields = ('name', 'description')

admin.site.register(Category, CategoryAdmin)
# Register other models as needed