from django.urls import path
from program import views

urlpatterns = [
    path('', views.log),
    path('zakaz/', views.zakaz),
    path('close_zakaz/', views.close_zakaz),
    path('add_zakaz/', views.add_zakaz),
    path('rasroch/<int:_id>/', views.rasroch),
    path('editor/<int:_id>/', views.edit_zakaz),
    path('oform/<int:_id>/', views.docum_oform),
    path('product/', views.products),
    path('add_product/', views.add_products),
    path('prodaj/', views.prodaj),
    path('prod/', views.prod),
    path('postav/', views.postav),
    path('editor/postav/<int:_id>/', views.edit_postav),
    path('close_postav/', views.close_postav),
    path('postav_prod/<int:_id>/', views.postav_prod),
    path('cash/', views.cash_register, name='cash_register'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('client_contacts/', views.client_contacts_view, name='client_contacts'),
]