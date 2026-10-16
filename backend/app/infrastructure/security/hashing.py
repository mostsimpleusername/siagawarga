"""
app/infrastructure/security/hashing.py
Utilitas hashing kata sandi native menggunakan bcrypt (KNF-03).
"""
import bcrypt


def hash_kata_sandi(kata_sandi: str) -> str:
    """Mengenkripsi kata sandi menggunakan algoritma bcrypt native."""
    pwd_bytes = kata_sandi.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


get_password_hash = hash_kata_sandi


def verifikasi_kata_sandi(kata_sandi_plain: str, kata_sandi_hash: str) -> bool:
    """Memvalidasi kecocokan kata sandi plain terhadap hash bcrypt."""
    try:
        plain_bytes = kata_sandi_plain.encode("utf-8")
        hash_bytes = kata_sandi_hash.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception:
        return False
