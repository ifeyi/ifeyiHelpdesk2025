from django.contrib import admin
from .models import (
    Ticket, Category, Tag, TicketAttachment, 
    TicketHistory, SLA, Department, SubDepartment
)

class SubDepartmentInline(admin.TabularInline):
    model = SubDepartment
    extra = 1

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager')
    search_fields = ('name', 'code', 'description')
    list_filter = ('manager',)
    inlines = [SubDepartmentInline]

@admin.register(SubDepartment)
class SubDepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'code', 'manager')
    search_fields = ('name', 'code', 'description')
    list_filter = ('department', 'manager')
    
class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 1
    
class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ('user', 'timestamp', 'field_changed', 'old_value', 'new_value')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'department', 'subdepartment', 'branch', 'created_by', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'branch', 'department', 'subdepartment', 'created_at', 'category')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username')
    date_hierarchy = 'created_at'
    inlines = [TicketAttachmentInline, TicketHistoryInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'office_door_number')
        }),
        ('Status Info', {
            'fields': ('status', 'priority', 'branch')
        }),
        ('Categorization', {
            'fields': ('department', 'subdepartment', 'category', 'tags')
        }),
        ('Assignments', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'due_date', 'resolved_at', 'closed_at')
        }),
        ('Additional Info', {
            'fields': ('sla_breach', 'is_public')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags',)

class SubCategoryInline(admin.TabularInline):
    model = Category
    fk_name = 'parent'
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'description')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    inlines = [SubCategoryInline]

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)

@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'file', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('ticket__title', 'description')

@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'field_changed', 'old_value', 'new_value', 'user', 'timestamp')
    list_filter = ('field_changed', 'timestamp', 'user')
    search_fields = ('ticket__title', 'old_value', 'new_value')
    date_hierarchy = 'timestamp'
    readonly_fields = ('ticket', 'user', 'timestamp', 'field_changed', 'old_value', 'new_value')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ('name', 'response_time_critical', 'resolution_time_critical', 'business_hours_only')
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'business_hours_only')
        }),
        ('Response Times (hours)', {
            'fields': ('response_time_low', 'response_time_medium', 'response_time_high', 'response_time_critical')
        }),
        ('Resolution Times (hours)', {
            'fields': ('resolution_time_low', 'resolution_time_medium', 'resolution_time_high', 'resolution_time_critical')
        }),
    )