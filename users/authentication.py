# authentication.py
from rest_framework import exceptions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from eth_keys import keys
from eth_hash.auto import keccak
import secrets
from drf_spectacular.utils import extend_schema_serializer
from drf_spectacular.types import OpenApiTypes

from django.contrib.auth import get_user_model

User = get_user_model()

@extend_schema_serializer(
    request_fields={
        'wallet_address': OpenApiTypes.STR,
        'signature': OpenApiTypes.STR,
    }
)

class WalletAuthenticationBackend:
    @staticmethod
    def validate_signature(wallet_address, signature, nonce):
        try:
            # Construct the message
            message = f"Login nonce: {nonce}".encode('utf-8')
            
            # Ethereum signed message prefix
            prefix = b"\x19Ethereum Signed Message:\n" + str(len(message)).encode()
            prefixed_message = prefix + message
            
            # Hash the message
            message_hash = keccak(prefixed_message)
            
            # Convert signature from hex
            signature_bytes = bytes.fromhex(signature[2:] if signature.startswith('0x') else signature)
            
            # Recover public key
            signature_obj = keys.Signature(signature_bytes)
            public_key = signature_obj.recover_public_key_from_msg_hash(message_hash)
            
            # Derive address from public key
            address_bytes = keccak(public_key.to_bytes())[-20:]
            recovered_address = '0x' + address_bytes.hex()
            
            return recovered_address.lower() == wallet_address.lower()
            
        except Exception as e:
            print(f"Signature validation error: {str(e)}")
            return False

class WalletTokenObtainSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        wallet_address = attrs.get('wallet_address', '').lower()
        signature = attrs.get('signature', '')
        
        try:
            user = User.objects.get(wallet_address=wallet_address)
            
            if not self.__class__.validate_signature(wallet_address, signature, user.nonce):
                raise exceptions.AuthenticationFailed('Invalid signature')
            
            # Rotate nonce after successful validation
            user.refresh_nonce()
            
            refresh = self.get_token(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'wallet_address': user.wallet_address,
                'user_type': user.user_type
            }
            
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
            
class WalletTokenObtainPairView(TokenObtainPairView):
    serializer_class = WalletTokenObtainSerializer
    
    @extend_schema(
        summary="Wallet Login",
        description="Authenticate using wallet signature",
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)