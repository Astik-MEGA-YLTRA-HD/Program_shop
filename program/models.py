
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Product(models.Model):
    product = models.CharField(max_length=100)
    prih_cen = models.DecimalField(max_digits=12, decimal_places=2)
    prih_date = models.DateField()
    count = models.SmallIntegerField()

class Zakaz(models.Model):
    fio = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    opl_date = models.DateField()
    vznos = models.DecimalField(max_digits=12, decimal_places=2)
    total_cen = models.DecimalField(max_digits=12, decimal_places=2)
    m_count = models.IntegerField()
    status = models.BooleanField(default=True)

class ZakazProducts(models.Model):
    product = models.CharField(max_length=100)
    cen = models.DecimalField(max_digits=12, decimal_places=2)
    count = models.SmallIntegerField()
    zakaz_id = models.ForeignKey('Zakaz', on_delete=models.CASCADE)

class Postav(models.Model):
    postav = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100)
    total_cen = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()

class PostavCashMovement(models.Model):
    TYPE_CHOICES = (
        ('INCOME', 'Приход'),
        ('OUTGO', 'Расход'),
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    movement_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='INCOME')
    reason = models.TextField(verbose_name="Причины")
    source = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateField()
    postav_id = models.ForeignKey('Postav', on_delete=models.CASCADE)

class PostavProducts(models.Model):
    product = models.CharField(max_length=100)
    cen = models.DecimalField(max_digits=12, decimal_places=2)
    count = models.SmallIntegerField()
    prih = models.BooleanField(default=False)
    postav_id = models.ForeignKey('Postav', on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    
class Document(models.Model):
    fio = models.CharField(max_length=100)
    postav = models.CharField(max_length=50)
    product = models.CharField(max_length=100)
    count = models.SmallIntegerField()

class Prodaj(models.Model):
    fio = models.CharField(max_length=100)
    product = models.CharField(max_length=100)
    prod_date = models.DateField()
    cen = models.DecimalField(max_digits=12, decimal_places=2)
    count = models.SmallIntegerField()
    prod_form = models.TextField(max_length=20)
    zakaz_id = models.TextField()

class CashMovement(models.Model):
    TYPE_CHOICES = (
        ('INCOME', 'Приход'),
        ('OUTGO', 'Расход'),
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма")
    movement_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='INCOME', verbose_name="Тип операции")
    reason = models.TextField(verbose_name="Причины")
    source = models.CharField(max_length=100, null=True, blank=True, verbose_name="Источник/Назначение")
    created_at = models.DateField()

    def __str__(self):
        return f"{self.amount} ({self.get_movement_type_display()} - {self.reason})"

    class Meta:
        verbose_name = "Денежное движение"
        verbose_name_plural = "Денежные движения"

class Contact(models.Model):
    CONTACT_TYPES = (
        ('supplier', 'Поставщик'),
        ('customer', 'Клиент'),
    )

    contact_type = models.CharField(max_length=10, choices=CONTACT_TYPES, verbose_name="Тип контакта")
    name = models.CharField(unique=True, max_length=100, verbose_name="ФИО или Организация")
    phone = models.CharField(blank=True, max_length=20, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.CharField(blank=True, max_length=200, verbose_name="Адрес")

    def __str__(self):
        return f"{self.contact_type}: {self.name}"

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"

class User(models.Model):
    name = models.CharField(max_length=55)
    password = models.CharField(max_length=128)  # Длина для хранения хеша пароля

    def set_password(self, raw_password):
        """Хеширует пароль перед сохранением"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Проверяет соответствие введенного пароля хранимому хешу"""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name