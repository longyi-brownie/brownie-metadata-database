"""
Server-side certificate management for PostgreSQL.

Manages CA and server certificates for PostgreSQL SSL/TLS configuration.
Client certificates are handled by the FastAPI application.
"""

import os
import base64
from typing import Optional, Dict, Any
from pathlib import Path


class ServerCertificateManager:
    """Manages PostgreSQL server certificates from Vault or local files."""
    
    def __init__(self):
        self.vault_enabled = os.getenv("VAULT_ENABLED", "false").lower() == "true"
        self.vault_url = os.getenv("VAULT_URL")
        self.vault_token = os.getenv("VAULT_TOKEN")
        self.vault_path = os.getenv("VAULT_CERT_PATH", "secret/brownie-metadata/certs")
        
        # Local certificate paths (for development)
        self.local_cert_dir = os.getenv("LOCAL_CERT_DIR", "dev-certs")
        
    def get_certificate(self, cert_type: str) -> Optional[str]:
        """
        Get certificate content from Vault or local file.
        
        Args:
            cert_type: Type of certificate (server_cert, server_key, ca_cert)
            
        Returns:
            Certificate content as string, or None if not found
        """
        if self.vault_enabled:
            return self._get_from_vault(cert_type)
        else:
            return self._get_from_local_file(cert_type)
    
    def _get_from_vault(self, cert_type: str) -> Optional[str]:
        """Get certificate from HashiCorp Vault."""
        try:
            import hvac
            
            client = hvac.Client(url=self.vault_url, token=self.vault_token)
            
            # Read secret from Vault
            secret_response = client.secrets.kv.v2.read_secret_version(
                path=self.vault_path
            )
            
            secret_data = secret_response['data']['data']
            cert_content = secret_data.get(cert_type)
            
            if cert_content:
                # Decode if base64 encoded
                try:
                    return base64.b64decode(cert_content).decode('utf-8')
                except:
                    return cert_content
            
            return None
            
        except ImportError:
            raise RuntimeError("hvac package required for Vault integration. Install with: pip install hvac")
        except Exception as e:
            raise RuntimeError(f"Failed to get certificate from Vault: {e}")
    
    def _get_from_local_file(self, cert_type: str) -> Optional[str]:
        """Get certificate from local file."""
        cert_file_map = {
            "server_cert": "server.crt",
            "server_key": "server.key", 
            "ca_cert": "ca.crt"
        }
        
        filename = cert_file_map.get(cert_type)
        if not filename:
            return None
            
        cert_path = Path(self.local_cert_dir) / filename
        
        if cert_path.exists():
            return cert_path.read_text()
        
        return None
    
    def get_postgres_ssl_config(self) -> Dict[str, Any]:
        """
        Get SSL configuration for PostgreSQL server.
        
        Returns:
            Dictionary with PostgreSQL SSL configuration parameters
        """
        ssl_config = {
            "ssl": "on",
            "ssl_cert_file": None,
            "ssl_key_file": None,
            "ssl_ca_file": None
        }
        
        if self.vault_enabled or self._has_local_certs():
            # Get server certificates
            server_cert = self.get_certificate("server_cert")
            server_key = self.get_certificate("server_key")
            ca_cert = self.get_certificate("ca_cert")
            
            if server_cert and server_key:
                # Write certificates to temporary files for PostgreSQL
                cert_dir = Path("/tmp/brownie-server-certs")
                cert_dir.mkdir(exist_ok=True)
                
                (cert_dir / "server.crt").write_text(server_cert)
                (cert_dir / "server.key").write_text(server_key)
                
                ssl_config.update({
                    "ssl_cert_file": str(cert_dir / "server.crt"),
                    "ssl_key_file": str(cert_dir / "server.key")
                })
                
                if ca_cert:
                    (cert_dir / "ca.crt").write_text(ca_cert)
                    ssl_config["ssl_ca_file"] = str(cert_dir / "ca.crt")
        
        return ssl_config
    
    def _has_local_certs(self) -> bool:
        """Check if local server certificates exist."""
        cert_dir = Path(self.local_cert_dir)
        return (cert_dir / "server.crt").exists() and (cert_dir / "server.key").exists()
    
    def validate_certificates(self) -> Dict[str, bool]:
        """
        Validate that required server certificates are available.
        
        Returns:
            Dictionary with validation results for each certificate type
        """
        results = {}
        
        for cert_type in ["server_cert", "server_key", "ca_cert"]:
            cert_content = self.get_certificate(cert_type)
            results[cert_type] = cert_content is not None
        
        return results


# Global server certificate manager instance
server_cert_manager = ServerCertificateManager()
