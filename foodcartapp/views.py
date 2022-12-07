import json

from django.http import JsonResponse
from django.templatetags.static import static

from .models import Product, Order, ProductQuantity


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


def register_order(request):
    try:
        raw_order = json.loads(request.body.decode())
    except ValueError as error:
        return 'Ошибка при создании нового заказа: {}'.format(error)

    address = raw_order.get('address', '')
    firstname = raw_order.get('firstname', '')
    lastname = raw_order.get('lastname', '')
    phonenumber = raw_order.get('phonenumber', '')
    products = raw_order.get('products', [])

    new_order = Order.objects.create(address=address, firstname=firstname, lastname=lastname, phonenumber=phonenumber)

    new_product_quantity = [
        ProductQuantity.objects.create(
            product=Product.objects.get(id=item.get('product', '')),
            quantity=item.get('quantity', ''),
            order=new_order
        ) for item in products if products
    ]

    if (new_order and new_product_quantity):
        return 'Заказ успешно оформлен'
    else:
        return 'При оформлении заказа были допущены ошибки!'
