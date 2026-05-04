from django.contrib import admin
from .models import Category

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('Category_name', 'slug')
    prepopulated_fields = {'slug': ('Category_name',)}

admin.site.register(Category, CategoryAdmin)

