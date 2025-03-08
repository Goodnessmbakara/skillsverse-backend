import base64
import json
import nacl.signing
import nacl.encoding


def verify_sui_signature(
    wallet_address, signature, message="Login to Job Matching Platform"
):
    """
    Verify the signature was signed by the wallet owner.
    """

    try:
        decoded_signature = base64.b64decode(signature)
        verify_key = nacl.signing.VerifyKey(
            wallet_address, encoder=nacl.encoding.HexEncoder
        )
        verify_key.verify(message.encode(), decoded_signature)
        return True
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False
