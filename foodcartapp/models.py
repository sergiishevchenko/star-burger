import copy

from django.db import models
from django.db.models import Sum, F
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from functools import reduce

from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def get_orders(self):
        return self.annotate(order_price=Sum(F('ordered_items__price')*F('ordered_items__quantity')))

    def get_accessible_restaurants(self):
        items_menu = RestaurantMenuItem.objects.select_related('product', 'restaurant')
        for order in self:
            ready_products = []
            for order_product in order.ordered_items.all():
                ready_products.append([item_menu.restaurant for item_menu in items_menu if order_product.product_id == item_menu.product.pk])
            are_available_restaurants = reduce(set.intersection, map(set, ready_products))
            order.are_available_restaurants = copy.deepcopy(are_available_restaurants)
        return self


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        UNPROCESSED = 'UNPROCESSED', _('Необработанный')
        IN_PROGRESS = 'IN_PROGRESS', _('В процессе выполнения')
        DONE = 'DONE', _('Выполнен')

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', _('Наличностью')
        ELECTRIC = 'ELECTRIC', _('Электронно')
        NO = 'NO', _('Не указан')

    address = models.CharField('Адрес доставки', max_length=100)
    firstname = models.CharField('Имя', blank=True, max_length=20)
    lastname = models.CharField('Фамилия', max_length=20)
    comment = models.TextField('Комментарий', blank=True)
    phonenumber = PhoneNumberField('Номер телефона', db_index=True)
    status = models.CharField('Статус', max_length=20, choices=OrderStatus.choices, default=OrderStatus.IN_PROGRESS, db_index=True)
    payment_method = models.CharField('Способ оплаты', max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.NO, db_index=True)
    selected_restaurant = models.ForeignKey(Restaurant, null=True, blank=True, related_name='orders', verbose_name='Ресторан, который готовит заказ', on_delete=models.SET_NULL)
    called_at = models.DateTimeField('Время звонка', blank=True, null=True)
    delivered_at = models.DateTimeField('Время доставки', blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='Дата создания заказа', auto_now=True, db_index=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return '{} - {}'.format(self.lastname, self.address)


class ProductQuantity(models.Model):
    quantity = models.PositiveIntegerField('Количество продукта', validators=[MinValueValidator(1)])
    price = models.DecimalField('Цена', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='ordered_items', on_delete=models.PROTECT)
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт - количество'
        verbose_name_plural = 'Продукты - количество'

    @property
    def order_price(self, save=True):
        return self.quantity * self.product.price
