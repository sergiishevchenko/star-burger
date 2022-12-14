from rest_framework.decorators import api_view
from rest_framework.response import Response

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
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    products = request.data.get('products', [])

    create_order = Order.objects.create(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address']
    )

    create_product_quantity = []
    for order in products:
        serializer_pq = ProductQuantitySerializer(data=order)
        serializer_pq.is_valid(raise_exception=True)

        create_product_quantity.append(ProductQuantity(
            product=serializer_pq.validated_data['product'],
            order=create_order,
            quantity=serializer_pq.validated_data['quantity'],
            price=serializer_pq.validated_data['product'].price * serializer_pq.validated_data['quantity'],

        ))

    ProductQuantity.objects.bulk_create(create_product_quantity)

    return Response(OrderSerializer(create_order).data)