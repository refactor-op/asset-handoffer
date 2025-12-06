"""配置管理"""

from pathlib import Path
import yaml
from typing import Any

from ..exceptions import ConfigError
from ..i18n import Messages


class Config:
    """配置管理"""
    
    def __init__(self, config_dict: dict, config_file: Path, messages: Messages = None):
        self.data = config_dict
        self.config_file = config_file
        self.messages = messages or Messages(config_dict.get('language', 'zh-CN'))
        self._resolve_paths()
        self._validate()
    
    def _resolve_paths(self):
        workspace = self.data.get('workspace', {})
        
        if isinstance(workspace, str):
            root = workspace
            inbox_name = 'inbox'
            repo_name = '.repo'
            failed_name = 'failed'
            logs_name = 'logs'
        else:
            root = workspace.get('root', './')
            inbox_name = workspace.get('inbox', 'inbox')
            repo_name = workspace.get('repo', '.repo')
            failed_name = workspace.get('failed', 'failed')
            logs_name = workspace.get('logs', 'logs')
        
        if not Path(root).is_absolute():
            root = (self.config_file.parent / root).resolve()
        else:
            root = Path(root)
        
        self.workspace_root = root
        self.inbox = root / inbox_name
        self.repo = root / repo_name
        self.failed = root / failed_name
        self.logs = root / logs_name
    
    def _validate(self):
        required = ['git.repository', 'naming.pattern']
        
        for field in required:
            if not self._get_nested(field):
                raise ConfigError(self.messages.t('config.missing_field', field=field))
        
        if 'asset_root' not in self.data:
            raise ConfigError(self.messages.t('config.missing_field', field='asset_root'))
        
        if 'path_template' not in self.data:
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
    def naming_pattern(self) -> str:
        return self.data['naming']['pattern']
    
    @property
    def naming_example(self) -> str:
        return self.data['naming'].get('example', '')
    
    @property
    def language(self) -> str:
        return self.data.get('language', 'zh-CN')
    
    def ensure_dirs(self):
        for d in [self.inbox, self.failed, self.logs]:
            d.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def load(config_file: Path) -> 'Config':
        temp_messages = Messages('zh-CN')
        
        if not config_file.exists():
            raise ConfigError(temp_messages.t('config.file_not_found', path=str(config_file)))
        
        try:
            data = yaml.safe_load(config_file.read_text(encoding='utf-8'))
        except yaml.YAMLError as e:
            raise ConfigError(temp_messages.t('config.invalid_yaml', error=str(e)))
        
        messages = Messages(data.get('language', 'zh-CN'))
        return Config(data, config_file, messages)
    
    @staticmethod
    def create(
        git_url: str,
        asset_root: str = "Assets/GameRes/",
        output_file: Path = None
    ) -> Path:
        from pathlib import Path
        
        template_path = Path(__file__).parent.parent / "templates" / "config.yaml"
        
        if not template_path.exists():
            raise ConfigError(f"配置模板不存在: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        content = template_content.replace(
            'asset_root: "Assets/GameRes/"',
            f'asset_root: "{asset_root}"'
        ).replace(
            'repository: "https://github.com/your-org/your-project.git"',
            f'repository: "{git_url}"'
        )
        
        if output_file is None:
            project_name = git_url.rstrip('/').split('/')[-1].replace('.git', '')
            output_file = Path(f"{project_name}.yaml")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_file
