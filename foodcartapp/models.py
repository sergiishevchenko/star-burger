from django.db import models
from django.db.models import Sum, F
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField


class OrderStatus(models.TextChoices):
    IN_PROGRESS = 'IN_PROGRESS', _('Необработанный')
    RESTAURANT = 'IN_RESTAURANT', _('Передан в ресторан')
    COURIER = 'IN_WAY', _('Передан курьеру')
    DONE = 'DONE', _('Выполнен')


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


class Order(models.Model):
    address = models.CharField('Адрес доставки', max_length=100)
    firstname = models.CharField('Имя', blank=True, max_length=20)
    lastname = models.CharField('Фамилия', max_length=20)
    comment = models.TextField('Комментарий', blank=True)
    phonenumber = PhoneNumberField('Номер телефона', db_index=True)
    status = models.CharField('Статус', max_length=20, choices=OrderStatus.choices, default=OrderStatus.IN_PROGRESS, db_index=True)
    called_at = models.DateTimeField('Время звонка', blank=True, null=True)
    delivered_at = models.DateTimeField('Время доставки', blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return '{} - {}'.format(self.lastname, self.address)

    @property
    def order_price(self):
        products = ProductQuantity.objects\
            .filter(order=self.id)\
                .values('product__price', 'quantity')\
                    .annotate(result=F('product__price') * F('quantity'))\
                        .aggregate(Sum('result'))\
                            .get('result__sum', 0.00)
        return products

    order_price.fget.short_description = 'Стоимость заказа'


class ProductQuantity(models.Model):
    quantity = models.PositiveIntegerField('Количество продукта')
    price = models.DecimalField('Цена', default=0, max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    product = models.ForeignKey(Product, related_name='product_quantity', on_delete=models.PROTECT)
    order = models.ForeignKey(Order, related_name='product_quantity', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт - количество'
        verbose_name_plural = 'Продукты - количество'
