"""Contract tests for the local Docker Compose topology.

These tests pin the invariants of ``docker-compose.yml`` that the rest of the
platform depends on. They deliberately assert *structure* -- which services
exist, who depends on whom, and what has a healthcheck -- rather than asserting
branded names. Names are expected to change (see the identifier refactor), but
the shape of the topology is not, so a rename must not require editing this
file. Completeness of the rename is proven separately, by scanning the tree for
leftover identifiers.

Every test here reads the Compose file statically. Nothing starts a container,
so the suite runs in under a second and needs no Docker.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"

APP_SERVICES = {
    "auth-service",
    "user-service",
    "post-service",
    "like-service",
    "comment-service",
    "analytics-service",
    "worker-service",
    "frontend",
}

STATEFUL_SERVICES = {"postgres", "redis"}

EXPECTED_SERVICES = APP_SERVICES | STATEFUL_SERVICES

# `frontend` serves static assets through Nginx and holds no backend
# configuration, so it is the one app service that does not read .env.
ENV_FILE_SERVICES = APP_SERVICES - {"frontend"}

EXPECTED_HOST_PORTS = {
    "postgres": 5432,
    "redis": 6379,
    "auth-service": 8001,
    "user-service": 8002,
    "post-service": 8003,
    "like-service": 8004,
    "comment-service": 8005,
    "analytics-service": 8006,
    "worker-service": 9100,
    "frontend": 3000,
}

REDIS_CONSUMERS = {"post-service", "analytics-service", "worker-service"}


@pytest.fixture(scope="module")
def compose():
    """Parse the Compose file once for the whole module."""
    if not COMPOSE_FILE.exists():
        pytest.fail(f"{COMPOSE_FILE} is missing from the repository")
    with COMPOSE_FILE.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@pytest.fixture(scope="module")
def services(compose):
    return compose["services"]


def host_ports(service):
    """Return the host-side port for a service, tolerating int or str form."""
    ports = service.get("ports", [])
    if not ports:
        return None
    mapping = ports[0]
    if isinstance(mapping, int):
        return mapping
    return int(str(mapping).split(":")[0])


def depends_on(service):
    """Return the set of service names a service declares a dependency on.

    Compose accepts two forms and this file uses both: a list, which expresses
    start ordering only, and a mapping, which can additionally gate on
    condition. Both are normalized to a set of names here.
    """
    deps = service.get("depends_on") or {}
    if isinstance(deps, list):
        return set(deps)
    return set(deps)


def dependency_condition(service, dependency):
    """Return the condition gating a dependency, or None if there is no gate.

    List-form `depends_on` carries no conditions, so it yields None. The caller
    must therefore treat None as "ordering only" rather than as a failure.
    """
    deps = service.get("depends_on") or {}
    if not isinstance(deps, dict):
        return None
    entry = deps.get(dependency)
    if isinstance(entry, dict):
        return entry.get("condition")
    return None


def test_compose_file_is_parseable(compose):
    assert isinstance(compose, dict), "docker-compose.yml did not parse to a mapping"
    assert "services" in compose, "docker-compose.yml has no top-level 'services'"


def test_expected_services_are_defined(services):
    assert set(services) == EXPECTED_SERVICES


def test_each_service_publishes_its_documented_host_port(services):
    for name, expected_port in EXPECTED_HOST_PORTS.items():
        assert host_ports(services[name]) == expected_port, (
            f"{name} should publish host port {expected_port}, "
            f"found {host_ports(services[name])}"
        )


def test_application_services_require_a_dot_env_file(services):
    """The seven backend services read configuration from .env via env_file.

    This is the contract that makes `cp .env.example .env` a mandatory setup
    step: without it Compose refuses to start these services at all. `frontend`
    is excluded because it serves static assets and holds no backend config.
    """
    for name in sorted(ENV_FILE_SERVICES):
        assert services[name].get("env_file"), (
            f"{name} must declare env_file; without .env it cannot start"
        )


def test_frontend_needs_no_dot_env_file(services):
    """frontend is a static Nginx site and must stay startable without .env."""
    assert not services["frontend"].get("env_file")


def test_stateful_services_do_not_depend_on_a_dot_env_file(services):
    """postgres and redis are configured with inline defaults instead.

    They must stay startable without a .env present, which is what makes them
    usable as healthcheck-gated dependencies in a clean checkout.
    """
    for name in sorted(STATEFUL_SERVICES):
        assert not services[name].get("env_file"), (
            f"{name} should be configured via environment: defaults, not env_file"
        )


def test_stateful_services_declare_healthchecks(services):
    """Every service_healthy dependency requires the target to have one."""
    for name in sorted(STATEFUL_SERVICES):
        assert services[name].get("healthcheck"), (
            f"{name} must declare a healthcheck; dependents wait on its status"
        )


def test_healthy_dependencies_target_services_that_have_healthchecks(services):
    """Catch a health-gated dependency pointing at a service with no probe.

    Compose fails at startup in this case, but the error is opaque, so it is
    asserted here where the message can name the offending service.
    """
    for name, service in services.items():
        for dependency in depends_on(service):
            if dependency_condition(service, dependency) == "service_healthy":
                assert services[dependency].get("healthcheck"), (
                    f"{name} waits for {dependency} to be healthy, "
                    f"but {dependency} declares no healthcheck"
                )


def test_only_declared_redis_consumers_depend_on_redis(services):
    """Redis is used by three services, and the topology must say so.

    An accidental extra dependency is easy to introduce and expensive to
    diagnose at runtime, so it is pinned explicitly.
    """
    for name, service in services.items():
        depends_on_redis = "redis" in depends_on(service)
        if name in REDIS_CONSUMERS:
            assert depends_on_redis, f"{name} consumes Redis and must depend on it"
        else:
            assert not depends_on_redis, f"{name} must not depend on Redis"


def test_every_service_joins_a_network(services):
    """A service outside the network cannot resolve the others by name."""
    for name, service in services.items():
        assert service.get("networks"), f"{name} is not attached to any network"


def test_top_level_volumes_match_the_declarations(services, compose):
    """Named volumes must be declared at the top level to be created."""
    declared = set(compose.get("volumes") or {})
    for name, service in services.items():
        for mount in service.get("volumes", []):
            if not isinstance(mount, str):
                continue
            source = mount.split(":")[0]
            if source.startswith("./") or source.startswith("/"):
                continue
            assert source in declared, (
                f"{name} mounts named volume '{source}', which is not declared "
                f"under the top-level 'volumes' key"
            )
