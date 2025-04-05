from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, AgentProfile, CustomerProfile


class AgentProfileInline(admin.StackedInline):
    model = AgentProfile
    can_delete = False
    verbose_name_plural = 'Agent Profile'
    fk_name = 'user'


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Customer Profile'
    fk_name = 'user'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'profile_picture')}),
        (_('Helpdesk info'), {'fields': ('user_type', 'department', 'phone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'user_type'),
        }),
    )
    
    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.user_type == User.UserType.AGENT:
            return [AgentProfileInline]
        elif obj.user_type == User.UserType.CUSTOMER:
            return [CustomerProfileInline]
        return []


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'availability_status', 'max_tickets')
    list_filter = ('availability_status',)
    search_fields = ('user__email', 'user__username')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'account_id', 'support_level')
    list_filter = ('support_level',)
    search_fields = ('user__email', 'user__username', 'company')