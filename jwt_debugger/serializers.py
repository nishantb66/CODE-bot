from rest_framework import serializers

# Supported algorithms. "none" is only allowed when explicitly enabled.
ALLOWED_ALGORITHMS = [
    'HS256', 'HS384', 'HS512',
    'RS256', 'RS384', 'RS512',
    'ES256', 'ES384', 'ES512',
    'PS256', 'PS384', 'PS512',
    'none',
]

SYMMETRIC_ALGORITHMS = {'HS256', 'HS384', 'HS512'}
ASYMMETRIC_ALGORITHMS = {
    'RS256', 'RS384', 'RS512',
    'ES256', 'ES384', 'ES512',
    'PS256', 'PS384', 'PS512',
}


class DecodeRequestSerializer(serializers.Serializer):
    token = serializers.CharField(trim_whitespace=True)
    secret = serializers.CharField(required=False, allow_blank=True, allow_null=True, trim_whitespace=True)
    algorithm = serializers.CharField(required=False, default='auto', trim_whitespace=True)
    verify_signature = serializers.BooleanField(required=False, default=True)
    audience = serializers.CharField(required=False, allow_blank=True, allow_null=True, trim_whitespace=True)
    issuer = serializers.CharField(required=False, allow_blank=True, allow_null=True, trim_whitespace=True)
    leeway_seconds = serializers.IntegerField(required=False, default=0, min_value=0, max_value=86400)
    allow_insecure_none = serializers.BooleanField(required=False, default=False)

    def validate_algorithm(self, value: str) -> str:
        if value == 'auto':
            return value
        if value not in ALLOWED_ALGORITHMS:
            raise serializers.ValidationError('Unsupported algorithm')
        return value

    def validate(self, attrs):
        alg = attrs.get('algorithm', 'auto')
        if alg == 'none' and not attrs.get('allow_insecure_none', False):
            raise serializers.ValidationError({'algorithm': 'Algorithm "none" is blocked unless explicitly allowed.'})
        return attrs


class EncodeRequestSerializer(serializers.Serializer):
    header = serializers.JSONField()
    payload = serializers.JSONField()
    secret = serializers.CharField(required=False, allow_blank=True, allow_null=True, trim_whitespace=True)
    algorithm = serializers.ChoiceField(choices=ALLOWED_ALGORITHMS[:-1])  # exclude none by default
    expires_in_seconds = serializers.IntegerField(required=False, default=3600, min_value=0, max_value=604800)
    include_iat = serializers.BooleanField(required=False, default=True)
    allow_insecure_none = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        alg = attrs.get('algorithm')
        allow_none = attrs.get('allow_insecure_none', False)
        if alg == 'none' and not allow_none:
            raise serializers.ValidationError({'algorithm': 'Algorithm "none" is blocked unless explicitly allowed.'})

        if alg in SYMMETRIC_ALGORITHMS and not attrs.get('secret'):
            raise serializers.ValidationError({'secret': 'A shared secret is required for HS* algorithms.'})

        if alg in ASYMMETRIC_ALGORITHMS and not attrs.get('secret'):
            raise serializers.ValidationError({'secret': 'A PEM-encoded private key is required for this algorithm.'})

        return attrs
