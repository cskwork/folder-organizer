import logging
from typing import Optional
from pathlib import Path

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
    def __init__(self, log_file: Optional[str] = None, max_retries: int = 3):
        self.max_retries = max_retries
        self.logger = logging.getLogger('FileOrganizer')
        self.logger.setLevel(logging.INFO)
        
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            handler = logging.FileHandler(log_dir / "file_organizer.log")
            
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Add console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def retry_operation(self, operation, *args, **kwargs):
        """Retry an operation with exponential backoff"""
        from time import sleep
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except RetryableError as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = (2 ** attempt)  # Exponential backoff
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
                sleep(wait_time)
            except Exception as e:
                # Non-retryable error
                raise

    def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle different types of errors and log them appropriately"""
        if isinstance(error, KeyboardInterrupt):
            self.logger.info("Operation interrupted by user")
            return "Operation cancelled by user"
            
        elif isinstance(error, OllamaConnectionError):
            self.logger.error(f"Ollama connection error: {str(error)} - Context: {context}")
            return f"Failed to connect to Ollama: {context}. Please ensure Ollama is running."
            
        elif isinstance(error, FileCategorizationError):
            self.logger.warning(f"Categorization error: {str(error)} - Context: {context}")
            return f"Unable to categorize file: {context}"
            
        elif isinstance(error, FileOperationError):
            self.logger.error(f"File operation error: {str(error)} - Context: {context}")
            return f"Error during file operation: {context}"
            
        elif isinstance(error, RetryableError):
            self.logger.warning(f"Retryable error: {str(error)} - Context: {context}")
            return f"Operation failed after retries: {context}"
            
        else:
            self.logger.error(f"Unexpected error: {str(error)} - Context: {context}")
            return f"Unexpected error: {context}"

    def log_info(self, message: str) -> None:
        """Log informational messages"""
        self.logger.info(message)

    def log_warning(self, message: str) -> None:
        """Log warning messages"""
        self.logger.warning(message)

    def log_error(self, message: str) -> None:
        """Log error messages"""
        self.logger.error(message)
