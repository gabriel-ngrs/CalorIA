from py_vapid import Vapid
import base64

v = Vapid()
v.generate_keys()
priv_pem = v.private_pem()
s = __import__("cryptography.hazmat.primitives.serialization", fromlist=["x"])
pub_b64 = base64.urlsafe_b64encode(
    v._private_key.public_key().public_bytes(
        s.Encoding.X962,
        s.PublicFormat.UncompressedPoint
    )
).rstrip(b"=").decode()
open("/tmp/vapid_private.pem", "wb").write(priv_pem)
print("Chave privada salva em /tmp/vapid_private.pem")
print("VAPID_PUBLIC_KEY=" + pub_b64)
