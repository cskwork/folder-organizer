"""
Unit tests for the dependency injection container.
"""

import pytest
from unittest.mock import Mock
from di_container import DIContainer, ServiceLifetime, ServiceDescriptor


class TestDIContainer:
    """Test cases for the DI container."""
    
    def test_register_singleton(self):
        """Test singleton service registration."""
        container = DIContainer()
        
        class TestService:
            def __init__(self):
                self.value = "test"
        
        container.register_singleton(TestService)
        
        # Should return same instance
        instance1 = container.resolve(TestService)
        instance2 = container.resolve(TestService)
        
        assert instance1 is instance2
        assert instance1.value == "test"
    
    def test_register_transient(self):
        """Test transient service registration."""
        container = DIContainer()
        
        class TestService:
            def __init__(self):
                self.value = "test"
        
        container.register_transient(TestService)
        
        # Should return different instances
        instance1 = container.resolve(TestService)
        instance2 = container.resolve(TestService)
        
        assert instance1 is not instance2
        assert instance1.value == instance2.value
    
    def test_register_with_factory(self):
        """Test service registration with factory function."""
        container = DIContainer()
        
        class TestService:
            def __init__(self, value):
                self.value = value
        
        def factory(container):
            return TestService("factory_value")
        
        container.register_singleton(TestService, factory=factory)
        
        instance = container.resolve(TestService)
        assert instance.value == "factory_value"
    
    def test_register_with_instance(self):
        """Test service registration with existing instance."""
        container = DIContainer()
        
        class TestService:
            def __init__(self):
                self.value = "instance"
        
        existing_instance = TestService()
        container.register_singleton(TestService, instance=existing_instance)
        
        resolved_instance = container.resolve(TestService)
        assert resolved_instance is existing_instance
    
    def test_dependency_injection(self):
        """Test automatic dependency injection."""
        container = DIContainer()
        
        class Dependency:
            def __init__(self):
                self.value = "dependency"
        
        class Service:
            def __init__(self, dependency: Dependency):
                self.dependency = dependency
        
        container.register_singleton(Dependency)
        container.register_transient(Service)
        
        service = container.resolve(Service)
        assert service.dependency.value == "dependency"
    
    def test_unregistered_service_error(self):
        """Test error when resolving unregistered service."""
        container = DIContainer()
        
        class UnregisteredService:
            pass
        
        with pytest.raises(ValueError, match="Service UnregisteredService not registered"):
            container.resolve(UnregisteredService)
    
    def test_is_registered(self):
        """Test service registration check."""
        container = DIContainer()
        
        class TestService:
            pass
        
        assert not container.is_registered(TestService)
        
        container.register_singleton(TestService)
        assert container.is_registered(TestService)
    
    def test_clear(self):
        """Test container clearing."""
        container = DIContainer()
        
        class TestService:
            pass
        
        container.register_singleton(TestService)
        assert container.is_registered(TestService)
        
        container.clear()
        assert not container.is_registered(TestService)


class TestServiceDescriptor:
    """Test cases for service descriptor."""
    
    def test_service_descriptor_creation(self):
        """Test service descriptor creation."""
        class TestService:
            pass
        
        descriptor = ServiceDescriptor(
            TestService,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        assert descriptor.service_type == TestService
        assert descriptor.implementation == TestService
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
    
    def test_service_descriptor_with_factory(self):
        """Test service descriptor with factory."""
        class TestService:
            pass
        
        def factory():
            return TestService()
        
        descriptor = ServiceDescriptor(
            TestService,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        
        assert descriptor.factory == factory
        assert descriptor.lifetime == ServiceLifetime.TRANSIENT
    
    def test_service_descriptor_validation(self):
        """Test service descriptor validation."""
        class TestService:
            pass
        
        with pytest.raises(ValueError, match="Either implementation or factory must be provided"):
            ServiceDescriptor(TestService, implementation=None, factory=None)