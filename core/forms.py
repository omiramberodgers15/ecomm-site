# forms.py
from django import forms
from .models import Product, SubCategory
from django.contrib.auth.models import User
from .models import Seller

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

    # Step 1: override __init__ to filter subcategories
    def __init__(self, *args, **kwargs):
        category_id = None

        # GET initial category if editing existing product
        if "instance" in kwargs and kwargs["instance"]:
            category_id = kwargs["instance"].category_id

        # GET posted category (user changes category)
        if "data" in kwargs:
            category_id = kwargs["data"].get("category")

        super().__init__(*args, **kwargs)

        # filter subcategories dynamically
        if category_id:
            self.fields["subcategory"].queryset = SubCategory.objects.filter(category_id=category_id)
        else:
            self.fields["subcategory"].queryset = SubCategory.objects.none()
