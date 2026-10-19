from django.contrib.auth.views import LoginView,LogoutView
from django.urls import path
from . import views
urlpatterns=[
 path('',views.dashboard,name='dashboard'),path('register/',views.register_view,name='register'),
 path('login/',LoginView.as_view(template_name='login.html'),name='login'),path('logout/',LogoutView.as_view(),name='logout'),
 path('card/',views.card_view,name='card'),path('card/toggle/',views.toggle_card,name='toggle_card'),
 path('topup/',views.topup,name='topup'),path('transfer/',views.transfer,name='transfer'),
 path('transactions/',views.transactions,name='transactions'),path('favorites/',views.favorites,name='favorites'),
 path('favorites/add/',views.add_favorite,name='add_favorite'),path('favorites/delete/<int:pk>/',views.delete_favorite,name='delete_favorite'),
 path('notifications/',views.notifications,name='notifications'),path('profile/',views.profile,name='profile')]
