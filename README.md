# Asset Handoffer

**美术资产交接自动化工具** - 让美术零门槛提交资产到远程仓库

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.9.11-green.svg)](https://github.com/HeBtcd/asset-handoffer)

## 为什么需要这个工具？

### 传统方式
```
美术创作完资产后：
1. 需要学习Git命令
2. 需要理解Unity项目结构
3. 需要手动找到正确的目录
4. 需要记住复杂的提交流程
5. 遇到冲突不知道如何处理

结果：美术求助程序员，程序员中断工作帮忙
```

### 使用本工具后
```
美术创作完资产后：
1. 按规范命名文件
2. 拖到inbox文件夹
3. 运行一个命令

完成！文件自动到正确位置并提交到远程仓库
```

## 核心理念

**美术零决策，程序承担风险。**

### 美术视角
- 不需要学习Git
- 不需要安装Unity
- 不需要理解项目结构
- 不需要处理任何冲突
- 只需：命名→拖放→一个命令

### 程序员视角
- 一次配置，全员受益
- 本地Git仓库，完整版本控制
- 所有风险由程序员处理（pull后解决冲突）
- 美术文件自动整理到正确位置

## 工作原理

```
美术工作区/
├── config.yaml          # 配置文件（程序员提供）
├── inbox/               # 📥 美术看得到：拖文件进来
│   └── Character_Hero.fbx
│
└── .repo/               # 🔒 美术看不到：隐藏的Git仓库
    ├── .git/
    ├── Assets/
    │   └── GameRes/
    │       └── Character/
    │           └── Hero/
    │               └── Character_Hero.fbx  ← 自动放这里
    └── ProjectSettings/
```

**工作流程**：
1. 文件放入inbox
2. 运行process命令
3. 工具自动：
   - 解析文件名（根据配置的正则表达式）
   - 移动到.repo对应位置
   - git add + commit + push
4. 完成！

**关键**：
- 美术只看到inbox
- 本地.repo是完整的Unity项目Git仓库
- 美术无感知Git的存在

## 快速开始

### 程序员：项目初始化（5分钟）

#### 1. 安装工具
```bash
pip install asset-handoffer
```

#### 2. 生成配置文件
```bash
asset-handoffer init

# 交互式输入：
远程仓库URL: https://github.com/team/mygame.git
Unity资产根路径: Assets/GameRes/

# 生成：mygame.yaml
```

#### 3. 编辑配置（可选）
根据项目需求自定义命名规则和路径模板。

#### 4. 分发给美术
将生成的 `config.yaml` 发给美术人员。

### 美术：设置和使用（3分钟）

#### 1. 安装工具
```bash
pip install asset-handoffer
```

#### 2. 首次设置
```bash
asset-handoffer setup config.yaml
```

#### 3. 日常使用
```bash
# 1. 把文件拖到 inbox/ 目录
# 2. 运行命令
asset-handoffer process config.yaml
```

完成！

## 命令参考

### `init` - 生成配置文件（程序员）
```bash
asset-handoffer init [OPTIONS]

# 选项：
#   --output, -o FILE    输出文件路径

# 示例：
asset-handoffer init -o project-a.yaml
```

### `setup` - 设置工作区（美术）
```bash
asset-handoffer setup CONFIG_FILE

# 首次使用时运行
# 会：创建工作区、克隆Git仓库

# 示例：
asset-handoffer setup mygame.yaml
```

### `process` - 处理文件（美术）
```bash
asset-handoffer process CONFIG_FILE [OPTIONS]

# 选项：
#   --file, -f FILE    指定文件（可多次）

# 示例：
asset-handoffer process config.yaml              # 处理全部inbox
asset-handoffer process config.yaml -f a.fbx     # 只处理a.fbx
asset-handoffer process config.yaml -f a.fbx -f b.png  # 处理多个
```

### `delete` - 删除文件
```bash
asset-handoffer delete PATTERN CONFIG_FILE

# 删除本地仓库中的文件并推送

# 示例：
asset-handoffer delete "Hero*.fbx" config.yaml
asset-handoffer delete "OldAssets/*" config.yaml
```

### `status` - 查看状态
```bash
asset-handoffer status CONFIG_FILE

# 显示inbox中待处理的文件

# 示例：
asset-handoffer status config.yaml
```

## 配置文件

### 极简配置示例
```yaml
workspace: "./"

git:
  repository: "https://github.com/team/game.git"
  branch: "main"
  commit_message: "Update {type}: {name}"

asset_root: "Assets/GameRes/"
path_template: "{type}/{name}/"

naming:
  pattern: "^(?P<type>[^_]+)_(?P<name>[^_]+)\\.(?P<ext>\\w+)$"
  example: "Character_Hero.fbx"

language: "zh-CN"
```

### 完整配置示例
```yaml
# 工作区（可自定义子目录）
workspace:
  root: "./"
  inbox: "inbox"
  repo: ".repo"
  failed: "failed"
  logs: "logs"

# Git配置
git:
  repository: "https://github.com/team/game.git"
  branch: "main"
  commit_message: "Update {type}: {name}"

# 资产根路径
asset_root: "Assets/GameRes/"

# 路径模板（使用命名规则中的字段）
path_template: "{type}/{name}/"

# 文件命名规则（正则表达式，完全自定义）
naming:
  pattern: "^(?P<type>[^_]+)_(?P<name>[^_]+)\\.(?P<ext>\\w+)$"
  example: "Character_Hero.fbx"

# 语言
language: "zh-CN"
```

### 自定义命名规则示例

#### 按日期和艺术家组织
```yaml
naming:
  pattern: "^(?P<date>\\d{8})_(?P<artist>\\w+)_(?P<asset>.+)\\.(?P<ext>\\w+)$"
  example: "20250106_John_TreeModel.fbx"

path_template: "{date}/{artist}/{asset}/"

git:
  commit_message: "[{date}] {artist}: Add {asset}"
```

#### 按版本号组织
```yaml
naming:
  pattern: "^(?P<name>[^_]+)_v(?P<version>\\d+)\\.(?P<ext>\\w+)$"
  example: "HeroModel_v2.fbx"

path_template: "Assets/{name}/v{version}/"
```

### 配置说明

#### `workspace`
工作区配置。可以是字符串（简写）或字典（完整配置）。

#### `asset_root`
Unity资产根路径，通常是 `Assets/GameRes/`。

#### `path_template`
路径生成模板。可以使用命名规则中定义的任意命名组。

#### `naming.pattern`
正则表达式，定义文件命名规则。**必须包含 `ext` 或 `extension` 命名组**。其他命名组完全自定义。

#### `git.commit_message`
提交消息模板。可以使用命名规则中定义的任意命名组。

## 常见问题

### Q: 美术需要安装Unity吗？
**A**: 不需要。美术电脑上只需要Python和这个工具。

### Q: 美术需要学Git吗？
**A**: 不需要。工具会自动处理所有Git操作。

### Q: 文件冲突怎么办？
**A**: 自动覆盖。程序员pull后看到冲突再处理。美术不需要关心。

### Q: 支持大文件吗？
**A**: 支持。使用真实的Git，可以配合Git LFS处理大文件。

### Q: 认证失败怎么办？
**A**: 请确保电脑上已配置 Git 凭据（SSH Key 或 Git Credential Manager）。可以在命令行尝试手动 git clone 仓库来验证。

### Q: 如何撤销美术的提交？
**A**: 程序员使用Git回滚，或使用`asset-handoffer delete`命令。

### Q: 命名规则可以自定义吗？
**A**: 完全可以！0.9.11版本支持完全自定义的命名规则，不再限制字段名。

## 贡献

欢迎 Issue & PR!