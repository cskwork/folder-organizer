import os
from typing import Dict, Any, Optional
import requests
import json
from pathlib import Path
import mimetypes
import magic
import langdetect
import re
from korean_utils import KoreanTextHandler

class ContentAnalyzer:
    """Analyzes file content and suggests appropriate names using LLM."""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.korean_handler = KoreanTextHandler()
        
        # Default configurations
        self.content_config = {
            "text_sample_length": 2000,
            "language_sample_length": 1000,
            "confidence_scores": {
                "korean": 0.8,
                "other": 0.7,
                "java_class": 0.9
            }
        }
        
        # Default LLM configuration
        self.provider = "openrouter"
        self.providers_config = {
            "openrouter": {
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "default_model": "google/gemini-pro"
            }
        }
        self.model_configs = {}
        
        if config_manager:
            # Load content analysis config
            self.content_config = config_manager.get_setting("content_analysis", self.content_config)
            
            # Load LLM config
            llm_config = config_manager.get_setting("llm_config", {})
            if llm_config:
                self.provider = llm_config.get("default_provider", self.provider)
                provider_configs = llm_config.get("providers", {})
                
                # Only update providers that are configured
                for provider, config in provider_configs.items():
                    if config and isinstance(config, dict):
                        self.providers_config[provider] = config
                
                self.model_configs = llm_config.get("model_configs", {})
                
                # Log current LLM configuration
                print("\nLLM Configuration:")
                print(f"- Active Provider: {self.provider}")
                print(f"- Available Providers: {list(self.providers_config.keys())}")
                if self.provider in self.providers_config:
                    provider_config = self.providers_config[self.provider]
                    print(f"- Model: {provider_config.get('default_model', 'not specified')}")
                    print(f"- API URL: {provider_config.get('url', 'not specified')}")
                    if 'api_key' in provider_config:
                        key_status = "configured" if provider_config['api_key'] else "not configured"
                        print(f"- API Key: {key_status}")
                print()
        
    def analyze_for_rename(self, file_path: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content and suggest a name."""
        try:
            print("\nStarting content analysis:")
            content_type = content_data.get('type', '')
            content_text = content_data.get('text', '')
            
            print(f"- Content type: {content_type}")
            print(f"- Content length: {len(content_text) if content_text else 0} chars")
            
            if not content_text:
                print("Error: No content available")
                return {
                    'success': False,
                    'error': 'No content available for analysis'
                }
            
            # Enhanced language detection with Korean support
            print("\nPerforming language detection:")
            is_korean = self.korean_handler.detect_korean_content(content_text[:self.content_config["language_sample_length"]])
            try:
                language = 'ko' if is_korean else langdetect.detect(content_text[:self.content_config["language_sample_length"]])
                print(f"- Detected language: {language}")
                print(f"- Is Korean: {is_korean}")
            except Exception as e:
                print(f"- Language detection failed: {str(e)}")
                language = 'unknown'
            
            # Handle Java files specifically
            if file_path.lower().endswith('.java'):
                print("\nProcessing Java file:")
                try:
                    # Extract class name and package info
                    print("- Attempting to extract class name and package")
                    class_match = re.search(r'public\s+class\s+(\w+)', content_text)
                    package_match = re.search(r'package\s+([\w.]+);', content_text)
                    
                    if class_match:
                        class_name = class_match.group(1)
                        package_name = package_match.group(1) if package_match else "unknown"
                        print(f"- Found class name: {class_name}")
                        print(f"- Found package: {package_name}")
                        
                        return {
                            'success': True,
                            'suggested_name': class_name,
                            'confidence': self.content_config["confidence_scores"]["java_class"],
                            'language': language,
                            'metadata': {
                                'package': package_name,
                                'class': class_name
                            }
                        }
                    else:
                        print("- No class name found in Java file")
                        print("- File content sample:")
                        print(content_text[:200] + "...")  # Print first 200 chars for debugging
                        
                        # Validate LLM config before proceeding
                        if not self.provider or not self.providers_config.get(self.provider):
                            print("Error: LLM provider not properly configured")
                            return {
                                'success': False,
                                'error': 'LLM provider not configured for fallback analysis'
                            }
                            
                        print("- Proceeding with LLM analysis")
                except Exception as e:
                    print(f"Error in Java file analysis: {str(e)}")
                    return {
                        'success': False,
                        'error': f'Failed to analyze Java file: {str(e)}'
                    }
            
            # Create prompt with language-specific handling
            print("\nPreparing LLM prompt:")
            prompt = self._create_rename_prompt(content_type, content_text[:self.content_config["text_sample_length"]], language)
            print(f"- Prompt length: {len(prompt)} chars")
            
            # Get suggestion from LLM
            print("\nQuerying LLM:")
            print(f"- Current provider: {self.provider}")
            print(f"- Provider config: {self.providers_config.get(self.provider)}")
            
            response = self._query_llm(prompt)
            print(f"- LLM response: {response if response else 'None'}")
            
            if not response:
                error_msg = f'Provider {self.provider} failed to analyze content'
                print(f"Error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Process suggested name
            print("\nProcessing suggested name:")
            suggested_name = response.strip()
            print(f"- Raw suggestion: {suggested_name}")
            
            if is_korean:
                suggested_name = self.korean_handler.sanitize_filename(suggested_name)
                print(f"- Sanitized Korean name: {suggested_name}")
            
            confidence_score = self.content_config["confidence_scores"]["korean" if is_korean else "other"]
            print(f"- Confidence score: {confidence_score}")
            
            result = {
                'success': True,
                'suggested_name': suggested_name,
                'confidence': confidence_score,
                'language': language
            }
            print(f"\nFinal result: {result}")
            return result
            
        except Exception as e:
            error_msg = f'Error analyzing content with {self.provider}: {str(e)}'
            print(f"\nError in analyze_for_rename: {error_msg}")
            print(f"Exception type: {type(e).__name__}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def _create_rename_prompt(self, content_type: str, content_text: str, language: str) -> str:
        """Create a prompt for the LLM with language-specific considerations."""
        if language == 'ko':
            prompt = (
                "다음 파일의 내용을 분석하여 적절한 파일 이름을 제안해주세요.\n"
                "파일 이름은 다음 조건을 만족해야 합니다:\n"
                "1. 파일의 주요 내용이나 목적을 잘 나타내야 함\n"
                "2. 한글과 영문 모두 사용 가능\n"
                "3. 길이는 2-5단어 정도로 적절하게\n"
                "4. 특수문자는 하이픈(-)만 사용\n"
                "5. 확장자는 제외\n\n"
                f"파일 종류: {content_type}\n"
                f"파일 내용:\n{content_text}\n\n"
                "파일 이름 제안 (확장자 제외): "
            )
        else:
            prompt = (
                "Suggest a filename for the following content.\n"
                "The filename should:\n"
                "1. Reflect the main content or purpose\n"
                "2. Be 2-5 words long\n"
                "3. Use only hyphens for separators\n"
                "4. Exclude the extension\n\n"
                f"Content type: {content_type}\n"
                f"Content:\n{content_text}\n\n"
                "Suggested filename (without extension): "
            )
        
        return prompt
        
    def _query_llm(self, prompt: str) -> Optional[str]:
        """Query the LLM using configured provider."""
        try:
            print("\nDebug - Starting LLM query with prompt:")
            print("=" * 50)
            print(prompt)
            print("=" * 50)
            
            # Validate configuration
            if not self.provider:
                print("Error: No LLM provider configured")
                return None
                
            provider_config = self.providers_config.get(self.provider)
            if not provider_config:
                print(f"Error: Configuration missing for provider {self.provider}")
                return None
                
            # For OpenRouter, validate API key
            if self.provider == "openrouter":
                if not provider_config.get('api_key'):
                    print("Error: OpenRouter API key not configured")
                    return None
                    
            print(f"\nProvider status:")
            print(f"- Active provider: {self.provider}")
            print(f"- Model: {provider_config.get('default_model', 'not specified')}")
            print(f"- API URL: {provider_config.get('url', 'not specified')}")
            
            # Make the API call based on provider
            if self.provider == "ollama":
                print("\nUsing Ollama API")
                return self._query_ollama(prompt, provider_config)
            elif self.provider == "openrouter":
                print("\nUsing OpenRouter API")
                response = self._query_openrouter(prompt, provider_config)
                print("\nDebug - OpenRouter Response:", response)  # Debug log
                return response
            else:
                print(f"\nError: Unknown provider {self.provider}")
                return None
                
        except Exception as e:
            print(f"\nError in _query_llm:")
            print(f"- Exception type: {type(e).__name__}")
            print(f"- Error message: {str(e)}")
            if isinstance(e, requests.exceptions.RequestException):
                print(f"- API request failed: {str(e)}")
            return None

    def _get_model_config(self, model_name: str) -> dict:
        """Get model-specific configuration based on model name."""
        # Get default config from settings
        base_config = self.model_configs.get("default", {
            "temperature": 0.7,
            "max_tokens": 100,
            "top_p": 0.9
        })
        
        # Check for model-specific configs
        if "gemini" in model_name.lower():
            return self.model_configs.get("gemini", base_config)
        elif "gpt" in model_name.lower():
            return self.model_configs.get("gpt", base_config)
        
        return base_config

    def _query_ollama(self, prompt: str, config: dict) -> Optional[str]:
        """Query the Ollama API."""
        try:
            # Construct the API endpoint
            base_url = config.get('url', 'http://localhost:11434')
            api_endpoint = f"{base_url}/api/generate"
            
            # Get the model name
            model = config.get('default_model', 'gemma:2b')
            
            # Prepare the request
            headers = {'Content-Type': 'application/json'}
            data = {
                'model': model,
                'prompt': prompt,
                'stream': False
            }
            
            print(f"Querying Ollama with model: {model}")
            print(f"Using endpoint: {api_endpoint}")
            
            # Make the request
            response = requests.post(api_endpoint, headers=headers, json=data)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            if 'response' in result:
                return result['response']
            else:
                print(f"Unexpected Ollama response format: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error querying Ollama: {str(e)}")
            if "Connection refused" in str(e):
                print("Make sure Ollama is running locally (http://localhost:11434)")
            return None
        except Exception as e:
            print(f"Unexpected error querying Ollama: {str(e)}")
            return None

    def _query_openrouter(self, prompt: str, config: dict) -> Optional[str]:
        """Query using OpenRouter API with enhanced error handling and model-specific configs."""
        try:
            if not config.get("configured", True):  # Default to True for backward compatibility
                print(f"OpenRouter is not configured")
                return None
                
            if not config.get("api_key"):
                print("OpenRouter API key is missing")
                return None
                
            url = config.get("url", "https://openrouter.ai/api/v1/chat/completions")
            model = config.get("default_model", "google/gemini-flash-1.5-8b")
            
            print(f"\nMaking OpenRouter API request:")
            print(f"- Model: {model}")
            print(f"- URL: {url}")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['api_key']}",
                "HTTP-Referer": "http://localhost:11434",
                "X-Title": "Folder Organizer"
            }
            
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"OpenRouter API error (Status {response.status_code})"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f": {error_data['error']}"
                except:
                    error_msg += f": {response.text}"
                print(error_msg)
                return None
                
            result = response.json()
            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"]["content"]
                return content.strip()
            else:
                print(f"Unexpected OpenRouter response format: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"OpenRouter API request failed: {str(e)}")
            if isinstance(e, requests.exceptions.Timeout):
                print("Request timed out after 30 seconds")
            elif isinstance(e, requests.exceptions.ConnectionError):
                print("Failed to connect to OpenRouter API")
            return None
        except Exception as e:
            print(f"Unexpected error with OpenRouter API: {str(e)}")
            return None
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract suggested name and confidence."""
        try:
            # Try to parse as JSON first
            data = json.loads(response)
            return {
                'name': data.get('name', ''),
                'confidence': float(data.get('confidence', 0.0)),
                'reasoning': data.get('reasoning', '')
            }
        except:
            # Fallback: try to extract just the filename if JSON parsing fails
            lines = response.split('\n')
            for line in lines:
                if line.strip() and not line.startswith(('#', '//', '-')):
                    return {
                        'name': line.strip()[:50],
                        'confidence': 0.5,
                        'reasoning': 'Extracted from plain text response'
                    }

    def test_llm_provider(self, provider: str = None) -> Dict[str, Any]:
        """Test the LLM provider configuration.
        
        Args:
            provider: Optional provider name. If None, uses the default provider.
            
        Returns:
            Dict containing test results with status and message.
        """
        if not provider:
            provider = self.provider
            
        provider_config = self.providers_config.get(provider)
        if not provider_config:
            return {
                'success': False,
                'message': f'Provider {provider} not configured'
            }
            
        test_prompt = "This is a test prompt. Please respond with 'ok' to verify the connection."
        
        try:
            if provider == "ollama":
                response = requests.post(
                    provider_config["url"],
                    json={
                        'model': provider_config.get("default_model", "mistral"),
                        'prompt': test_prompt,
                        'stream': False
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'message': 'Successfully connected to Ollama API'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Ollama API error: Status {response.status_code}'
                    }
                    
            elif provider == "openrouter":
                if not provider_config.get('api_key'):
                    return {
                        'success': False,
                        'message': 'OpenRouter API key not configured'
                    }
                    
                headers = {
                    "Authorization": f"Bearer {provider_config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                if provider_config.get("site_url"):
                    headers["HTTP-Referer"] = provider_config["site_url"]
                if provider_config.get("app_name"):
                    headers["X-Title"] = provider_config["app_name"]
                    
                response = requests.post(
                    provider_config["url"],
                    headers=headers,
                    json={
                        "model": provider_config.get("default_model", "openai/gpt-3.5-turbo"),
                        "messages": [
                            {
                                "role": "user",
                                "content": test_prompt
                            }
                        ]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'message': 'Successfully connected to OpenRouter API'
                    }
                else:
                    error_msg = 'OpenRouter API error'
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            error_msg += f": {error_data['error']}"
                    except:
                        error_msg += f": Status {response.status_code}"
                    return {
                        'success': False,
                        'message': error_msg
                    }
            else:
                return {
                    'success': False,
                    'message': f'Unsupported provider: {provider}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': f'{provider} API request timed out after 10 seconds'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': f'Failed to connect to {provider} API. Check if the service is running and accessible.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error testing {provider}: {str(e)}'
            }
