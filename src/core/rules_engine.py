from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import re
import magic
from datetime import datetime
import logging

@dataclass
class Rule:
    """Represents a file organization rule"""
    name: str
    description: str
    condition: Callable[[Path], bool]
    action: Callable[[Path, Path], None]
    target_dir: Path
    enabled: bool = True

class RulesEngine:
    """Engine for managing and executing file organization rules"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.rules: List[Rule] = []
        self.logger = logging.getLogger(__name__)
        
        # Load default rules
        self._load_default_rules()
        
        # Load custom rules from config
        if config_manager:
            self._load_custom_rules()
    
    def _load_default_rules(self):
        """Load default organization rules"""
        # Images rule
        self.add_rule(
            name="Images",
            description="Organize image files by year/month",
            condition=lambda p: magic.from_file(str(p), mime=True).startswith('image/'),
            action=self._organize_by_date,
            target_dir=Path("Images")
        )
        
        # Documents rule
        self.add_rule(
            name="Documents",
            description="Organize documents by type",
            condition=lambda p: any(p.suffix.lower() in ['.pdf', '.doc', '.docx', '.txt']),
            action=self._organize_by_type,
            target_dir=Path("Documents")
        )
        
        # Code files rule
        self.add_rule(
            name="Code",
            description="Organize code files by language",
            condition=lambda p: any(p.suffix.lower() in ['.py', '.js', '.java', '.cpp']),
            action=self._organize_by_language,
            target_dir=Path("Code")
        )
    
    def _load_custom_rules(self):
        """Load custom rules from config"""
        if not self.config_manager:
            return
            
        custom_rules = self.config_manager.get("rules", {}).get("custom_rules", [])
        for rule_config in custom_rules:
            try:
                # Create condition function from pattern
                pattern = rule_config.get("pattern", "")
                condition = self._create_condition(pattern)
                
                # Create action function
                action_type = rule_config.get("action", "by_type")
                action = self._get_action_function(action_type)
                
                # Add rule
                self.add_rule(
                    name=rule_config.get("name", "Custom Rule"),
                    description=rule_config.get("description", ""),
                    condition=condition,
                    action=action,
                    target_dir=Path(rule_config.get("target_dir", "Other")),
                    enabled=rule_config.get("enabled", True)
                )
                
            except Exception as e:
                self.logger.error(f"Error loading custom rule: {e}")
    
    def add_rule(self, name: str, description: str, condition: Callable,
                action: Callable, target_dir: Path, enabled: bool = True):
        """Add a new organization rule"""
        rule = Rule(name, description, condition, action, target_dir, enabled)
        self.rules.append(rule)
    
    def process_file(self, file_path: Path, base_dir: Path) -> Optional[Path]:
        """Process a file through all enabled rules"""
        try:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                    
                if rule.condition(file_path):
                    target_path = base_dir / rule.target_dir
                    rule.action(file_path, target_path)
                    return target_path
                    
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return None
            
        return None
    
    def _create_condition(self, pattern: str) -> Callable[[Path], bool]:
        """Create a condition function from a pattern"""
        if pattern.startswith("mime:"):
            mime_type = pattern[5:]
            return lambda p: magic.from_file(str(p), mime=True).startswith(mime_type)
        elif pattern.startswith("ext:"):
            extensions = pattern[4:].split(",")
            return lambda p: p.suffix.lower() in extensions
        else:
            regex = re.compile(pattern)
            return lambda p: bool(regex.match(p.name))
    
    def _get_action_function(self, action_type: str) -> Callable[[Path, Path], None]:
        """Get an action function by type"""
        actions = {
            "by_type": self._organize_by_type,
            "by_date": self._organize_by_date,
            "by_language": self._organize_by_language
        }
        return actions.get(action_type, self._organize_by_type)
    
    def _organize_by_date(self, file_path: Path, target_dir: Path):
        """Organize file by creation date"""
        timestamp = file_path.stat().st_mtime
        date = datetime.fromtimestamp(timestamp)
        final_dir = target_dir / str(date.year) / date.strftime("%m-%B")
        final_dir.mkdir(parents=True, exist_ok=True)
        
        new_path = final_dir / self._get_unique_name(file_path.name, final_dir)
        file_path.rename(new_path)
    
    def _organize_by_type(self, file_path: Path, target_dir: Path):
        """Organize file by type"""
        file_type = file_path.suffix[1:].upper() if file_path.suffix else "Other"
        final_dir = target_dir / file_type
        final_dir.mkdir(parents=True, exist_ok=True)
        
        new_path = final_dir / self._get_unique_name(file_path.name, final_dir)
        file_path.rename(new_path)
    
    def _organize_by_language(self, file_path: Path, target_dir: Path):
        """Organize code files by programming language"""
        extension_to_language = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.go': 'Go'
        }
        
        language = extension_to_language.get(
            file_path.suffix.lower(),
            file_path.suffix[1:].upper() if file_path.suffix else "Other"
        )
        
        final_dir = target_dir / language
        final_dir.mkdir(parents=True, exist_ok=True)
        
        new_path = final_dir / self._get_unique_name(file_path.name, final_dir)
        file_path.rename(new_path)
    
    def _get_unique_name(self, filename: str, directory: Path) -> str:
        """Generate a unique filename in the target directory"""
        if not (directory / filename).exists():
            return filename
            
        name, ext = Path(filename).stem, Path(filename).suffix
        counter = 1
        
        while (directory / f"{name}_{counter}{ext}").exists():
            counter += 1
            
        return f"{name}_{counter}{ext}"
    
    def get_rule_info(self) -> List[Dict[str, Any]]:
        """Get information about all rules"""
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "enabled": rule.enabled,
                "target_dir": str(rule.target_dir)
            }
            for rule in self.rules
        ]
    
    def enable_rule(self, rule_name: str, enabled: bool = True):
        """Enable or disable a rule by name"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = enabled
                break
    
    def save_rules(self):
        """Save custom rules to config"""
        if not self.config_manager:
            return
            
        custom_rules = []
        for rule in self.rules:
            custom_rules.append({
                "name": rule.name,
                "description": rule.description,
                "enabled": rule.enabled,
                "target_dir": str(rule.target_dir)
            })
            
        self.config_manager.set("rules.custom_rules", custom_rules)
        self.config_manager.save()
