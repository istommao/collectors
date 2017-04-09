"""collection admin."""
from django.contrib import admin

from collection.models import ResourceType, Resource


class ResourceTypeAdmin(admin.ModelAdmin):
    """资源类型."""

    list_display = ('name', 'creation_time')


class ResourceAdmin(admin.ModelAdmin):
    """资源."""

    list_display = ('title', 'category', 'creation_time', 'updation_time')


admin.site.register(ResourceType, ResourceTypeAdmin)
admin.site.register(Resource, ResourceAdmin)
