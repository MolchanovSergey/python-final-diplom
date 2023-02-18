import requests
from yaml import load as load_yaml, Loader
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from orders.celery import app

from .models import Shop, Category, Product, Parameter, ProductParameter, ProductInfo

@app.task()
def get_import(partner, url):
    if url:
        validate_url = URLValidator()
        try:
            validate_url(url)
        except ValidationError as e:
            return {'Status': False, 'Error': str(e)}
        else:
            stream = requests.get(url).content

        data = load_yaml(stream, Loader=Loader)
        try:
            shop, _ = Shop.objects.get_or_create(name=data['shop'],
                                             user_id=partner)
        except IntegrityError as e:
            return {'Status': False, 'Error': str(e)}

        for category in data['categories']:
            category_object, _ = Category.objects.get_or_create(
                id=category['id'], name=category['name'])
            category_object.shops.add(shop.id)
            category_object.save()

        ProductInfo.objects.filter(shop_id=shop.id).delete()
        for item in data['goods']:
            product, _ = Product.objects.get_or_create(
                name=item['name'], category_id=item['category']
            )
            product_info = ProductInfo.objects.create(
                product_id=product.id, external_id=item['id'],
                model=item['model'], price=item['price'],
                price_rrc=item['price_rrc'], quantity=item['quantity'],
                shop_id=shop.id
            )
            for name, value in item['parameters'].items():
                parameter_object, _ = Parameter.objects.get_or_create(
                    name=name
                )
                ProductParameter.objects.create(
                    product_info_id=product_info.id,
                    parameter_id=parameter_object.id, value=value
                )
        return {'Status': True}
    return {'Status': False, 'Errors': 'Url is false'}
