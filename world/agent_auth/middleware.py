"""
Agent Auth Middleware
豁免 API 路径的 CSRF 保护
"""
import re
from django.utils.deprecation import MiddlewareMixin


class ApiCsrfExemptMiddleware(MiddlewareMixin):
    """
    豁免 /api/* 路径的 CSRF 保护
    
    这些 API 不使用 cookie 认证，而是使用 API Key，
    因此不需要 CSRF 保护。
    """
    
    EXEMPT_URLS = [
        r'^/api/.*$',
    ]
    
    def process_request(self, request):
        # 检查请求路径是否匹配豁免规则
        path = request.path_info
        for pattern in self.EXEMPT_URLS:
            if re.match(pattern, path):
                # 标记请求为 CSRF 豁免
                request.csrf_processing_done = True
                break
        return None