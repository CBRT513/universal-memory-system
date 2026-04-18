#!/usr/bin/env python3
"""
Firebase Auth Integration with Domain Whitelisting
"""

import os
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Authorized domains for Firebase authentication
AUTHORIZED_DOMAINS = {
    "sso.test",
    "cbrt-ui.test",
    "localhost",
    "127.0.0.1",
    "barge2rail.com",
    "cbrt.com"
}

class AuthIntegration:
    """Handles Firebase authentication with domain validation"""
    
    def __init__(self, project_id: str = "barge2rail-auth-e4c16"):
        self.project_id = project_id
        self.authorized_domains = AUTHORIZED_DOMAINS.copy()
        
        # Add any environment-specific domains
        extra_domains = os.environ.get("FIREBASE_EXTRA_DOMAINS", "")
        if extra_domains:
            for domain in extra_domains.split(","):
                self.authorized_domains.add(domain.strip())
    
    def check_domain_whitelist(self, request_origin: str) -> Dict[str, Any]:
        """
        Check if the request origin is in the whitelist
        
        Args:
            request_origin: The origin URL or domain making the request
            
        Returns:
            Dict with 'allowed' boolean and optional 'error' message
        """
        try:
            # Parse the origin
            if not request_origin:
                return {
                    "allowed": False,
                    "error": "No origin domain provided",
                    "code": "auth/missing-origin"
                }
            
            # Handle full URLs or just domains
            if request_origin.startswith("http"):
                parsed = urlparse(request_origin)
                domain = parsed.hostname
                
                # Check if hostname is None (invalid URL)
                if domain is None:
                    return {
                        "allowed": False,
                        "error": "Invalid domain format",
                        "code": "auth/invalid-domain"
                    }
                
                port = parsed.port
                
                # Special handling for localhost with ports
                if domain == "localhost" and port:
                    # Allow any localhost port
                    domain = "localhost"
            else:
                # Assume it's just a domain
                domain = request_origin.lower()
            
            # Check if domain is authorized
            if domain in self.authorized_domains:
                logger.info(f"Domain authorized: {domain}")
                return {
                    "allowed": True,
                    "domain": domain,
                    "project": self.project_id
                }
            else:
                logger.warning(f"Unauthorized domain attempt: {domain}")
                return {
                    "allowed": False,
                    "error": f"Domain '{domain}' is not authorized for authentication",
                    "code": "auth/unauthorized-domain",
                    "suggestion": "Please contact administrator to whitelist this domain"
                }
                
        except Exception as e:
            logger.error(f"Error checking domain whitelist: {e}")
            return {
                "allowed": False,
                "error": "Invalid domain format",
                "code": "auth/invalid-domain"
            }
    
    def validate_auth_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an authentication request including domain check
        
        Args:
            request: Dict containing auth request details
            
        Returns:
            Validation result with details
        """
        # Extract origin from request
        origin = request.get("origin") or request.get("referer") or request.get("domain")
        
        # Check domain whitelist
        domain_check = self.check_domain_whitelist(origin)
        if not domain_check["allowed"]:
            return {
                "valid": False,
                "error": domain_check["error"],
                "code": domain_check["code"],
                "suggestion": domain_check.get("suggestion")
            }
        
        # Additional validation can go here
        auth_method = request.get("auth_method", "firebase")
        if auth_method not in ["firebase", "sso", "local"]:
            return {
                "valid": False,
                "error": "Invalid authentication method",
                "code": "auth/invalid-method"
            }
        
        return {
            "valid": True,
            "domain": domain_check["domain"],
            "auth_method": auth_method,
            "project": self.project_id
        }
    
    def handle_auth_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Firebase auth errors with graceful responses
        
        Args:
            error: The Firebase error
            context: Additional context about the request
            
        Returns:
            User-friendly error response
        """
        error_str = str(error).lower()
        
        # Map Firebase errors to user-friendly messages
        if "unauthorized-domain" in error_str or "unauthorized domain" in error_str:
            domain = context.get("domain", "unknown")
            return {
                "error": "Authentication not allowed from this domain",
                "code": "auth/unauthorized-domain",
                "domain": domain,
                "message": f"The domain '{domain}' is not authorized for authentication. Please use an authorized domain or contact support.",
                "authorized_domains": list(self.authorized_domains)
            }
        elif "invalid-email" in error_str:
            return {
                "error": "Invalid email address",
                "code": "auth/invalid-email",
                "message": "Please provide a valid email address"
            }
        elif "user-not-found" in error_str:
            return {
                "error": "User not found",
                "code": "auth/user-not-found",
                "message": "No account exists with this email address"
            }
        elif "wrong-password" in error_str:
            return {
                "error": "Incorrect password",
                "code": "auth/wrong-password",
                "message": "The password is incorrect"
            }
        else:
            # Generic error handling
            logger.error(f"Unhandled auth error: {error}")
            return {
                "error": "Authentication failed",
                "code": "auth/unknown",
                "message": "An error occurred during authentication. Please try again."
            }
    
    def get_authorized_domains(self) -> List[str]:
        """Get list of all authorized domains"""
        return sorted(list(self.authorized_domains))
    
    def add_domain(self, domain: str) -> bool:
        """
        Add a domain to the authorized list (runtime only)
        
        Args:
            domain: Domain to add
            
        Returns:
            True if added, False if already exists
        """
        if domain not in self.authorized_domains:
            self.authorized_domains.add(domain)
            logger.info(f"Domain added to whitelist: {domain}")
            return True
        return False
    
    def remove_domain(self, domain: str) -> bool:
        """
        Remove a domain from the authorized list (runtime only)
        
        Args:
            domain: Domain to remove
            
        Returns:
            True if removed, False if not found
        """
        if domain in self.authorized_domains:
            self.authorized_domains.remove(domain)
            logger.info(f"Domain removed from whitelist: {domain}")
            return True
        return False


# Singleton instance
_auth_integration = None

def get_auth_integration(project_id: Optional[str] = None) -> AuthIntegration:
    """Get or create auth integration instance"""
    global _auth_integration
    if _auth_integration is None:
        _auth_integration = AuthIntegration(project_id or "barge2rail-auth-e4c16")
    return _auth_integration