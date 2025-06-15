"""
Service configuration for dependency injection setup.
"""

from utils.di_container import DIContainer, get_container
from interfaces import *
from config_manager import ConfigManager
from async_file_analyzer import AsyncFileAnalyzer
from async_content_analyzer import AsyncContentAnalyzer
from async_file_organizer import AsyncFileOrganizer
from business_logic_service import BusinessLogicService
from ui_service import UIService
from file_renamer import FileRenamer
from error_handler import ErrorHandler

def configure_services(container: DIContainer = None) -> DIContainer:
    """Configure all services for dependency injection."""
    
    if container is None:
        container = get_container()
    
    # Core services (singletons)
    container.register_singleton(
        IConfigManager, 
        implementation=ConfigManager
    )
    
    container.register_singleton(
        IErrorHandler,
        implementation=ErrorHandler
    )
    
    container.register_singleton(
        IFileRenamer,
        implementation=FileRenamer
    )
    
    # Content analyzer (singleton for caching)
    container.register_singleton(
        IContentAnalyzer,
        factory=lambda c: AsyncContentAnalyzer(c.resolve(IConfigManager))
    )
    
    # File analyzer (transient for multiple operations)
    container.register_transient(
        IFileAnalyzer,
        factory=lambda c: AsyncFileAnalyzer(
            c.resolve(IConfigManager),
            c.resolve(IContentAnalyzer)
        )
    )
    
    # File organizer (transient for multiple operations)
    container.register_transient(
        IFileOrganizer,
        factory=lambda c: AsyncFileOrganizer(
            c.resolve(IConfigManager),
            c.resolve(IFileRenamer),
            c.resolve(IErrorHandler)
        )
    )
    
    # Business logic service (singleton)
    container.register_singleton(
        IBusinessLogicService,
        factory=lambda c: BusinessLogicService(
            c.resolve(IFileAnalyzer),
            c.resolve(IFileOrganizer),
            c.resolve(IConfigManager)
        )
    )
    
    # UI service (singleton)
    container.register_singleton(
        IUIService,
        implementation=UIService
    )
    
    return container

def get_service(service_type: type):
    """Get a service instance from the configured container."""
    container = get_container()
    return container.resolve(service_type)

def configure_for_testing() -> DIContainer:
    """Configure services for testing with mocks."""
    from unittest.mock import Mock
    
    container = DIContainer()
    
    # Mock implementations for testing
    container.register_singleton(IConfigManager, instance=Mock())
    container.register_singleton(IErrorHandler, instance=Mock())
    container.register_singleton(IFileRenamer, instance=Mock())
    container.register_singleton(IContentAnalyzer, instance=Mock())
    container.register_singleton(IFileAnalyzer, instance=Mock())
    container.register_singleton(IFileOrganizer, instance=Mock())
    container.register_singleton(IBusinessLogicService, instance=Mock())
    container.register_singleton(IUIService, instance=Mock())
    
    return container

# Application startup configuration
def initialize_application() -> DIContainer:
    """Initialize the application with all services configured."""
    container = configure_services()
    
    # Perform any additional setup
    config_manager = container.resolve(IConfigManager)
    
    # Load configuration
    try:
        # Ensure config is loaded and valid
        rules = config_manager.get_organization_rules()
        if not rules:
            # Set default rules if none exist
            default_rules = {
                "use_content_analysis": True,
                "use_file_type": True,
                "use_date": True,
                "smart_rename_enabled": True
            }
            for key, value in default_rules.items():
                config_manager.set_setting(f"organization_rules.{key}", value)
    except Exception as e:
        print(f"Warning: Failed to initialize configuration: {e}")
    
    return container

# Cleanup function
def cleanup_services():
    """Cleanup all services on application shutdown."""
    try:
        container = get_container()
        
        # Stop async services
        if container.is_registered(IFileAnalyzer):
            file_analyzer = container.resolve(IFileAnalyzer)
            if hasattr(file_analyzer, 'stop'):
                file_analyzer.stop()
        
        if container.is_registered(IFileOrganizer):
            file_organizer = container.resolve(IFileOrganizer)
            if hasattr(file_organizer, 'stop'):
                file_organizer.stop()
        
        if container.is_registered(IContentAnalyzer):
            content_analyzer = container.resolve(IContentAnalyzer)
            if hasattr(content_analyzer, 'close'):
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(content_analyzer.close())
                    else:
                        loop.run_until_complete(content_analyzer.close())
                except:
                    pass
        
        # Clear container
        container.clear()
        
    except Exception as e:
        print(f"Warning: Error during service cleanup: {e}")

# Service health check
def check_service_health() -> Dict[str, bool]:
    """Check health of all services."""
    health_status = {}
    
    try:
        container = get_container()
        
        # Check if services are properly registered
        service_types = [
            IConfigManager,
            IErrorHandler,
            IFileRenamer,
            IContentAnalyzer,
            IFileAnalyzer,
            IFileOrganizer,
            IBusinessLogicService,
            IUIService
        ]
        
        for service_type in service_types:
            try:
                service = container.resolve(service_type)
                health_status[service_type.__name__] = service is not None
            except Exception as e:
                health_status[service_type.__name__] = False
                print(f"Service {service_type.__name__} health check failed: {e}")
    
    except Exception as e:
        print(f"Health check failed: {e}")
        return {service.__name__: False for service in service_types}
    
    return health_status