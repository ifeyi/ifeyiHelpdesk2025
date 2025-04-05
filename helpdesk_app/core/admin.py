from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import EmailLog, EmailSetting


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('email_type_display', 'recipient', 'subject_truncated', 'status_display', 'created_at', 'sent_at')
    list_filter = ('email_type', 'status', 'created_at')
    search_fields = ('recipient', 'subject', 'content')
    readonly_fields = ('email_type', 'subject', 'recipient', 'content', 'related_object_id', 
                      'related_object_type', 'status', 'error_message', 'created_at', 'sent_at')
    date_hierarchy = 'created_at'
    
    def email_type_display(self, obj):
        return obj.get_email_type_display()
    email_type_display.short_description = _('Email Type')
    
    def subject_truncated(self, obj):
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_truncated.short_description = _('Subject')
    
    def status_display(self, obj):
        status_colors = {
            'pending': 'orange',
            'sent': 'green',
            'failed': 'red',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    status_display.short_description = _('Status')


class SelectedAgentsInline(admin.TabularInline):
    model = EmailSetting.selected_agents.through
    extra = 1
    verbose_name = _('Selected Agent')
    verbose_name_plural = _('Selected Agents')


@admin.register(EmailSetting)
class EmailSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_truncated', 'is_enabled')
    search_fields = ('name', 'description')
    list_filter = ('is_enabled',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_enabled', 'email_signature'),
        }),
        (_('Agent Notifications'), {
            'fields': ('notify_all_agents_on_new_ticket', 'notify_selected_agents_only',
                      'notify_agent_on_assignment', 'notify_agent_on_comment'),
        }),
        (_('Customer Notifications'), {
            'fields': ('notify_customer_on_ticket_created', 'notify_customer_on_status_change', 
                      'notify_customer_on_comment'),
        }),
    )
    inlines = [SelectedAgentsInline]
    exclude = ('selected_agents',)
    
    def description_truncated(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_truncated.short_description = _('Description')