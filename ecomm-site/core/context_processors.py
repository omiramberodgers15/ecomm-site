from .models import Category

def global_categories(request):
    return {
        "all_categories": Category.objects.all()
    }