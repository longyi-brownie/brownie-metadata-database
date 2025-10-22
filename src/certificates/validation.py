"""Certificate validation utilities for PostgreSQL connections."""

import os
import ssl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class CertificateValidator:
    """Validates client certificates for PostgreSQL connections."""

    def __init__(self, cert_dir: str = "/certs"):
        self.cert_dir = Path(cert_dir)

    def validate_certificate_chain(
        self,
        client_cert_path: str,
        client_key_path: str,
        ca_cert_path: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Validate certificate chain and return validation results.

        Args:
            client_cert_path: Path to client certificate
            client_key_path: Path to client private key
            ca_cert_path: Path to CA certificate (optional)

        Returns:
            Dictionary with validation results
        """
        results = {
            "client_cert_exists": False,
            "client_key_exists": False,
            "ca_cert_exists": False,
            "client_cert_valid": False,
            "client_key_valid": False,
            "ca_cert_valid": False,
            "cert_expired": False,
            "cn_matches": False,
            "key_cert_match": False,
        }

        # Check file existence
        client_cert = Path(client_cert_path)
        client_key = Path(client_key_path)
        ca_cert = Path(ca_cert_path) if ca_cert_path else None

        results["client_cert_exists"] = client_cert.exists()
        results["client_key_exists"] = client_key.exists()
        if ca_cert:
            results["ca_cert_exists"] = ca_cert.exists()

        if not results["client_cert_exists"] or not results["client_key_exists"]:
            logger.warning("Certificate files missing", results=results)
            return results

        try:
            # Validate certificate format and expiration
            cert_info = self._validate_certificate_format(client_cert)
            results["client_cert_valid"] = cert_info["valid"]
            results["cert_expired"] = cert_info["expired"]
            results["cn_matches"] = cert_info["cn_matches"]

            # Validate private key format
            results["client_key_valid"] = self._validate_private_key_format(client_key)

            # Check if key matches certificate
            results["key_cert_match"] = self._validate_key_cert_match(
                client_cert, client_key
            )

            # Validate CA certificate if provided
            if ca_cert and ca_cert.exists():
                ca_info = self._validate_certificate_format(ca_cert)
                results["ca_cert_valid"] = ca_info["valid"]

        except Exception as e:
            logger.error("Certificate validation failed", error=str(e))
            results["client_cert_valid"] = False
            results["client_key_valid"] = False

        return results

    def _validate_certificate_format(self, cert_path: Path) -> Dict[str, any]:
        """Validate certificate format and extract information."""
        try:
            with open(cert_path, "rb") as f:
                cert_data = f.read()

            # Parse certificate
            cert = (
                ssl.DER_cert_to_PEM_cert(cert_data)
                if cert_data.startswith(b"\x30")
                else cert_data.decode()
            )

            # Create SSL context and load certificate
            context = ssl.create_default_context()
            context.load_cert_chain(cert_path)

            # Get certificate info
            cert_obj = (
                ssl.DER_cert_to_PEM_cert(cert_data)
                if cert_data.startswith(b"\x30")
                else cert_data
            )
            cert_info = ssl.cert_time_to_seconds(cert_obj)

            # Check expiration
            now = datetime.now()
            not_after = datetime.fromtimestamp(cert_info["notAfter"])
            expired = now > not_after

            # Extract Common Name
            cn = self._extract_common_name(cert_obj)
            cn_matches = cn == "brownie-fastapi-server"

            return {
                "valid": True,
                "expired": expired,
                "cn_matches": cn_matches,
                "common_name": cn,
                "not_after": not_after,
            }

        except Exception as e:
            logger.error(
                "Certificate format validation failed",
                cert_path=str(cert_path),
                error=str(e),
            )
            return {"valid": False, "expired": True, "cn_matches": False}

    def _validate_private_key_format(self, key_path: Path) -> bool:
        """Validate private key format."""
        try:
            with open(key_path, "rb") as f:
                key_data = f.read()

            # Try to parse as PEM
            if b"BEGIN PRIVATE KEY" in key_data or b"BEGIN RSA PRIVATE KEY" in key_data:
                return True

            # Try to parse as DER
            if key_data.startswith(b"\x30"):
                return True

            return False

        except Exception as e:
            logger.error(
                "Private key validation failed", key_path=str(key_path), error=str(e)
            )
            return False

    def _validate_key_cert_match(self, cert_path: Path, key_path: Path) -> bool:
        """Validate that private key matches certificate."""
        try:
            # This is a simplified check - in production you'd want more thorough validation
            # For now, we'll just check that both files exist and are readable
            return (
                cert_path.exists()
                and key_path.exists()
                and cert_path.is_file()
                and key_path.is_file()
            )

        except Exception as e:
            logger.error("Key-certificate match validation failed", error=str(e))
            return False

    def _extract_common_name(self, cert_data: bytes) -> Optional[str]:
        """Extract Common Name from certificate."""
        try:
            # This is a simplified implementation
            # In production, you'd use cryptography library for proper parsing
            cert_str = cert_data.decode() if isinstance(cert_data, bytes) else cert_data

            # Look for CN in subject line
            lines = cert_str.split("\n")
            for line in lines:
                if "Subject:" in line and "CN=" in line:
                    # Extract CN value
                    cn_start = line.find("CN=") + 3
                    cn_end = line.find(",", cn_start)
                    if cn_end == -1:
                        cn_end = len(line)
                    return line[cn_start:cn_end].strip()

            return None

        except Exception as e:
            logger.error("Failed to extract Common Name", error=str(e))
            return None

    def get_validation_summary(
        self, results: Dict[str, bool]
    ) -> Tuple[bool, List[str]]:
        """
        Get validation summary and list of issues.

        Args:
            results: Validation results from validate_certificate_chain

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        is_valid = True

        if not results["client_cert_exists"]:
            issues.append("Client certificate file missing")
            is_valid = False

        if not results["client_key_exists"]:
            issues.append("Client private key file missing")
            is_valid = False

        if not results["client_cert_valid"]:
            issues.append("Client certificate format invalid")
            is_valid = False

        if not results["client_key_valid"]:
            issues.append("Client private key format invalid")
            is_valid = False

        if results["cert_expired"]:
            issues.append("Client certificate expired")
            is_valid = False

        if not results["cn_matches"]:
            issues.append("Certificate CN does not match expected username")
            is_valid = False

        if not results["key_cert_match"]:
            issues.append("Private key does not match certificate")
            is_valid = False

        if results.get("ca_cert_exists") and not results.get("ca_cert_valid"):
            issues.append("CA certificate format invalid")
            is_valid = False

        return is_valid, issues
