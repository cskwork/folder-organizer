"""Centralized logging configuration for the Intelligent File Organizer."""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class LoggerSetup:
    """Centralized logger setup and configuration."""
    
    _initialized = False
    
    @classmethod
    def setup_logging(
        cls,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> None:
        """Setup structured logging for the application.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file. If None, creates default in logs/ directory
            max_file_size: Maximum log file size in bytes before rotation
            backup_count: Number of backup log files to keep
        """
        if cls._initialized:
            return
            
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Set default log file if not provided
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = log_dir / f"file_organizer_{timestamp}.log"
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler with rotation
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # Set specific logger levels
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        
        cls._initialized = True
        logging.info(f"Logging initialized with level {log_level}")
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger instance with the given name.
        
        Args:
            name: Name for the logger (usually __name__)
            
        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)


class StructuredLogger:
    """Wrapper for structured logging with context."""
    
    def __init__(self, name: str):
        self.logger = LoggerSetup.get_logger(name)
        self._context = {}
    
    def add_context(self, **kwargs) -> None:
        """Add context to all future log messages."""
        self._context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear all context."""
        self._context.clear()
    
    def _format_message(self, message: str) -> str:
        """Format message with context."""
        if self._context:
            context_str = " | ".join(f"{k}={v}" for k, v in self._context.items())
            return f"{message} | {context_str}"
        return message
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context."""
        if kwargs:
            self.add_context(**kwargs)
        self.logger.debug(self._format_message(message))
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        if kwargs:
            self.add_context(**kwargs)
        self.logger.info(self._format_message(message))
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context."""
        if kwargs:
            self.add_context(**kwargs)
        self.logger.warning(self._format_message(message))
    
    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message with context."""
        if kwargs:
            self.add_context(**kwargs)
        self.logger.error(self._format_message(message), exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log critical message with context."""
        if kwargs:
            self.add_context(**kwargs)
        self.logger.critical(self._format_message(message), exc_info=exc_info)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with full traceback."""
        if kwargs:
            self.add_context(**kwargs)
        self.logger.exception(self._format_message(message))


# Initialize logging on module import
LoggerSetup.setup_logging()