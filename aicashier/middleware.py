# aicashier/middleware.py
"""
Custom middleware สำหรับจัดการ cache และ security headers
"""

class NoCacheMiddleware:
    """
    Middleware ที่ป้องกันการ cache หน้า sensitive pages
    โดยเฉพาะหน้า ai_disabled และ home page
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # ตรวจสอบว่าเป็นหน้า sensitive หรือไม่
        path = request.path
        sensitive_paths = ['/home/', '/ai/disabled/']
        
        if any(path.startswith(p) for p in sensitive_paths):
            # ตั้ง headers ป้องกัน caching
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, post-check=0, pre-check=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response
