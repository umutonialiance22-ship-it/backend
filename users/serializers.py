from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Fields match what the frontend sends:
      { full_name, email, phone, password }
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "password"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            phone=validated_data.get("phone", ""),
            password=validated_data["password"],
            role=User.CUSTOMER,  # public registration always gets CUSTOMER
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(
            request=self.context.get("request"),
            email=data["email"].lower(),
            password=data["password"],
        )
        if user is None:
            raise serializers.ValidationError(
                {"detail": "No account found with that email and password."}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "This account has been deactivated."}
            )
        data["user"] = user
        return data


class MeSerializer(serializers.ModelSerializer):
    """
    Shape the frontend expects from GET /api/auth/me/:
      { full_name, role, is_vip }
    """
    class Meta:
        model = User
        fields = ["full_name", "role", "is_vip", "email", "phone"]


class UserSummarySerializer(serializers.ModelSerializer):
    """Used by manager endpoints to list customers."""
    membership = serializers.SerializerMethodField()
    name = serializers.CharField(source="full_name")
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "email", "phone", "membership", "status"]

    def get_membership(self, obj):
        return "VIP" if obj.is_vip else "Regular"

    def get_status(self, obj):
        return "Active" if obj.is_active else "Inactive"
