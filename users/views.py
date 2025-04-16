from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

class NonceView(APIView):
    @extend_schema(
        parameters=[],
        responses={
            200: {'description': 'Current nonce for wallet address'},
            201: {'description': 'New user created with nonce'}
        }
    )
    def get(self, request, wallet_address):
        try:
            user = User.objects.get(wallet_address__iexact=wallet_address)
            return Response({'nonce': user.nonce})
        except User.DoesNotExist:
            user = User.objects.create_user(wallet_address=wallet_address)
            return Response({'nonce': user.nonce}, status=status.HTTP_201_CREATED)


class WalletSignInView(APIView):
    def post(self, request):
        wallet_address = request.data.get('wallet_address')
        
        try:
            user = User.objects.get(wallet_address=wallet_address)
        except User.DoesNotExist:
            return Response({"error": "Invalid wallet address."}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })

class WalletSignUpView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": serializer.data,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
