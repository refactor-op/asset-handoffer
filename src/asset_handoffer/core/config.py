from pathlib import Path
import yaml
from typing import Any
from .exceptions import ConfigError
from .i18n import Messages


class Config:
    def __init__(self, config_dict: dict, config_file: Path, messages: Messages = None):
        self.data = config_dict
        self.config_file = config_file
        self.messages = messages or Messages(config_dict.get('language', 'zh-CN'))
        self._resolve_paths()
        self._validate()
    
    def _resolve_paths(self):
        workspace = self.data.get('workspace', './')
        
        if isinstance(workspace, dict):
            root = workspace.get('root', './')
            inbox_name = workspace.get('inbox', 'inbox')
            repo_name = workspace.get('repo', '.repo')
            failed_name = workspace.get('failed', 'failed')
        else:
            root, inbox_name, repo_name, failed_name = workspace, 'inbox', '.repo', 'failed'
        
        root = Path(root) if Path(root).is_absolute() else (self.config_file.parent / root).resolve()
        
        self.workspace_root = root
        self.inbox = root / inbox_name
        self.repo = root / repo_name
        self.failed = root / failed_name
    
    def _validate(self):
        has_rules = self._get_nested('naming.rules')
        has_pattern = self._get_nested('naming.pattern')
        
        if not has_rules and not has_pattern:
            raise ConfigError(self.messages.t('config.missing_field', field='naming.rules 或 naming.pattern'))
        
        if not self._get_nested('git.repository'):
            raise ConfigError(self.messages.t('config.missing_field', field='git.repository'))
        
        if 'asset_root' not in self.data:
            raise ConfigError(self.messages.t('config.missing_field', field='asset_root'))
        
        if not has_rules and 'path_template' not in self.data:
            raise ConfigError(self.messages.t('config.missing_field', field='path_template'))
    
    def _get_nested(self, key_path: str) -> Any:
        keys = key_path.split('.')
        value = self.data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    @property
    def git_url(self) -> str:
        return self.data['git']['repository']
    
    @property
    def git_branch(self) -> str:
        return self.data.get('git', {}).get('branch', 'main')
    
    @property
    def git_token(self) -> str:
        return self.data.get('git', {}).get('token', '')
    
    @property
    def git_commit_template(self) -> str:
        return self.data.get('git', {}).get('commit_message', 'Update: {name}')
    
    @property
    def git_user_name(self) -> str:
        return self.data.get('git', {}).get('user', {}).get('name', 'Asset Handoffer')
    
    @property
    def git_user_email(self) -> str:
        return self.data.get('git', {}).get('user', {}).get('email', 'asset-handoffer@local')
    
    @property
    def asset_root(self) -> str:
        return self.data.get('asset_root', '')
    
    @property
    def path_template(self) -> str:
        return self.data.get('path_template', '')
    
    @property
    def naming_rules(self) -> list[dict]:
        rules = self._get_nested('naming.rules')
        if rules:
            return rules
        pattern = self._get_nested('naming.pattern')
        if pattern:
            return [{
                'pattern': pattern,
                'path_template': self.path_template,
                'example': self._get_nested('naming.example') or ''
            }]
        return []
    
    @property
    def naming_examples(self) -> list[str]:
        return [r.get('example', '') for r in self.naming_rules if r.get('example')]
    
    @property
    def language(self) -> str:
        return self.data.get('language', 'zh-CN')
    
    def ensure_dirs(self):
        for d in [self.inbox, self.failed]:
            d.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def load(config_file: Path) -> 'Config':
        temp_messages = Messages()
        
        if not config_file.exists():
            raise ConfigError(temp_messages.t('config.file_not_found', path=str(config_file)))
        
        try:
            data = yaml.safe_load(config_file.read_text(encoding='utf-8'))
        except yaml.YAMLError as e:
            raise ConfigError(temp_messages.t('config.invalid_yaml', error=str(e)))
        
        return Config(data, config_file, Messages(data.get('language', 'zh-CN')))
    
    @staticmethod
    def create(git_url: str, asset_root: str = "Assets/GameRes/", output_file: Path = None) -> Path:
        template_path = Path(__file__).parent.parent / "templates" / "config.yaml"
        
        if not template_path.exists():
            raise ConfigError(f"配置模板不存在: {template_path}")
        
        content = template_path.read_text(encoding='utf-8').replace(
            'asset_root: "Assets/GameRes/"', f'asset_root: "{asset_root}"'
        ).replace(
            'repository: "https://your-git-host.com/your-org/your-project.git"', f'repository: "{git_url}"'
        )
        
        if output_file is None:
            project_name = git_url.rstrip('/').split('/')[-1].replace('.git', '')
            output_file = Path(f"{project_name}.yaml")
        
        output_file.write_text(content, encoding='utf-8')
        return output_file
