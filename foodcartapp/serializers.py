from rest_framework import serializers

from .models import Order, ProductQuantity


class ProductQuantitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductQuantity
        fields = ('quantity', 'product',)
        read_only_fields = ('order',)


class OrderSerializer(serializers.ModelSerializer):
    products = ProductQuantitySerializer(allow_empty=False, many=True, write_only=True)

    class Meta:
        model = Order
        fields = ('products', 'address', 'firstname', 'lastname', 'phonenumber',)
