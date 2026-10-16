"""
api/index.py
Entry point Serverless Function untuk Vercel Python Runtime.
Mengimpor instance FastAPI app dari main.py dan mengeksposnya ke Vercel.
"""
import sys
import os

# Tambahkan root path ke sys.path agar seluruh modul app dapat diimpor
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Impor FastAPI app dari main.py
from main import app
