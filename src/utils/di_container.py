"""
Dependency Injection Container for the File Organizer application.

This module provides a centralized way to manage dependencies and their lifecycles,
replacing the tight coupling in the original architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, Any, Optional, Callable, TypeVar, Generic
import threading
from enum import Enum

T = TypeVar('T')

# Sentinel for distinguishing between default None and explicit None
_NOT_PROVIDED = object()

class ServiceLifetime(Enum):
    """Service lifetime management options."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class ServiceDescriptor:
    """Describes how a service should be created and managed."""
    
    def __init__(self, 
                 service_type: Type[T],
                 implementation: Optional[Type[T]] = _NOT_PROVIDED,
                 factory: Optional[Callable[..., T]] = None,
                 lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
                 instance: Optional[T] = None):
        self.service_type = service_type
        self.factory = factory
        self.lifetime = lifetime
        self.instance = instance
        
        # Check if explicitly setting both implementation and factory to None
        if implementation is None and factory is None and instance is None:
            raise ValueError("Either implementation or factory must be provided")
        
        # Set implementation with fallback to service_type
        self.implementation = implementation if implementation is not _NOT_PROVIDED else service_type

class DIContainer:
    """Dependency Injection Container with thread-safe singleton management."""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        
    def register_singleton(self, service_type: Type[T], 
                          implementation: Optional[Type[T]] = None,
                          factory: Optional[Callable[..., T]] = None,
                          instance: Optional[T] = None) -> 'DIContainer':
        """Register a service as singleton."""
        with self._lock:
            if instance is not None:
                self._services[service_type] = ServiceDescriptor(
                    service_type, instance=instance, lifetime=ServiceLifetime.SINGLETON
                )
                self._singletons[service_type] = instance
            else:
                # If no implementation provided, use service_type as implementation
                impl = implementation if implementation is not None else service_type
                self._services[service_type] = ServiceDescriptor(
                    service_type, impl, factory, ServiceLifetime.SINGLETON
                )
        return self
        
    def register_transient(self, service_type: Type[T], 
                          implementation: Optional[Type[T]] = None,
                          factory: Optional[Callable[..., T]] = None) -> 'DIContainer':
        """Register a service as transient (new instance each time)."""
        with self._lock:
            # If no implementation provided, use service_type as implementation
            impl = implementation if implementation is not None else service_type
            self._services[service_type] = ServiceDescriptor(
                service_type, impl, factory, ServiceLifetime.TRANSIENT
            )
        return self
        
    def register_scoped(self, service_type: Type[T], 
                       implementation: Optional[Type[T]] = None,
                       factory: Optional[Callable[..., T]] = None) -> 'DIContainer':
        """Register a service as scoped (per operation/request)."""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type, implementation, factory, ServiceLifetime.SCOPED
            )
        return self
        
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance."""
        with self._lock:
            if service_type not in self._services:
                raise ValueError(f"Service {service_type.__name__} not registered")
                
            descriptor = self._services[service_type]
            
            # Return existing singleton
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if service_type in self._singletons:
                    return self._singletons[service_type]
                    
            # Create new instance
            instance = self._create_instance(descriptor)
            
            # Store singleton
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                self._singletons[service_type] = instance
                
            return instance
            
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new instance of the service."""
        if descriptor.instance is not None:
            return descriptor.instance
            
        if descriptor.factory:
            return descriptor.factory(self)
            
        # Auto-wire constructor dependencies
        constructor = descriptor.implementation.__init__
        if hasattr(constructor, '__annotations__'):
            # Get constructor parameter types
            annotations = constructor.__annotations__
            kwargs = {}
            
            for param_name, param_type in annotations.items():
                if param_name == 'return':
                    continue
                if param_type in self._services:
                    kwargs[param_name] = self.resolve(param_type)
                    
            return descriptor.implementation(**kwargs)
        else:
            return descriptor.implementation()
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services
    
    def clear(self) -> None:
        """Clear all registrations and singletons."""
        with self._lock:
            self._services.clear()
            self._singletons.clear()

# Global container instance
_container: Optional[DIContainer] = None
_container_lock = threading.RLock()

def get_container() -> DIContainer:
    """Get the global dependency injection container."""
    global _container
    with _container_lock:
        if _container is None:
            _container = DIContainer()
        return _container

def set_container(container: DIContainer) -> None:
    """Set the global dependency injection container."""
    global _container
    with _container_lock:
        _container = container