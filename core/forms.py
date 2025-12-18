# forms.py
from django import forms
from .models import Product, SubCategory
from django.contrib.auth.models import User
from .models import Seller
from .models import Category

class SellerRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()

    class Meta:
        model = Seller
        fields = ['business_name', 'phone', 'address']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        seller = Seller.objects.create(
            user=user,
            business_name=self.cleaned_data['business_name'],
            phone=self.cleaned_data['phone'],
            address=self.cleaned_data['address'],
            approved=False  # default
        )
        return seller





class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['seller', 'approved']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Always start with empty queryset for subcategory
        self.fields['subcategory'].queryset = SubCategory.objects.none()

        # Determine the category to filter subcategories
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = SubCategory.objects.filter(category=self.instance.category)