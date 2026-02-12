from django.shortcuts import render, redirect, get_object_or_404
from program.models import Zakaz, Product, Prodaj, ZakazProducts, Postav, PostavProducts, CashMovement, Contact, User, PostavCashMovement
from program.date import fun
from decimal import Decimal
from django.db.models import F
from datetime import date, timedelta


def log(req):
    if req.method == 'POST':
        login = req.POST.get("login")
        password = req.POST.get("password")

        try:
            user = User.objects.get(name=login)
        except User.DoesNotExist:
            return render(req, 'program/login.html', {'error': 'Пользователь не найден.'})

        if user.check_password(password):
            # Логика авторизации (например, установить cookie или записать сессию)
            print("вошел")
            response = redirect('/glavn/zakaz')
            
            # Устанавливаем cookie с именем пользователя
            response.set_cookie('username', user.name, max_age=3600)

            return response
        else:
            print("не")
            return render(req, 'program/login.html', {'error': 'Неверный пароль.'})
    else:
        return render(req, 'program/login.html')
    


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        # Проверяем наличие cookie с именем пользователя
        username = request.COOKIES.get('username')
        if not username:
            return render(request, 'error.html', {'message': 'Требуется войти в систему.'})
        
        # Проверяем роль пользователя
        try:
            user = User.objects.get(name=username)
            if user.name != 'beka':
                return render(request, 'error.html', {'message': 'Только администраторы могут просматривать эту страницу.'})
        except User.DoesNotExist:
            return render(request, 'error.html', {'message': 'Пользователь не найден.'})
        
        return view_func(request, *args, **kwargs)
    return wrapper



def prod(req):
    data = Prodaj.objects.all()
    return render(req, 'program/prod.html', {'data': data})



def products(req):
    data = Product.objects.all()
    return render(req, 'program/products.html', {'data': data})



def add_products(req):
    if req.method == 'POST':
        products = req.POST.getlist('product[]')
        prih_cens = req.POST.getlist('prih_cen[]')
        counts = req.POST.getlist('count[]')
        prih_date = req.POST['prih_date']
        postav_name = req.POST['postav']

        # Поиск поставщика по названию
        postav = Postav.objects.get(postav=postav_name)

        # Проверяем, существуют ли товары в базе данных
        existing_products = Product.objects.values_list("product", flat=True).filter(product__in=products)
        existing_products_set = set(existing_products)

        # Новые товары
        new_products = set(products) - existing_products_set

        # Обрабатываем каждый товар отдельно
        for i in range(len(products)):
            product_name = products[i]
            count = int(counts[i])
            prih_cen = Decimal(prih_cens[i])  # Преобразование строки в десятичное число

            if product_name in existing_products_set:
                # Обновляем количество существующего товара
                Product.objects.filter(product=product_name).update(count=F('count') + count)

                # Запись о поступлении денег от поставщика
                PostavCashMovement.objects.create(
                    amount=prih_cen * count,
                    movement_type='INCOME',
                    reason=f"Поставили товар {product_name}, кол-во: {count}",
                    created_at=prih_date,
                    postav_id=postav,
                    source="Товары",
                )

                # Общая запись о поступлении денег
                CashMovement.objects.create(
                    amount=prih_cen * count,
                    movement_type='INCOME',
                    reason=f"Поставили товар {product_name}, кол-во: {count}",
                    created_at=prih_date,
                    source="Товары",
                )
            elif product_name in new_products:
                # Создаем новый товар
                Product.objects.create(
                    product=product_name,
                    prih_cen=prih_cen,
                    count=count,
                    prih_date=prih_date,
                )

                # Запись о поступлении денег от поставщика
                PostavCashMovement.objects.create(
                    amount=prih_cen * count,
                    movement_type='INCOME',
                    reason=f"Поставили товар {product_name}, кол-во: {count}",
                    created_at=prih_date,
                    postav_id=postav,
                    source="Товары",
                )

                # Общая запись о поступлении денег
                CashMovement.objects.create(
                    amount=prih_cen * count,
                    movement_type='INCOME',
                    reason=f"Поставили товар {product_name}, кол-во: {count}",
                    created_at=prih_date,
                    source="Товары",
                )

        # После обработки всех товаров считаем баланс
        movements = PostavCashMovement.objects.filter(postav_id=postav.pk)
        if movements.exists():  # Проверяем, существуют ли записи движения денежных средств
            balance = calculate_balance(movements)
        else:
            balance = Decimal('0')  # Устанавливаем нулевой баланс, если записей нет

        # Обновляем общий баланс поставщика
        Postav.objects.filter(pk=postav.pk).update(total_cen=balance)

        return redirect('/glavn/product/')
    else:
        # Если запрос не POST, показываем страницу формы добавления продукции
        postv = Contact.objects.filter(contact_type="supplier")
        prod = Product.objects.filter(count__gt=0)
        return render(req, 'program/add_product.html', {"postv": postv, "prod":prod})


def prodaj(req):
    if req.method == 'POST':
        # Получаем необходимые данные из формы
        _fio = req.POST.get("fio")
        _product = req.POST.get("product")
        _cen = Decimal(req.POST.get("cen"))
        _prod_date = req.POST.get("prod_date")
        _count = int(req.POST.get("count"))

        # Проверяем наличие товара на складе
        stock_product = Product.objects.filter(product=_product).first()
        if not stock_product:
            return render(req, 'program/prodaj.html', {"error": "Данный товар отсутствует на складе"})

        # Проверяем достаточное количество товара
        if stock_product.count < _count:
            return render(req, 'program/prodaj.html', {"error": "Недостаточное количество товара на складе"})

        # Уменьшаем количество товара на складе
        stock_product.count -= _count
        stock_product.save()

        # Регистрируем продажу
        Prodaj.objects.create(
            fio=_fio,
            product=_product,
            cen=_cen,
            prod_date=_prod_date,
            count=_count,
            prod_form="Продано на месте",
            zakaz_id="0"
        )

        # Зарегистрируем приход средств от продажи
        CashMovement.objects.create(
            amount=_cen,
            movement_type='INCOME',
            reason=f"Продажа товара '{_product}', клиент: {_fio}",
            source=_fio,
            created_at=_prod_date,
        )
        print(1)
        return render(req, 'program/prodaj.html', {"success": "Продажа зарегистрирована успешно"})
    else:
        data1 = Contact.objects.filter(contact_type="customer")
        data2 = Product.objects.all()
        return render(req, 'program/prodaj.html', {"data1": data1, "data2": data2})



def zakaz(request):
    data = Zakaz.objects.filter(status=True).order_by("opl_date")
    day = date.today()
    super_cen = sum(z.total_cen for z in data)
    return render(request, 'program/index.html', {'data': data, "super_cen": super_cen, "day": day})



def close_zakaz(request):
    data = Zakaz.objects.filter(status=False).order_by("opl_date")
    super_cen = sum(z.total_cen for z in data)
    return render(request, 'program/close_zakaz.html', {'data': data, "super_cen": super_cen})


@admin_required
def add_zakaz(req):
    if req.method == 'POST':
        fio = req.POST['fio']
        opl_date = req.POST['opl_date']
        m_count = int(req.POST['m_count'])
        vznos = int(req.POST['vznos'])
        products = req.POST.getlist('product[]')
        prices = req.POST.getlist('cen[]')
        quantities = req.POST.getlist('count[]')

        # Проверяем доступность товаров на складе
        available_products = {}
        for product_name in products:
            product = Product.objects.filter(product=product_name).first()
            if product and product.count > 0:
                available_products[product_name] = product.count
            else:
                return render(req, 'program/add_zakaz.html', {"error": f"Товар '{product_name}' отсутствует на складе"})

        # Проверяем достаточность товаров на складе
        for idx, product_name in enumerate(products):
            requested_quantity = int(quantities[idx])
            if available_products.get(product_name, 0) < requested_quantity:
                return render(req, 'program/add_zakaz.html', {"error": f"Недостаточно товара '{product_name}' на складе"})

        # Создаем новый заказ
        total_price = sum(map(Decimal, prices))
        percent_value = total_price * Decimal("0.01")
        new_prices = [Decimal(price) - ((Decimal(price) / percent_value) * vznos * Decimal("0.01")) for price in prices]
        final_total_price = sum(new_prices)

        new_order = Zakaz.objects.create(
            fio=fio,
            slug="ttt",
            opl_date=opl_date,
            m_count=m_count,
            total_cen=final_total_price,
            vznos=vznos
        )

        # Обрабатываем товары в заказе
        for idx, product_name in enumerate(products):
            stock_product = Product.objects.get(product=product_name)
            requested_qty = int(quantities[idx])
            stock_product.count -= requested_qty
            stock_product.save()

            ZakazProducts.objects.create(
                product=product_name,
                cen=Decimal(new_prices[idx]),
                count=requested_qty,
                zakaz_id=new_order
            )

            Prodaj.objects.create(
                fio=fio,
                product=product_name,
                cen=Decimal(prices[idx]),
                prod_date=opl_date,
                count=requested_qty,
                prod_form="В рассрочку",
                zakaz_id=str(new_order.id)
            )

        CashMovement.objects.create(
            amount=vznos,
            movement_type='INCOME',
            reason=f"Оплата по рассрочке заказа #{new_order.pk}",
            source=fio,
            created_at=opl_date,
        )

        # Очищаем склад от нулевых позиций

        return redirect('/glavn/zakaz/')
    else:
        data1 = Contact.objects.filter(contact_type="customer")
        data2 = Product.objects.filter(count__gt=0)
        return render(req, 'program/add_zakaz.html', {"data1": data1, "data2": data2})



def rasroch(req, _id):
    if req.method == 'POST':
        del_id = req.POST.get('delete')
        if del_id:
            try:
                today = date.today()  
                formatted_date = today.strftime("%Y-%m-%d") 

                # Закрываем заказ и ставим пометку о выплате
                order_data = Zakaz.objects.filter(id=_id, status=True).first()
                Zakaz.objects.filter(id=_id, status=True).update(total_cen = 0)
                CashMovement.objects.create(
                    amount=order_data.total_cen,
                    movement_type='INCOME',
                    reason=f"Оплата по рассрочке заказа #{_id}",
                    source=order_data.fio,
                    created_at=formatted_date,
                )
                Prodaj.objects.filter(zakaz_id=del_id).update(prod_form="Рассрочка выплачена")
                Zakaz.objects.filter(id=del_id).update(status=False)
                return redirect('/glavn/zakaz')
            except Zakaz.DoesNotExist:
                pass

        if all(map(req.POST.get, ["opl", "date"])):
            _opl = Decimal(req.POST.get("opl"))
            _date = req.POST.get("date")

            # Получаем заказ из базы данных
            order_data = Zakaz.objects.filter(id=_id, status=True).first()
            if not order_data:
                return render(req, 'program/index.html', {"message": "Заказ не найден"})

            # Зарегистрируем приход средств от очередного платежа
            CashMovement.objects.create(
                amount=_opl,
                movement_type='INCOME',
                reason=f"Оплата по рассрочке заказа #{_id}",
                source=order_data.fio,
                created_at=_date,
            )

            # Базовые параметры заказа
            total_cen = order_data.total_cen
            current_m_count = order_data.m_count

            # Размер месячного платежа
            monthly_payment = total_cen / current_m_count

            # Смотрим, соответствует ли платеж норме
            if _opl < monthly_payment:
                return render(req, 'program/index.html', {"message": "Минимальная сумма платежа меньше установленной нормы"})

            # Рассчитываем оставшуюся задолженность
            remaining_debt = total_cen - _opl

            # Если долг погашен полностью
            if remaining_debt <= 0:
                # Закрытие заказа и установка статуса "закрыт"
                Zakaz.objects.filter(id=_id, status=True).update(
                    total_cen=0,
                    m_count=0,
                    opl_date=_date,
                    status=False  # Установка статуса False
                )
                return render(req, 'program/index.html', {"message": "Оплата произведена успешно. Заказ закрыт."})
            else:
                # Сохраняем новую дату и уменьшаем количество месяцев
                new_m_count = current_m_count - 1
                Zakaz.objects.filter(id=_id, status=True).update(
                    total_cen=remaining_debt,
                    m_count=new_m_count,
                    opl_date=_date
                )

    # Информация о состоянии заказа
    updated_order = Zakaz.objects.filter(id=_id).first()
    if updated_order is None:
        return render(req, 'program/error.html', {"message": "Заказ не найден"})

    # Готовые данные для рендера
    data = {
        'date': fun(str(updated_order.opl_date), updated_order.m_count),
        'cen': round(updated_order.total_cen / updated_order.m_count, 2) if updated_order.m_count > 0 else 0,
        'id': _id
    }

    return render(req, 'program/rasroch.html', data)


@admin_required
def edit_zakaz(req, _id):
    if req.method == 'POST':
        _opl_date = req.POST.get("opl_date")
        _product = req.POST.getlist("product[]")
        _cen = req.POST.getlist("cen[]")

        # Преобразуем цены в Decimal, предварительно заменяя запятые на точки
        _cen = [_cen_item.replace(',', '.') for _cen_item in _cen]

        # Обновляем данные заказа
        for i in range(len(_product)):
            product = Product.objects.get(product=_product[i])
            count = ZakazProducts.objects.filter(zakaz_id=_id, product=_product[i]).values("count")[0]["count"]

            # Обновляем продукцию в заказе
            ZakazProducts.objects.filter(zakaz_id=_id, product=_product[i]).update(cen=_cen[i])

        _total_cen = 0

        for i in range(len(_cen)):
            _total_cen += Decimal(_cen[i])

        # Обновляем основную информацию заказа
        Zakaz.objects.filter(id=_id).update(opl_date=_opl_date, total_cen=_total_cen)

    # Получаем обновлённую информацию
    data1 = Zakaz.objects.get(id=_id)
    date = str(data1.opl_date)
    data2 = ZakazProducts.objects.filter(zakaz_id=_id)

    return render(req, 'program/editor_zakaz.html', {"data1": data1, "opl_date": date, "data2": data2})


@admin_required
def docum_oform(request, _id):
    if request.method == 'POST':
        # Проверяем заполненность обязательных полей
        required_fields = ["client_phon", "address", "passport"]
        if not all(map(lambda field: bool(request.POST.get(field)), required_fields)):
            return render(request, 'program/oform.html', {"error_message": "Все поля обязательны для заполнения"})

        # Берём данные из POST-запроса
        client_phone = request.POST.get("client_phon")
        address = request.POST.get("address")
        passport = request.POST.get("passport")

        # Найти заказ по переданному id
        try:
            zakaz = Zakaz.objects.get(pk=_id)

            # Подбираем список товаров, относящихся к этому заказу
            products = ZakazProducts.objects.filter(zakaz_id=zakaz).values(
                'product',
                'cen',
                'count'
            )

            lst = []
            for i in products:
                lst.append(i["product"])
            join_prod = ", ".join(lst)

            # Контекст данных для шаблона
            data = {
                "id": zakaz.pk,
                "date": zakaz.opl_date,
                "name": zakaz.fio,
                "client_phon": client_phone,
                "address": address,
                "passport": passport,
                "products": products,
                "join_prod": join_prod,
                "m_count": zakaz.m_count,
                "total_cen": zakaz.total_cen,
                "opl": Decimal(zakaz.total_cen) / Decimal(zakaz.m_count),
                "all_opl": Decimal(zakaz.total_cen) + Decimal(zakaz.vznos),
                "k_opl": Decimal(zakaz.total_cen),
                "pred_opl": Decimal(zakaz.vznos)
            }
            print(data["products"])

            # Рендерим документ с этими данными
            return render(request, 'program/docum.html', {"data": data})

        except Zakaz.DoesNotExist:
            return redirect('/glavn/zakaz/')

    else:
        return render(request, 'program/oform.html')



def postav(req):
    data = Postav.objects.all()
    return render(req, 'program/postav.html', {'data': data})



def close_postav(req):
    data = Postav.objects.filter(status=False)
    return render(req, 'program/close_postav.html', {'data': data})
    


def edit_postav(req, _id):
    if req.method == 'POST':
        _opl_date = req.POST.get("opl_date")


        # Обновляем основную информацию заказа
        Postav.objects.filter(id=_id).update(opl_date=_opl_date)

    # Получаем обновлённую информацию
    data1 = Postav.objects.get(id=_id)
    date = str(data1.date)

    return render(req, 'program/editor_postav.html', {"data1": data1, "opl_date": date})
    


@admin_required
def postav_prod(req, _id):
    # Сначала получаем экземпляр Postav по переданной переменной _id
    postav_instance = get_object_or_404(Postav, pk=_id)

    movements = PostavCashMovement.objects.filter(postav_id=postav_instance).order_by("-created_at")
    balance = calculate_balance(movements)

    Postav.objects.filter(pk=_id).update(total_cen=balance)

    if req.method == 'POST':
        amount = float(req.POST.get('amount'))
        movement_type = req.POST.get('movement_type')
        reason = req.POST.get('reason')
        source = req.POST.get('source')
        date = req.POST.get('date')

        CashMovement.objects.create(
            amount=amount,
            movement_type=movement_type,
            reason=reason,
            source=source,
            created_at=date,
        )

        # Передаем postav_id как экземпляр модели Postav
        PostavCashMovement.objects.create(
            amount=amount,
            movement_type=movement_type,
            reason=reason,
            source=source,
            created_at=date,
            postav_id=postav_instance  # Здесь указываем экземпляр модели
        )

        Postav.objects.filter(pk=_id).update(total_cen=balance, date=date)

        return redirect(f'/glavn/postav_prod/{_id}/')

    return render(req, 'program/postav_prod.html', {'movements': movements, 'balance': balance})

def cash_register(req):
    movements = CashMovement.objects.all().order_by("-created_at")
    balance = calculate_balance(movements)

    if req.method == 'POST':
        amount = float(req.POST.get('amount'))
        movement_type = req.POST.get('movement_type')
        reason = req.POST.get('reason')
        source = req.POST.get('source')
        date = req.POST.get('date')

        CashMovement.objects.create(amount=amount, movement_type=movement_type, reason=reason, source=source, created_at = date)
        return redirect('/glavn/cash/')

    return render(req, 'program/cash.html', {'movements': movements, 'balance': balance})

def calculate_balance(movements):
    income_sum = sum(float(move.amount) for move in movements if move.movement_type == 'INCOME')
    outgo_sum = sum(float(move.amount) for move in movements if move.movement_type == 'OUTGO')
    return income_sum - outgo_sum



def contacts_view(req):
    # Получаем все контакты из базы данных

    contacts = Contact.objects.filter(contact_type="supplier")

    if req.method == 'POST':
        # Получаем данные из POST-запроса
        contact_type = req.POST.get('contact_type')
        name = req.POST.get('name')
        phone = req.POST.get('phone')
        email = req.POST.get('email')
        address = req.POST.get('address')

        # Создаем и сохраняем новый контакт
        Contact.objects.create(contact_type=contact_type, name=name, phone=phone, address=address)

        if contact_type == "supplier":
            day = date.today()
            Postav.objects.create(postav=name, slug="ttt", total_cen=0, date=day)

        # Перенаправляем на страницу контактов после успешного добавления
        return redirect('/glavn/contacts/')

    return render(req, 'program/contact.html', {'contacts': contacts})



def client_contacts_view(req):
    # Получаем все контакты из базы данных
    contacts = Contact.objects.filter(contact_type="customer")

    if req.method == 'POST':
        # Получаем данные из POST-запроса
        contact_type = req.POST.get('contact_type')
        name = req.POST.get('name')
        phone = req.POST.get('phone')
        email = req.POST.get('email')
        address = req.POST.get('address')

        # Создаем и сохраняем новый контакт
        Contact.objects.create(contact_type=contact_type, name=name, phone=phone, address=address)

        # Перенаправляем на страницу контактов после успешного добавления
        return redirect('/glavn/client_contacts/')

    return render(req, 'program/client_contact.html', {'contacts': contacts})