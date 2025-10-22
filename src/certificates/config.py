"""Centralized certificate configuration for PostgreSQL connections."""

import os
from pathlib import Path
from typing import Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class CertificateConfig(BaseSettings):
    """Centralized certificate configuration settings."""

    # Certificate directory
    cert_dir: str = Field(default="/certs", description="Certificate directory path")

    # Client certificate paths
    client_cert_file: str = Field(
        default="client.crt", description="Client certificate filename"
    )
    client_key_file: str = Field(
        default="client.key", description="Client private key filename"
    )
    ca_cert_file: str = Field(default="ca.crt", description="CA certificate filename")

    # Server certificate paths
    server_cert_file: str = Field(
        default="server.crt", description="Server certificate filename"
    )
    server_key_file: str = Field(
        default="server.key", description="Server private key filename"
    )

    # Certificate validation settings
    validate_certificates: bool = Field(
        default=True, description="Enable certificate validation"
    )
    strict_validation: bool = Field(
        default=False, description="Fail on certificate validation errors"
    )

    # Expected certificate Common Name
    expected_cn: str = Field(
        default="brownie-fastapi-server", description="Expected certificate CN"
    )

    class Config:
        env_prefix = "CERT_"

    @property
    def client_cert_path(self) -> str:
        """Get full path to client certificate."""
        return str(Path(self.cert_dir) / self.client_cert_file)

    @property
    def client_key_path(self) -> str:
        """Get full path to client private key."""
        return str(Path(self.cert_dir) / self.client_key_file)

    @property
    def ca_cert_path(self) -> str:
        """Get full path to CA certificate."""
        return str(Path(self.cert_dir) / self.ca_cert_file)

    @property
    def server_cert_path(self) -> str:
        """Get full path to server certificate."""
        return str(Path(self.cert_dir) / self.server_cert_file)

    @property
    def server_key_path(self) -> str:
        """Get full path to server private key."""
        return str(Path(self.cert_dir) / self.server_key_file)

    def get_client_cert_paths(self) -> Dict[str, str]:
        """Get dictionary of client certificate paths."""
        return {
            "client_cert": self.client_cert_path,
            "client_key": self.client_key_path,
            "ca_cert": self.ca_cert_path,
        }

    def get_server_cert_paths(self) -> Dict[str, str]:
        """Get dictionary of server certificate paths."""
        return {
            "server_cert": self.server_cert_path,
            "server_key": self.server_key_path,
            "ca_cert": self.ca_cert_path,
        }

    def validate_certificate_files(self) -> Dict[str, bool]:
        """Check if certificate files exist."""
        paths = self.get_client_cert_paths()
        return {name: Path(path).exists() for name, path in paths.items()}


# Global certificate configuration instance
cert_config = CertificateConfig()
