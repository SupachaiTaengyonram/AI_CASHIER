# ตัวอย่างสคริปต์รันครั้งเดียว
from aicashier.models import Product
from aicashier.services import rag_service

def initialize_all_products():
    products = Product.objects.all()
    print(f"Found {products.count()} products. Starting indexing...")
    for p in products:
        rag_service.update_product_in_rag(p)
    print("All products indexed.")