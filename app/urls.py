from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


app_name = 'alexienu'

urlpatterns = [
    path('', views.index, name='index'),
    path('add_form/', views.add_form, name='add_form'),
    path('add/', views.add, name='add'),

    path('account/<str:account_name>/', views.account, name='account'),

    path('login/', views.AlexieNuLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page="/alexienu/"), name='logout'),
]
