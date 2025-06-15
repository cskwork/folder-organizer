"""
Interface definitions for the File Organizer application.

This module defines abstract interfaces that decouple the application's components,
enabling dependency injection and improved testability.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Tuple, List
from pathlib import Path
import asyncio

class IConfigManager(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting."""
        pass
    
    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """Set configuration setting."""
        pass
    
    @abstractmethod
    def get_organization_rules(self) -> Dict[str, Any]:
        """Get organization rules."""
        pass
    
    @abstractmethod
    def add_observer(self, observer) -> None:
        """Add configuration change observer."""
        pass
    
    @abstractmethod
    def remove_observer(self, observer) -> None:
        """Remove configuration change observer."""
        pass

class IFileAnalyzer(ABC):
    """Interface for file analysis operations."""
    
    @abstractmethod
    async def analyze_directory_async(self, directory: str, 
                                    use_content: bool = True,
                                    use_type: bool = True, 
                                    use_date: bool = True,
                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Analyze directory asynchronously."""
        pass
    
    @abstractmethod
    async def analyze_file_async(self, file_path: str) -> Dict[str, Any]:
        """Analyze single file asynchronously."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop analysis operations."""
        pass

class IContentAnalyzer(ABC):
    """Interface for content analysis operations."""
    
    @abstractmethod
    async def analyze_content_async(self, file_path: str, 
                                  content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze file content asynchronously."""
        pass
    
    @abstractmethod
    async def suggest_name_async(self, file_path: str, 
                               content: Optional[str] = None) -> Optional[str]:
        """Suggest smart file name asynchronously."""
        pass

class IFileOrganizer(ABC):
    """Interface for file organization operations."""
    
    @abstractmethod
    async def organize_files_async(self, 
                                 source_dir: str,
                                 analysis_results: Dict[str, Any],
                                 remove_empty: bool = True,
                                 progress_callback: Optional[Callable] = None) -> None:
        """Organize files asynchronously."""
        pass
    
    @abstractmethod
    def determine_para_category(self, file_path: str, 
                              analysis: Dict[str, Any]) -> Tuple[str, str]:
        """Determine PARA category for file."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """Get operation statistics."""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """Undo last operation."""
        pass
    
    @abstractmethod
    def redo(self) -> bool:
        """Redo last undone operation."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop organization operations."""
        pass

class IFileRenamer(ABC):
    """Interface for file renaming operations."""
    
    @abstractmethod
    async def rename_file_async(self, old_path: str, new_name: str) -> str:
        """Rename file asynchronously."""
        pass
    
    @abstractmethod
    def generate_safe_name(self, original_name: str, 
                         destination_dir: str) -> str:
        """Generate safe filename."""
        pass

class IErrorHandler(ABC):
    """Interface for error handling operations."""
    
    @abstractmethod
    async def retry_operation_async(self, operation: Callable, 
                                  *args, **kwargs) -> Any:
        """Retry operation asynchronously."""
        pass
    
    @abstractmethod
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with context."""
        pass

class IProgressReporter(ABC):
    """Interface for progress reporting."""
    
    @abstractmethod
    def report_progress(self, current: int, total: int, message: str) -> None:
        """Report progress update."""
        pass
    
    @abstractmethod
    def is_cancelled(self) -> bool:
        """Check if operation is cancelled."""
        pass
    
    @abstractmethod
    def cancel(self) -> None:
        """Cancel operation."""
        pass

class IUIService(ABC):
    """Interface for UI operations decoupled from business logic."""
    
    @abstractmethod
    def show_message(self, title: str, message: str, 
                    message_type: str = "info") -> None:
        """Show message to user."""
        pass
    
    @abstractmethod
    def show_error(self, title: str, message: str) -> None:
        """Show error message to user."""
        pass
    
    @abstractmethod
    def show_success(self, title: str, message: str) -> None:
        """Show success message to user."""
        pass
    
    @abstractmethod
    def ask_confirmation(self, title: str, message: str) -> bool:
        """Ask user for confirmation."""
        pass
    
    @abstractmethod
    def select_directory(self, title: str = "Select Directory") -> Optional[str]:
        """Show directory selection dialog."""
        pass

class IBusinessLogicService(ABC):
    """Interface for core business logic operations."""
    
    @abstractmethod
    async def analyze_and_organize_async(self, 
                                       source_directory: str,
                                       options: Dict[str, Any],
                                       progress_reporter: IProgressReporter) -> Dict[str, Any]:
        """Main business logic workflow."""
        pass
    
    @abstractmethod
    async def preview_organization_async(self, 
                                       source_directory: str,
                                       options: Dict[str, Any]) -> Dict[str, Any]:
        """Preview organization without executing."""
        pass
    
    @abstractmethod
    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get history of operations for undo/redo."""
        pass

class IAsyncOperationManager(ABC):
    """Interface for managing async operations."""
    
    @abstractmethod
    async def execute_with_progress(self, 
                                  operation: Callable,
                                  progress_reporter: IProgressReporter,
                                  *args, **kwargs) -> Any:
        """Execute operation with progress tracking."""
        pass
    
    @abstractmethod
    def cancel_all_operations(self) -> None:
        """Cancel all running operations."""
        pass
    
    @abstractmethod
    def get_active_operations(self) -> List[str]:
        """Get list of active operation IDs."""
        pass