from django import forms
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



from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['seller', 'approved']
