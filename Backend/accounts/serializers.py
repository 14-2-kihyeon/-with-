# accounts/serializers.py
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

class CustomRegisterSerializer(RegisterSerializer):
    # ✅ email을 optional로
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        # ✅ email이 아예 없어도 키가 생기게
        data["email"] = self.validated_data.get("email", "")
        return data
