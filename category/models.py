from django.db import models
from django.urls import reverse

class Category(models.Model):
    Category_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True, null=True)


    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def on_list(self):
        return reverse('products_by_category', args=[self.slug])


    def __str__(self):
        return self.Category_name
    

