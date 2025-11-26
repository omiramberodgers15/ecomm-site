# core/models.py
from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User

from django.utils.text import slugify

# core/models.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings


# ---------- CATEGORY ----------
class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

            # Ensure unique slug
            base_slug = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# ---------- SUBCATEGORY ----------
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"



# ---------- SELLER ----------
class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="seller_profile")
    business_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    approved = models.BooleanField(default=False)  # ✅ Admin approves seller

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name


class Product(models.Model):

    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="products", null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, related_name="products", null=True, blank=True)
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=300, blank=True, null=True)
     #color_options = models.JSONField(blank=True, null=True)  # store available colors ['red','blue']
    # other fields...
    description = models.TextField()
    hook = models.CharField(max_length=200, blank=True, null=True, help_text="Short marketing tagline")
    is_clearance = models.BooleanField(default=False)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    # NEW initial/original price (strike-through price)
    initial_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="The original price before discount"
    )
    min_order = models.PositiveIntegerField(default=1)

    
    color_options = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated color names")
    shipping_info = models.TextField(blank=True, null=True)
    product_protection = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    related_searches = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='related_to+'
    )

    recommended_from_supplier = models.ManyToManyField(
    'Supplier',  
    blank=True,
    related_name='recommended_products'
    )
    approved = models.BooleanField(default=False)


    def __str__(self):
        return self.name

    @property
    def color_count(self):
        """Return the number of colors available."""
        if self.color_options:
            return len([c.strip() for c in self.color_options.split(',') if c.strip()])
        return 0    

    @property
    def average_rating(self):
        return self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    @property
    def review_count(self):
        return self.reviews.count()



class PriceOption(models.Model):
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_options')
    min_quantity = models.PositiveIntegerField(default=1)
    max_quantity = models.PositiveIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name}: {self.min_quantity}-{self.max_quantity or '∞'} pcs @ {self.price}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    avatar = models.ImageField(upload_to='review_avatars/', blank=True, null=True)  # New field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} - {self.product.name}"


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    color = models.CharField(max_length=50, blank=True, null=True)  # color for this image

    def __str__(self):
        return f"Image for {self.product.name}"




# ---------- CART ITEM ----------
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.quantity * self.product.base_price

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.user.username})"


# ---------- ORDER ----------
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    items = models.ManyToManyField(CartItem, related_name='orders')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_total(self):
        self.total_price = sum([item.total_price for item in self.items.all()])
        self.save()
        return self.total_price

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} - {'Paid' if self.paid else 'Pending'}"



@receiver(post_save, sender=Seller)
def notify_seller_approval(sender, instance, created, **kwargs):
    if not created and instance.approved:
        send_mail(
            "Your Seller Account Has Been Approved!",
            f"Hello {instance.user.username},\n\nYour seller account '{instance.business_name}' has been approved. You can now log in and start adding products.",
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=True,
        )





class Message(models.Model):
    sender = models.ForeignKey(User, related_name='core_sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='core_received_messages', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', related_name='messages', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.read})"



class Deal(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return self.name



class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
    )

    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"



class TicketReply(models.Model):
    ticket = models.ForeignKey('SupportTicket', on_delete=models.CASCADE, related_name='replies')
    reply_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to Ticket #{self.ticket.id}"

