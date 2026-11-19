# /schemas/internal_knowledge/source_uri.py
from typing import Optional
from pydantic import Field, model_validator
from schemas.base import ImmutableSchema, DocumentedEnum

class SourceScheme(DocumentedEnum):
    """支持的采集源协议类型枚举"""
    REPO = ("repo", "代码仓库", "远端或本地 Git 代码仓库切片")
    FILE = ("file", "本地文件", "本地文件系统路径")
    HTTP = ("http", "网页文档", "HTTP 网页或在线接口")
    HTTPS = ("https", "安全网页", "HTTPS 网页、Wiki 或在线文档")
    S3 = ("s3", "对象存储", "S3/OSS 等对象存储桶文件")
    DB = ("db", "数据库", "关系型数据库或 CMDB 结构化记录")
    CHAT = ("chat", "对话流", "AI 助手多轮对话、IM 群聊或会议转录流")

class SourceURI(ImmutableSchema):
    """纯数据结构：解析后的采集源定位符值对象（不含解析与I/O行为）
    场景统一URI规范与字段拆解对照表:

    通用抽象结构：`<scheme>://<location>[#<anchor>]` 或版本库紧凑格式 `repo:<url>#<revision>:<subpath>[#<anchor>]`

    | 采集源场景 | `scheme` | 完整 URI 示例 | `location` | `revision` | `subpath` | `anchor` |
    | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
    | **远端 Git 仓库** | `repo` | `repo:https://xxxi.com` | `https://xxxi.com` | `xxic_9920` | `xxx/scriptFilexxc.sh` | `L42-L68` |
    | **本地文件 (绝对)** | `file` | `file:///Users/dev/project/scripts/sync.sh#L42-L68` | `/Users/dev/project/scripts/sync.sh` | `None` | `None` | `L42-L68` |
    | **本地文件 (相对)** | `file` | `file:./scripts/sync.sh#func:sync_artifacts` | `./scripts/sync.sh` | `None` | `None` | `func:sync_artifacts` |
    | **网页 / Wiki** | `https` | `https://internal.com` | `://internal.com` | `None` | `None` | `rollback-steps` |
    | **对象存储 (S3/OSS)** | `s3` | `s3://prod-docs/manuals/arch.pdf#page=12` | `prod-docs/manuals/arch.pdf` | `None` | `None` | `page=12` |
    | **数据库 / CMDB** | `db` | `db://mysql-prod/cmdb.services#id=1024` | `mysql-prod/cmdb.services` | `None` | `None` | `id=1024` |
    | **AI 助手多轮对话** | `chat` | `chat://internal-agent/sess_89a7b6c5#turn:3-5` | `internal-agent/sess_89a7b6c5` | `None` | `None` | `turn:3-5` |
    | **对话单条消息** | `chat` | `chat://internal-agent/sess_89a7b6c5#msg:msg_0042` | `internal-agent/sess_89a7b6c5` | `None` | `None` | `msg:msg_0042` |
    | **IM 群聊 / 频道** | `chat` | `chat://slack/C01234567#ts:1731995400.001200` | `slack/C01234567` | `None` | `None` | `ts:1731995400.001200` |
    | **语音 / 会议转录** | `chat` | `chat://meeting/mtg_20261119#00:14:20-00:16:05` | `meeting/mtg_20261119` | `None` | `None` | `00:14:20-00:16:05` |

    通用锚点 (`anchor`) 语义约定:

    | 锚点类型 | 书写格式 | 适用场景说明 |
    | :--- | :--- | :--- |
    | **代码行范围** | `L42` 或 `L42-L68` | 精确定位源码文件的单行或起止行区间 |
    | **代码符号名** | `func:upload_artifact` / `class:Information` | 基于 AST 符号定位函数或类定义（比行号更抗变更） |
    | **文档分页/章节** | `page=12` / `sec:overview` | PDF 页码定位或 Markdown/HTML 标题锚点 |
    | **对话交互定位** | `turn:3-5` / `msg:msg_0042` / `ts:1731995400` | 对话轮次区间、消息唯一 ID 或流式时间戳 |
    """
    scheme: SourceScheme = Field(..., description="采集源协议类型")
    location: str = Field(..., min_length=1, description="核心资源定位路径")
    revision: Optional[str] = Field(default=None, description="版本标识（仅 repo 使用）")
    subpath: Optional[str] = Field(default=None, description="仓库内相对子路径（仅 repo 使用）")
    anchor: Optional[str] = Field(default=None, description="细粒度内部定位锚点")

    @model_validator(mode="after")
    def validate_scheme_constraints(self) -> "SourceURI":
        """结构不变式校验：revision 与 subpath 仅允许在 repo 协议下使用"""
        if self.scheme != SourceScheme.REPO and (self.revision is not None or self.subpath is not None):
            raise ValueError(
                f"协议 '{self.scheme.value}' 不支持 revision 或 subpath 字段，仅 'repo' 协议可使用"
            )
        return self

    @property
    def canonical_uri(self) -> str:
        """纯只读派生属性：还原为规范化的标准 URI 字符串"""
        if self.scheme == SourceScheme.REPO:
            base = f"repo:{self.location}"
            if self.revision:
                base += f"#{self.revision}"
            if self.subpath:
                base += f":{self.subpath}"
            if self.anchor:
                base += f"#{self.anchor}"
            return base

        if self.scheme == SourceScheme.FILE and self.location.startswith("."):
            base = f"file:{self.location}"
        else:
            base = f"{self.scheme.value}://{self.location}"

        return f"{base}#{self.anchor}" if self.anchor else base
