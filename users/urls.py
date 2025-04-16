from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import NonceView
from .authentication import WalletTokenObtainPairView

urlpatterns = [
    path('auth/nonce/<str:wallet_address>/', NonceView.as_view(), name='nonce'),
    path('auth/login', WalletTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh',TokenRefreshView.as_view(), name='token_refresh'),
]
