from rest_framework.test import APITestCase
from rest_framework import status


class JWTDebuggerTests(APITestCase):
    def test_sign_and_inspect_hs256_token(self):
        sign_payload = {
            'header': {'alg': 'HS256', 'typ': 'JWT'},
            'payload': {'sub': 'user-1', 'role': 'tester'},
            'secret': 'super-secret',
            'algorithm': 'HS256',
            'expires_in_seconds': 300,
            'include_iat': True,
        }
        sign_response = self.client.post('/api/jwt/sign/', sign_payload, format='json')
        self.assertEqual(sign_response.status_code, status.HTTP_200_OK)
        self.assertTrue(sign_response.data.get('success'))
        token = sign_response.data.get('token')
        self.assertTrue(token)

        inspect_payload = {
            'token': token,
            'secret': 'super-secret',
            'algorithm': 'HS256',
            'verify_signature': True,
        }
        inspect_response = self.client.post('/api/jwt/inspect/', inspect_payload, format='json')
        self.assertEqual(inspect_response.status_code, status.HTTP_200_OK)
        self.assertTrue(inspect_response.data.get('success'))
        self.assertTrue(inspect_response.data.get('signature_valid'))
        self.assertEqual(inspect_response.data.get('payload', {}).get('sub'), 'user-1')

    def test_inspect_invalid_token(self):
        inspect_payload = {
            'token': 'bad.token.value',
            'secret': 'secret',
            'algorithm': 'HS256',
            'verify_signature': True,
        }
        response = self.client.post('/api/jwt/inspect/', inspect_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success', True))
