from django.contrib import admin
from .models import Category,Review,Product,ProImage,Cart,Cartitems
# Register your models here.
admin.site.register(Category)
admin.site.register(Review)
admin.site.register(Product)
admin.site.register(ProImage)
admin.site.register(Cart)
admin.site.register(Cartitems)