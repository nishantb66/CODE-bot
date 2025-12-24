"""
JWT Debugger API views.
Provides endpoints to inspect and generate JWTs with clear warnings.
"""
from datetime import datetime, timezone
import logging
import jwt
from jwt import InvalidTokenError, ExpiredSignatureError, InvalidSignatureError, InvalidAlgorithmError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    DecodeRequestSerializer,
    EncodeRequestSerializer,
    ALLOWED_ALGORITHMS,
    SYMMETRIC_ALGORITHMS,
    ASYMMETRIC_ALGORITHMS,
)
from .services import KeyGeneratorService, CodeGeneratorService, SecurityScannerService

logger = logging.getLogger(__name__)


class JWTDecodeAPIView(APIView):
    """
    Inspect and optionally verify a JWT.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DecodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid request',
                'details': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        token = data['token']
        secret = data.get('secret') or None
        verify_signature = data.get('verify_signature', True)
        audience = data.get('audience') or None
        issuer = data.get('issuer') or None
        leeway = data.get('leeway_seconds', 0)
        allow_insecure_none = data.get('allow_insecure_none', False)

        warnings = []
        header = None
        payload = None
        used_algorithm = None
        signature_valid = False

        try:
            header = jwt.get_unverified_header(token)
        except Exception as exc:  # broad to surface malformed tokens
            return Response({
                'success': False,
                'error': f'Unable to parse header: {str(exc)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        requested_alg = data.get('algorithm', 'auto')
        used_algorithm = header.get('alg') if requested_alg == 'auto' else requested_alg
        if not used_algorithm:
            used_algorithm = 'HS256'
            warnings.append('No algorithm found in header; defaulting to HS256.')

        if used_algorithm == 'none' and not allow_insecure_none:
            return Response({
                'success': False,
                'error': 'Algorithm "none" is blocked. Enable allow_insecure_none to proceed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if verify_signature:
            if used_algorithm in SYMMETRIC_ALGORITHMS and not secret:
                return Response({
                    'success': False,
                    'error': 'A shared secret is required to verify this token.'
                }, status=status.HTTP_400_BAD_REQUEST)
            if used_algorithm in ASYMMETRIC_ALGORITHMS and not secret:
                return Response({
                    'success': False,
                    'error': 'A public/private key (PEM) is required to verify this token.'
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if verify_signature:
                options = {
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_aud': bool(audience),
                    'verify_iss': bool(issuer),
                }

                payload = jwt.decode(
                    token,
                    key=secret,
                    algorithms=[used_algorithm],
                    audience=audience,
                    issuer=issuer,
                    options=options,
                    leeway=leeway,
                )
                signature_valid = True
            else:
                options = {
                    'verify_signature': False,
                    'verify_exp': False,
                    'verify_aud': False,
                    'verify_iss': False,
                }
                payload = jwt.decode(token, options=options)
                warnings.append('Signature verification disabled; trust this output only after verifying the signature.')

        except ExpiredSignatureError:
            return Response({
                'success': False,
                'error': 'Token has expired.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except InvalidSignatureError:
            return Response({
                'success': False,
                'error': 'Signature verification failed.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except InvalidAlgorithmError:
            return Response({
                'success': False,
                'error': 'The token algorithm is not allowed or mismatched.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except InvalidTokenError as exc:
            return Response({
                'success': False,
                'error': f'Invalid token: {str(exc)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # unexpected issues
            logger.exception('Unexpected error while decoding JWT')
            return Response({
                'success': False,
                'error': f'Failed to process token: {str(exc)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'header': header,
            'payload': payload,
            'algorithm': used_algorithm,
            'signature_valid': signature_valid,
            'warnings': warnings,
        })


class JWTEncodeAPIView(APIView):
    """
    Generate a JWT from a provided header and payload.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EncodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid request',
                'details': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        header = data['header'] or {}
        payload = data['payload'] or {}
        secret = data.get('secret') or ''
        algorithm = data['algorithm']
        expires_in_seconds = data.get('expires_in_seconds', 0)
        include_iat = data.get('include_iat', True)

        warnings = []

        if 'typ' not in header:
            header['typ'] = 'JWT'
        header.setdefault('alg', algorithm)

        now = datetime.now(timezone.utc)
        now_ts = int(now.timestamp())
        if include_iat and 'iat' not in payload:
            payload['iat'] = now_ts

        if expires_in_seconds and expires_in_seconds > 0:
            payload['exp'] = now_ts + expires_in_seconds
        elif 'exp' in payload:
            # If user supplied exp manually, accept as-is
            pass
        else:
            warnings.append('No expiration set; long-lived tokens can be risky.')

        if algorithm in SYMMETRIC_ALGORITHMS and len(secret) < 8:
            warnings.append('The shared secret is short; consider a longer passphrase for HS* algorithms.')

        try:
            token = jwt.encode(payload, key=secret, algorithm=algorithm, headers=header)
        except Exception as exc:
            logger.exception('Failed to sign token')
            return Response({
                'success': False,
                'error': f'Failed to sign token: {str(exc)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # PyJWT may return bytes in older versions
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        return Response({
            'success': True,
            'token': token,
            'header': header,
            'payload': payload,
            'algorithm': algorithm,
            'warnings': warnings,
        }, status=status.HTTP_200_OK)


class KeyGeneratorAPIView(APIView):
    """Generate cryptographic keys for JWT signing."""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Get and normalize key_type (handle both uppercase and lowercase)
            key_type = request.data.get('key_type', 'hs256')
            if not key_type:
                return Response({
                    'success': False,
                    'error': 'key_type is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            key_type_lower = key_type.lower()
            
            if key_type_lower == 'hs256':
                secret = KeyGeneratorService.generate_hs_secret()
                return Response({
                    'success': True,
                    'key_type': 'HS256',
                    'secret': secret,
                    'recommendation': 'Copy this secret and keep it safe. Use it for HS256/384/512 algorithms.'
                })
            elif key_type_lower == 'rsa':
                keypair = KeyGeneratorService.generate_rsa_keypair()
                return Response({
                    'success': True,
                    'key_type': 'RSA',
                    'private_key': keypair['private_key'],
                    'public_key': keypair['public_key'],
                    'key_size': keypair['key_size'],
                    'recommendation': 'Use private key for signing (server), public key for verification (clients).'
                })
            elif key_type_lower == 'ec':
                curve = request.data.get('ec_curve', 'P-256')
                keypair = KeyGeneratorService.generate_ec_keypair(curve)
                return Response({
                    'success': True,
                    'key_type': 'EC',
                    'curve': keypair['curve'],
                    'private_key': keypair['private_key'],
                    'public_key': keypair['public_key'],
                    'recommendation': 'Use private key for signing (server), public key for verification (clients).'
                })
            else:
                return Response({
                    'success': False,
                    'error': f'Unsupported key type: {key_type}. Supported types: HS256, RSA, EC'
                }, status=status.HTTP_400_BAD_REQUEST)
        except ImportError:
            return Response({
                'success': False,
                'error': 'Cryptography library not installed. Install with: pip install cryptography'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.exception('Error generating key')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CodeGeneratorAPIView(APIView):
    """Generate code snippets for JWT handling."""
    permission_classes = [AllowAny]

    def post(self, request):
        language = request.data.get('language', 'nodejs').lower()
        token = request.data.get('token', 'your.jwt.token')
        secret = request.data.get('secret', 'your-secret-key')
        algorithm = request.data.get('algorithm', 'HS256')
        
        try:
            if language == 'nodejs':
                code = CodeGeneratorService.generate_nodejs_code(token, secret, algorithm)
            elif language == 'python':
                code = CodeGeneratorService.generate_python_code(token, secret, algorithm)
            elif language == 'java':
                code = CodeGeneratorService.generate_java_code(token, secret, algorithm)
            elif language == 'go':
                code = CodeGeneratorService.generate_go_code(token, secret, algorithm)
            elif language == 'php':
                code = CodeGeneratorService.generate_php_code(token, secret, algorithm)
            else:
                return Response({
                    'success': False,
                    'error': 'Unsupported language'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'language': language,
                'code': code
            })
        except Exception as e:
            logger.exception('Error generating code')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SecurityScannerAPIView(APIView):
    """Scan JWT for security vulnerabilities."""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token', '').strip()
        secret = request.data.get('secret', '')
        verify_signature = request.data.get('verify_signature', False)
        
        if not token:
            return Response({
                'success': False,
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Decode header
            header = jwt.get_unverified_header(token)
            
            # Decode payload
            payload = jwt.decode(token, options={'verify_signature': False})
            
            # Verify signature if requested
            signature_valid = False
            if verify_signature and secret:
                try:
                    jwt.decode(token, secret, algorithms=[header.get('alg', 'HS256')])
                    signature_valid = True
                except:
                    signature_valid = False
            
            # Run security scan
            scan_result = SecurityScannerService.scan_token(header, payload, signature_valid)
            
            return Response({
                'success': True,
                'security_score': scan_result['security_score'],
                'issues': scan_result['issues'],
                'recommendation': scan_result['recommendation'],
                'header': header,
                'payload': payload
            })
        except Exception as e:
            logger.exception('Error scanning token')
            return Response({
                'success': False,
                'error': f'Failed to scan token: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class JWKSIntegrationAPIView(APIView):
    """Fetch and cache keys from JWKS endpoints."""
    permission_classes = [AllowAny]

    def post(self, request):
        jwks_url = request.data.get('jwks_url', '').strip()
        
        if not jwks_url:
            return Response({
                'success': False,
                'error': 'JWKS URL is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not jwks_url.startswith('http'):
            return Response({
                'success': False,
                'error': 'Invalid JWKS URL'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            import requests
            response = requests.get(jwks_url, timeout=5)
            response.raise_for_status()
            jwks_data = response.json()
            
            keys = jwks_data.get('keys', [])
            
            return Response({
                'success': True,
                'keys': keys,
                'key_count': len(keys),
                'message': f'Successfully fetched {len(keys)} keys from JWKS endpoint'
            })
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'error': 'Request timeout. JWKS endpoint took too long to respond.'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            return Response({
                'success': False,
                'error': f'Failed to fetch JWKS: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception('Error fetching JWKS')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
