"""
JWT Debugger - Services for key generation, code generation, and security scanning
"""
import json
import secrets
from typing import Dict, List, Any

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, ec
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class KeyGeneratorService:
    """Generate cryptographic keys for JWT signing."""
    
    @staticmethod
    def generate_hs_secret(length: int = 32) -> str:
        """Generate a random secret for HS algorithms."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_rsa_keypair(key_size: int = 2048) -> Dict[str, str]:
        """Generate RSA key pair (PEM format)."""
        if not HAS_CRYPTO:
            raise ImportError("cryptography library required")
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return {
            'private_key': private_pem,
            'public_key': public_pem,
            'key_size': key_size
        }
    
    @staticmethod
    def generate_ec_keypair(curve: str = 'P-256') -> Dict[str, str]:
        """Generate EC key pair (PEM format)."""
        if not HAS_CRYPTO:
            raise ImportError("cryptography library required")
        
        curve_map = {
            'P-256': ec.SECP256R1(),
            'P-384': ec.SECP384R1(),
            'P-521': ec.SECP521R1(),
        }
        
        if curve not in curve_map:
            curve = 'P-256'
        
        private_key = ec.generate_private_key(curve_map[curve], default_backend())
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return {
            'private_key': private_pem,
            'public_key': public_pem,
            'curve': curve
        }


class CodeGeneratorService:
    """Generate code snippets for JWT handling in various languages."""
    
    @staticmethod
    def generate_nodejs_code(token: str, secret: str, algorithm: str) -> str:
        """Generate Node.js JWT code."""
        code = f"""// Node.js - Using jsonwebtoken
const jwt = require('jsonwebtoken');

const token = '{token}';
const secret = `{secret}`;

// Verify and decode
try {{
  const decoded = jwt.verify(token, secret, {{ algorithms: ['{algorithm}'] }});
  console.log('Token valid:', decoded);
}} catch (err) {{
  console.error('Invalid token:', err.message);
}}

// Create new token
const payload = {{ userId: 123, role: 'admin' }};
const newToken = jwt.sign(payload, secret, {{ 
  algorithm: '{algorithm}',
  expiresIn: '1h' 
}});
console.log('New token:', newToken);
"""
        return code
    
    @staticmethod
    def generate_python_code(token: str, secret: str, algorithm: str) -> str:
        """Generate Python JWT code."""
        code = f"""# Python - Using PyJWT
import jwt
from datetime import datetime, timedelta

token = '{token}'
secret = '{secret}'

# Verify and decode
try:
    decoded = jwt.decode(token, secret, algorithms=['{algorithm}'])
    print("Token valid:", decoded)
except jwt.InvalidTokenError as e:
    print("Invalid token:", str(e))

# Create new token
payload = {{
    "userId": 123,
    "role": "admin",
    "exp": datetime.utcnow() + timedelta(hours=1)
}}
new_token = jwt.encode(payload, secret, algorithm='{algorithm}')
print("New token:", new_token)
"""
        return code
    
    @staticmethod
    def generate_java_code(token: str, secret: str, algorithm: str) -> str:
        """Generate Java JWT code."""
        code = f"""// Java - Using JJWT
import io.jsonwebtoken.*;

String token = "{token}";
String secret = "{secret}";

// Verify and decode
try {{
    Jws<Claims> jws = Jwts.parserBuilder()
        .setSigningKey(secret.getBytes())
        .build()
        .parseClaimsJws(token);
    System.out.println("Token valid: " + jws.getBody());
}} catch (JwtException e) {{
    System.err.println("Invalid token: " + e.getMessage());
}}

// Create new token
String newToken = Jwts.builder()
    .setSubject("user-123")
    .claim("role", "admin")
    .setIssuedAt(new Date())
    .setExpiration(new Date(System.currentTimeMillis() + 3600000))
    .signWith(SignatureAlgorithm.{algorithm}, secret)
    .compact();
System.out.println("New token: " + newToken);
"""
        return code
    
    @staticmethod
    def generate_go_code(token: str, secret: str, algorithm: str) -> str:
        """Generate Go JWT code."""
        code = f"""// Go - Using golang-jwt
package main

import (
    "fmt"
    "github.com/golang-jwt/jwt/v5"
    "time"
)

func main() {{
    token := "{token}"
    secret := "{secret}"
    
    // Verify and decode
    parsed, err := jwt.Parse(token, func(token *jwt.Token) (interface{{}}, error) {{
        return []byte(secret), nil
    }})
    
    if err != nil {{
        fmt.Println("Invalid token:", err)
        return
    }}
    
    if claims, ok := parsed.Claims.(jwt.MapClaims); ok {{
        fmt.Println("Token valid:", claims)
    }}
    
    // Create new token
    claims := jwt.MapClaims{{
        "userId": 123,
        "role": "admin",
        "exp": time.Now().Add(time.Hour).Unix(),
    }}
    
    newToken := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    newTokenString, err := newToken.SignedString([]byte(secret))
    if err != nil {{
        fmt.Println("Error creating token:", err)
    }}
    fmt.Println("New token:", newTokenString)
}}
"""
        return code
    
    @staticmethod
    def generate_php_code(token: str, secret: str, algorithm: str) -> str:
        """Generate PHP JWT code."""
        code = f"""<?php
// PHP - Using firebase/php-jwt
use Firebase\\\\JWT\\\\JWT;
use Firebase\\\\JWT\\\\Key;

$token = "{token}";
$secret = "{secret}";

// Verify and decode
try {{
    $decoded = JWT::decode($token, new Key($secret, '{algorithm}'));
    echo "Token valid: ";
    print_r($decoded);
}} catch (Exception $e) {{
    echo "Invalid token: " . $e->getMessage();
}}

// Create new token
$payload = [
    'userId' => 123,
    'role' => 'admin',
    'iat' => time(),
    'exp' => time() + 3600
];

$newToken = JWT::encode($payload, $secret, '{algorithm}');
echo "New token: " . $newToken;
?>
"""
        return code


class SecurityScannerService:
    """Scan JWTs for security issues."""
    
    @staticmethod
    def scan_token(header: Dict, payload: Dict, signature_valid: bool) -> Dict[str, Any]:
        """Scan JWT for security vulnerabilities."""
        issues = []
        score = 100  # Start with perfect score
        
        # Check algorithm
        alg = header.get('alg', 'unknown')
        if alg == 'none':
            issues.append({
                'severity': 'critical',
                'message': 'Algorithm "none" allows unsigned tokens. Never use in production.',
                'code': 'ALG_NONE'
            })
            score -= 40
        elif alg.startswith('HS'):
            issues.append({
                'severity': 'medium',
                'message': 'Symmetric algorithm detected. Ensure secret is strong and never shared publicly.',
                'code': 'ALG_SYMMETRIC'
            })
            score -= 5
        
        # Check expiration
        if 'exp' not in payload:
            issues.append({
                'severity': 'high',
                'message': 'Token has no expiration (exp). Tokens should expire to limit damage if compromised.',
                'code': 'NO_EXPIRATION'
            })
            score -= 20
        
        # Check issued at
        if 'iat' not in payload:
            issues.append({
                'severity': 'low',
                'message': 'Token missing "iat" (issued at). Useful for audit trails and token age validation.',
                'code': 'NO_IAT'
            })
            score -= 5
        
        # Check not before
        if 'nbf' not in payload:
            issues.append({
                'severity': 'low',
                'message': 'Token missing "nbf" (not before). Consider adding for time-based access control.',
                'code': 'NO_NBF'
            })
            score -= 3
        
        # Check signature validity
        if not signature_valid:
            issues.append({
                'severity': 'critical',
                'message': 'Signature verification failed. Token may be tampered or using wrong key.',
                'code': 'INVALID_SIGNATURE'
            })
            score -= 30
        
        # Check for sensitive data in payload
        sensitive_keys = ['password', 'pin', 'credit_card', 'ssn', 'api_key', 'secret']
        found_sensitive = [key for key in payload.keys() if any(s in key.lower() for s in sensitive_keys)]
        if found_sensitive:
            issues.append({
                'severity': 'critical',
                'message': f'Sensitive data detected in payload: {", ".join(found_sensitive)}. JWTs are base64 encoded, not encrypted.',
                'code': 'SENSITIVE_DATA'
            })
            score -= 25
        
        return {
            'security_score': max(0, score),
            'issues': issues,
            'recommendation': get_security_recommendation(score)
        }


def get_security_recommendation(score: int) -> str:
    """Get recommendation based on security score."""
    if score >= 90:
        return "✅ Good - Token appears secure for most use cases."
    elif score >= 70:
        return "⚠️ Fair - Consider adding expiration and ensuring secure key management."
    elif score >= 50:
        return "❌ Poor - Several security issues detected. Review before production use."
    else:
        return "🚨 Critical - Serious security vulnerabilities detected. Do not use in production."
