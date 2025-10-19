#!/usr/bin/env python3
"""
Enterprise Metrics Sidecar for Brownie Metadata Database

This sidecar collects and exports custom metrics for enterprise monitoring:
- Database performance metrics
- Connection pool statistics
- Query performance
- Cache hit rates
- Business metrics (incidents, teams, users)
"""

import logging
import os
import sys
import time

import psycopg
import redis
from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import structlog

from src.logging_config.config import LoggingConfig, configure_logging

# Configure centralized logging
config = LoggingConfig()
configure_logging(config)
logger = structlog.get_logger()

# Prometheus metrics
db_connections = Gauge(
    "brownie_db_connections_total", "Total database connections", ["state"]
)
db_query_duration = Histogram(
    "brownie_db_query_duration_seconds", "Database query duration", ["query_type"]
)
db_query_errors = Counter(
    "brownie_db_query_errors_total", "Database query errors", ["error_type"]
)
db_size_bytes = Gauge("brownie_db_size_bytes", "Database size in bytes")
db_table_sizes = Gauge(
    "brownie_db_table_size_bytes", "Table size in bytes", ["table_name"]
)

redis_connections = Gauge("brownie_redis_connections_total", "Total Redis connections")
redis_memory_usage = Gauge(
    "brownie_redis_memory_usage_bytes", "Redis memory usage in bytes"
)
redis_hit_rate = Gauge("brownie_redis_hit_rate", "Redis cache hit rate")

business_metrics = {
    "organizations_total": Gauge(
        "brownie_organizations_total", "Total number of organizations"
    ),
    "teams_total": Gauge("brownie_teams_total", "Total number of teams"),
    "users_total": Gauge("brownie_users_total", "Total number of users"),
    "incidents_total": Gauge("brownie_incidents_total", "Total number of incidents"),
    "active_incidents": Gauge(
        "brownie_active_incidents_total", "Number of active incidents"
    ),
    "agent_configs_total": Gauge(
        "brownie_agent_configs_total", "Total number of agent configurations"
    ),
}


class MetricsCollector:
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "postgres"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "dbname": os.getenv("DB_NAME", "brownie_metadata"),
            "user": os.getenv("DB_USER", "brownie-fastapi-server"),
            "sslmode": os.getenv("DB_SSL_MODE", "require"),
            "sslcert": f"{os.getenv('CERT_DIR', '/certs')}/client.crt",
            "sslkey": f"{os.getenv('CERT_DIR', '/certs')}/client.key",
            "sslrootcert": f"{os.getenv('CERT_DIR', '/certs')}/ca.crt",
        }

        self.redis_config = {
            "host": os.getenv("REDIS_HOST", "redis"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "decode_responses": True,
        }

        self.metrics_port = int(os.getenv("METRICS_PORT", 9091))

    def collect_database_metrics(self):
        """Collect database performance metrics"""
        try:
            with psycopg.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Database size
                    cur.execute("SELECT pg_database_size(current_database())")
                    db_size_bytes.set(cur.fetchone()[0])

                    # Table sizes
                    cur.execute(
                        """
                        SELECT schemaname, tablename, pg_total_relation_size(schemaname||'.'||tablename) as size
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY size DESC
                    """
                    )
                    for schema, table, size in cur.fetchall():
                        db_table_sizes.labels(table_name=table).set(size)

                    # Connection stats
                    cur.execute(
                        """
                        SELECT state, count(*) 
                        FROM pg_stat_activity 
                        WHERE datname = current_database()
                        GROUP BY state
                    """
                    )
                    for state, count in cur.fetchall():
                        db_connections.labels(state=state).set(count)

                    # Business metrics
                    cur.execute("SELECT COUNT(*) FROM organizations")
                    business_metrics["organizations_total"].set(cur.fetchone()[0])

                    cur.execute("SELECT COUNT(*) FROM teams")
                    business_metrics["teams_total"].set(cur.fetchone()[0])

                    cur.execute("SELECT COUNT(*) FROM users")
                    business_metrics["users_total"].set(cur.fetchone()[0])

                    cur.execute("SELECT COUNT(*) FROM incidents")
                    business_metrics["incidents_total"].set(cur.fetchone()[0])

                    cur.execute("SELECT COUNT(*) FROM incidents WHERE status = 'OPEN'")
                    business_metrics["active_incidents"].set(cur.fetchone()[0])

                    cur.execute("SELECT COUNT(*) FROM agent_configs")
                    business_metrics["agent_configs_total"].set(cur.fetchone()[0])

        except Exception as e:
            logger.error("Failed to collect database metrics", error=str(e))
            db_query_errors.labels(error_type="connection").inc()

    def collect_redis_metrics(self):
        """Collect Redis performance metrics"""
        try:
            r = redis.Redis(**self.redis_config)

            # Connection info
            info = r.info()
            redis_connections.set(info.get("connected_clients", 0))
            redis_memory_usage.set(info.get("used_memory", 0))

            # Hit rate calculation
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            if total > 0:
                hit_rate = hits / total
                redis_hit_rate.set(hit_rate)
            else:
                redis_hit_rate.set(0)

        except Exception as e:
            logger.error("Failed to collect Redis metrics", error=str(e))

    def run(self):
        """Start the metrics collection server"""
        logger.info(
            "Starting Brownie Metadata Database metrics sidecar", port=self.metrics_port
        )

        # Start Prometheus metrics server
        start_http_server(self.metrics_port)

        # Collect metrics every 30 seconds
        while True:
            try:
                self.collect_database_metrics()
                self.collect_redis_metrics()
                logger.info("Metrics collected successfully")
            except Exception as e:
                logger.error("Failed to collect metrics", error=str(e))

            time.sleep(30)


if __name__ == "__main__":
    collector = MetricsCollector()
    collector.run()
