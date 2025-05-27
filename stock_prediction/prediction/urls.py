from django.urls import path
from django.contrib.auth import views as auth_views
from .views import signup, login_view, logout_view, get_stock_data, predict_view # Import functions
from . import views
from .views import stock_history_view
urlpatterns = [
    path("", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("contact/", views.contact_view, name="contact"),
    path("signup/", signup, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("predict/", predict_view, name="predict"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("stock-history/<str:stock_symbol>/", stock_history_view, name="stock_history"),
    path("stock/<str:stock_symbol>/", get_stock_data, name="get_stock_data"),
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="prediction/password_reset.html"), name="password_reset"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="prediction/password_reset_sent.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="prediction/password_reset_confirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="prediction/password_reset_complete.html"), name="password_reset_complete"),
]
