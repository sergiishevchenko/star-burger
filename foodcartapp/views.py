import json

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static

from .models import Product, Order, ProductQuantity
from .serializers import OrderSerializer, ProductQuantitySerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@transaction.atomic
@api_view(['POST'])
def register_order(request):
    raw_order = json.loads(json.dumps(request.data))
    serializer = OrderSerializer(data=raw_order)
    serializer.is_valid(raise_exception=True)

    for product in raw_order['products']:
        product_serializer = ProductQuantitySerializer(data=product)
        product_serializer.is_valid(raise_exception=True)


    address = raw_order.get('address', '')
    firstname = raw_order.get('firstname', '')
    lastname = raw_order.get('lastname', '')
    phonenumber = raw_order.get('phonenumber', '')
    products = raw_order.get('products', [])

    new_order = Order.objects.create(address=address, firstname=firstname, lastname=lastname, phonenumber=phonenumber)
    [ProductQuantity.objects.create(product=Product.objects.get(id=item.get('product', '')), quantity=item.get('quantity', ''), order=new_order) for item in products if products]

    return Response(OrderSerializer(new_order).data, status=status.HTTP_201_CREATED)