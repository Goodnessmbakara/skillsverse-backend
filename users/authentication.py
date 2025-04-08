# authentication.py
from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import secrets
import eth_keys
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView 

User = get_user_model()

class WalletAuthenticationBackend:
    def authenticate(self, request, wallet_address=None, signature=None):
        try:
            user = User.objects.get(wallet_address=wallet_address)
            message_hash = defunct_hash_message(text=user.nonce)
             # Verify signature
            message = f"Login nonce: {user.nonce}".encode('utf-8')
            signature_bytes = bytes.fromhex(signature[2:]) if signature.startswith('0x') else bytes.fromhex(signature)
            
            pub_key = eth_keys.keys.Signature(signature_bytes).recover_public_key_from_msg(message)
            recovered_address = pub_key.to_checksum_address()
            
            if recovered_address.lower() == wallet_address.lower():
                user.nonce = secrets.token_hex(16)
                user.save()
                return user
            return None
        except User.DoesNotExist:
            return None

class WalletTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        wallet_address = attrs.get("wallet_address")
        signature = attrs.get("signature")

        user = WalletAuthenticationBackend().authenticate(
            self.context['request'],
            wallet_address=wallet_address,
            signature=signature
        )

        if not user:
            raise exceptions.AuthenticationFailed('Invalid wallet signature')

        refresh = self.get_token(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "wallet_address": user.wallet_address,
            "user_type": user.user_type
        }

        return data

class WalletTokenObtainPairView(TokenObtainPairView):
    serializer_class = WalletTokenObtainPairSerializer