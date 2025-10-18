from django.contrib import admin
from .models import Folder, File, FileUploadSession, CustomUser, Role


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'token', 'parent', 'created_at', 'updated_at')
    search_fields = ('name', 'token')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('token', 'created_at', 'updated_at')
    ordering = ('name',)


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_type', 'folder', 'size', 'created_at', 'updated_at')
    search_fields = ('name', 'token')
    list_filter = ('file_type', 'created_at')
    readonly_fields = ('token', 'size', 'created_at', 'updated_at')
    ordering = ('-created_at',)


admin.site.register(FileUploadSession)
admin.site.register(CustomUser)
admin.site.register(Role)
