
# 작성자만 수정/삭제   
# 우리가 수업시간에 배운 permissions활용법이랑 조금 다름

# 우리가 배운 DRF 기본 permissions들은 대부분 '요청자 인증 여부'까지만 보여줌
# "이 객체의 작성자인지(=object-level permission)"를 자동으로 판단해주지 않음
# 커스텀 permission(객체 단위 권한)이 가장 정석이고 실무에서도 흔히 쓰는 방식



# posts/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user

class IsCommentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
    


