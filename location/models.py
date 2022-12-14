from django.db import models

class Location(models.Model):
    address = models.CharField(max_length=200, unique=True, verbose_name='Адрес')
    lat = models.FloatField(null=True, blank=True, verbose_name='Широта координат')
    lng = models.FloatField(null=True, blank=True, verbose_name='Долгота координат')
    update_date = models.DateTimeField(auto_now=True, db_index=True, verbose_name='Когда был запрос')

    def __str__(self):
        return '({} {}) {}'.format(self.lng, self.lat, self.address)
