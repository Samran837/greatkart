
from category.models import Category


def menu_list(request):
    links = Category.objects.all()
    return dict(links=links)