import logging
from typing import Optional, Any, Callable
from pathlib import Path
from ..config.logging_config import StructuredLogger

class FileOrganizerError(Exception):
    """Base exception class for file organizer errors"""
    pass

class OllamaConnectionError(FileOrganizerError):
    """Exception raised when connection to Ollama fails"""
    pass

class RetryableError(FileOrganizerError):
    """Exception for operations that can be retried"""
    pass

class FileCategorizationError(FileOrganizerError):
    """Exception raised when file categorization fails"""
    pass

class FileOperationError(FileOrganizerError):
    """Exception raised when file operations fail"""
    pass

class ErrorHandler:
    """Enhanced error handler with structured logging and retry logic."""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.logger = StructuredLogger('FileOrganizer.ErrorHandler')
        self.retry_counts = {}
        self.error_stats = {
            'total_errors': 0,
            'retryable_errors': 0,
            'fatal_errors': 0,
            'successful_retries': 0
        }

    def retry_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """Retry an operation with exponential backoff and detailed logging."""
        from time import sleep
        operation_name = getattr(operation, '__name__', str(operation))
        
        self.logger.add_context(
            operation=operation_name,
            max_retries=self.max_retries,
            args_count=len(args),
            kwargs_count=len(kwargs)
        )
        
        try:
            for attempt in range(self.max_retries):
                try:
                    self.logger.debug(f"Attempting operation {operation_name}", attempt=attempt + 1)
                    result = operation(*args, **kwargs)
                    
                    if attempt > 0:
                        self.error_stats['successful_retries'] += 1
                        self.logger.info(f"Operation {operation_name} succeeded after {attempt + 1} attempts")
                    
                    return result
                    
                except RetryableError as e:
                    self.error_stats['retryable_errors'] += 1
                    
                    if attempt == self.max_retries - 1:
                        self.logger.error(f"Operation {operation_name} failed after {self.max_retries} attempts", 
                                        error_type="RetryableError", 
                                        final_error=str(e))
                        raise
                        
                    wait_time = (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...",
                                      attempt=attempt + 1,
                                      wait_time=wait_time,
                                      error=str(e))
                    sleep(wait_time)
                    
                except Exception as e:
                    self.error_stats['fatal_errors'] += 1
                    self.logger.error(f"Non-retryable error in {operation_name}", 
                                    error_type=type(e).__name__, 
                                    error=str(e),
                                    exc_info=True)
                    raise
        finally:
            self.logger.clear_context()

    def handle_error(self, error: Exception, context: str = "") -> str:
        """Handle different types of errors with enhanced logging and context."""
        self.error_stats['total_errors'] += 1
        error_type = type(error).__name__
        
        self.logger.add_context(
            error_type=error_type,
            context=context,
            total_errors=self.error_stats['total_errors']
        )
        
        try:
            if isinstance(error, KeyboardInterrupt):
                self.logger.info("Operation interrupted by user")
                return "Operation cancelled by user"
                
            elif isinstance(error, OllamaConnectionError):
                self.logger.error(f"Ollama connection error: {str(error)}", exc_info=True)
                return f"Failed to connect to Ollama: {context}. Please ensure Ollama is running."
                
            elif isinstance(error, FileCategorizationError):
                self.logger.warning(f"Categorization error: {str(error)}")
                return f"Unable to categorize file: {context}"
                
            elif isinstance(error, FileOperationError):
                self.logger.error(f"File operation error: {str(error)}", exc_info=True)
                return f"Error during file operation: {context}"
                
            elif isinstance(error, RetryableError):
                self.logger.warning(f"Retryable error: {str(error)}")
                return f"Operation failed after retries: {context}"
                
            else:
                self.logger.error(f"Unexpected error: {str(error)}", exc_info=True)
                return f"Unexpected error: {context}"
        
        finally:
            self.logger.clear_context()

    def log_info(self, message: str, **kwargs) -> None:
        """Log informational messages with optional context."""
        self.logger.info(message, **kwargs)

    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning messages with optional context."""
        self.logger.warning(message, **kwargs)

    def log_error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error messages with optional context and exception info."""
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def get_error_stats(self) -> dict:
        """Get current error statistics."""
        return self.error_stats.copy()
    
    def reset_error_stats(self) -> None:
        """Reset error statistics."""
        self.error_stats = {
            'total_errors': 0,
            'retryable_errors': 0,
            'fatal_errors': 0,
            'successful_retries': 0
        }
        self.logger.info("Error statistics reset")
