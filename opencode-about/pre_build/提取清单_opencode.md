# ═══════════════════════════════════════════════════════════
#  提取清单 — opencode v1.15.10
#  Step 1 产出：纯客观摘录
#  来源：源码 (packages/opencode/src/) + package.json + README
# ═══════════════════════════════════════════════════════════

## 1. Agent 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Agent_01 | Agent.Info | Agent 配置模式，指定身份、权限、模型绑定和行为参数 | name, description, mode(subagent/primary/all), native, hidden, topP, temperature, color, permission(Ruleset), model, variant, prompt, options, steps | 被 Agent.Service 管理，被 Session/LLM/ToolRegistry 消费 | agent.ts:29-50 |
| C_Agent_02 | Agent.Service | Agent 管理服务契约：获取、列表、默认、生成 | get(name)→Info, list()→Info[], defaultInfo()→Info, defaultAgent()→string, generate({description})→GeneratedAgent | 依赖 Config/Auth/Plugin/Skill/Provider | agent.ts:58-78 |
| C_Agent_03 | build (主Agent) | 默认全权限开发者 Agent，mode="primary"，所有工具允许 | name:"build", mode:"primary", native:true | 默认 Agent | agent.ts:130-143 |
| C_Agent_04 | plan (只读Agent) | 分析探索模式，编辑工具默认拒绝，仅允许 .opencode/plans/ 写入 | mode:"primary", edit→deny 除 .opencode/plans/ | 非默认，通过 Tab 切换 | agent.ts:145-166 |
| C_Agent_05 | general (子Agent) | 通用目的子 Agent 用于并行多步任务 | mode:"subagent" | 被 task 工具内部调用 | agent.ts:168-180 |
| C_Agent_06 | explore (探索子Agent) | 代码库探索子 Agent，仅只读工具 | mode:"subagent", prompt=PROMPT_EXPLORE | 快速文件搜索、代码检索 | agent.ts:182-203 |
| C_Agent_07 | Subagent | 非主 Agent，可被 Task 工具调度用于并行或专业工作 | mode:"subagent" | 由 Permission.evaluate("task", name, permission) 过滤 | agent.ts, registry.ts:307 |
| C_Agent_08 | GeneratedAgent | LLM 生成的动态 Agent 配置 | identifier, whenToUse, systemPrompt | 由 Agent.generate() 产出 | agent.ts:52-56 |

## 2. Tool 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Tool_01 | Tool.Def | 完全解析、可执行的工具规格 | id, description, parameters(Schema.Decoder), jsonSchema, execute(fn), formatValidationError | 由 Tool.Info.init() 产出，被 ToolRegistry 聚合 | tool.ts:53-63 |
| C_Tool_02 | Tool.Info | 延迟初始化的工具声明，持有一个 init 函数产生 DefWithoutID | id, init(() → Effect<DefWithoutID>) | 由 Tool.define() 创建 | tool.ts:69-75 |
| C_Tool_03 | Tool.Context | 每次工具调用的执行上下文 | sessionID, messageID, agent, abort(AbortSignal), callID, extra, messages, metadata(), ask()→Permission.Request | 传入 Tool.Def.execute | tool.ts:34-44 |
| C_Tool_04 | ExecuteResult | 工具执行结果 | title, metadata(M), output(string), attachments(FilePart[],可选) | Tool.Def.execute 返回值 | tool.ts:46-51 |
| C_Tool_05 | InvalidArgumentsError | 类型化错误：LLM 调用工具时参数校验失败 | tool, detail | 被上游捕获为可匹配错误 | tool.ts:22-32 |
| C_Tool_06 | ToolRegistry | 中央注册表：聚合内置/自定义/插件工具，发现外部工具文件，解析模型适配工具列表 | ids(), all(), named(), tools(model) | 依赖 Config/Plugin/Agent/Skill/Session/Provider | registry.ts:82-110 |
| C_Tool_07 | read (工具) | 读取文件或列出目录，支持文本/图片/PDF/二进制检测 | filePath, offset, limit | LSP.touchFile, Reference, assertExternalDirectoryEffect | read.ts |
| C_Tool_08 | edit (工具) | 精确字符串替换，diff 预览，原子文件锁 | filePath, oldString, newString, replaceAll | BOM 感知，文件锁，LSP/Formatter/Bus | edit.ts |
| C_Tool_09 | write (工具) | 创建或覆盖文件 | content, filePath(必须绝对路径) | 与 edit 同构 | write.ts |
| C_Tool_10 | shell (工具) | 执行 shell 命令，tree-sitter 解析命令用于权限作用域 | command, cwd, timeout | ShellID, Shell.Service, ChildProcessSpawner | shell.ts |
| C_Tool_11 | task (工具) | 启动子 Agent 同步/后台执行 | description, prompt, subagent_type, task_id, background | Session, BackgroundJob, Bus | task.ts |
| C_Tool_12 | grep (工具) | 基于 ripgrep 的正则内容搜索 | pattern, path, include | Ripgrep.Service | grep.ts |
| C_Tool_13 | glob (工具) | 基于 ripgrep 的文件模式匹配 | pattern, path | Ripgrep.Service.files() | glob.ts |
| C_Tool_14 | webfetch (工具) | 获取转换网页内容 | url, format(text/markdown/html), timeout | HttpClient, TurndownService | webfetch.ts |
| C_Tool_15 | question (工具) | 交互式用户提问 | questions(Question.Prompt[]) | Question.Service.ask() | question.ts |
| C_Tool_16 | todowrite (工具) | 更新会话任务列表 | todos(content,status,priority)[] | Todo.Service.update() | todo.ts |
| C_Tool_17 | skill (工具) | 加载领域特定技能指令 | name | Skill.Service | skill tool |
| C_Tool_18 | Truncate.Service | 输出尺寸管理：超大输出写入磁盘，返回截断预览 | cleanup(), write(text)→path, output(text)→Result, limits() | tool.ts wrap 逻辑调用 | truncate.ts |

## 3. Session 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Session_01 | Session.Info | 会话持久化数据模式 | id(SessionID), slug, projectID, directory, parentID, title, agent, model, version, summary, cost, tokens, share, time, permission, revert | 对应 SessionTable 行 | session.ts:208-228 |
| C_Session_02 | Session.Service | 会话 CRUD + 流管理：创建、更新、移除、压缩、回退、提示、子会话 | create, update, remove, compact, revert, prompt, children | 依赖 Database/Bus/Snapshot/Storage | session.ts |
| C_Session_03 | Session.Tokens | Token 用量计数器 | input, output, reasoning, cache:{read,write} | session.ts:168-176 |
| C_Session_04 | Session.Summary | 会话变更摘要：增删行数、文件数 | additions, deletions, files, diffs | session.ts:161-166 |
| C_Session_05 | Session.Model | 会话模型绑定 | id(ModelID), providerID(ProviderID), variant | session.ts:202-206 |
| C_Session_06 | SessionID | 带品牌标记的会话标识符 | 品牌字符串，主键 | schema.ts:7-8 |
| C_Session_07 | MessageID | 带品牌标记的消息标识符 | 前缀"msg", 品牌字符串 | schema.ts:10-17 |
| C_Session_08 | PartID | 带品牌标记的消息部分标识符 | 前缀"prt", 品牌字符串 | schema.ts:19-25 |
| C_Session_09 | MessageV2.Part (联合类型) | 所有消息部分类型的联合 | TextPart, ReasoningPart, FilePart, SnapshotPart, PatchPart, AgentPart, CompactionPart, SubtaskPart, ToolPart | 存储在 PartTable，序列为 JSON | message-v2.ts |
| C_Session_10 | MessageV2.TextPart | 文本内容部分，主要载体 | text, synthetic(boolean), ignored(boolean), time, metadata | message-v2.ts:97-111 |
| C_Session_11 | MessageV2.ReasoningPart | LLM 推理输出部分 | text, metadata, time | message-v2.ts:113-123 |
| C_Session_12 | MessageV2.FilePart | 文件附件部分 | mime, filename, url, source(FilePartSource) | 被 ExecuteResult.attachments 引用 | message-v2.ts:160-168 |
| C_Session_13 | MessageV2.SubtaskPart | 子任务调度部分 | prompt, description, agent, model | message-v2.ts:193-200+ |
| C_Session_14 | LLM.Service | LLM 流编排：管理提供者解析、工具绑定、认证、权限检查 | stream(StreamInput)→Stream<LLMEvent> | 依赖 Auth/Config/Provider/Plugin/Permission | llm.ts:56-57 |
| C_Session_15 | MessageV2.OutputFormat | LLM 输出格式控制 | OutputFormatText, OutputFormatJsonSchema | 传给 LLM 流 | message-v2.ts:60-74 |
| C_Session_16 | Compaction | 上下文窗口管理：自动摘要/压缩消息历史 | auto, overflow, tail_start_id | 对应 CompactionPart | 推断 |

## 4. Provider 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Provider_01 | Provider.Service | AI 模型提供者管理：加载 SDK、解析模型、认证、语言模型实例化 | getModel, getLanguage, getProvider, defaultModel, models, info | 依赖 Config/Plugin/Auth/Env | provider.ts |
| C_Provider_02 | ProviderID | 带品牌标记的 AI 模型提供者标识符 | 品牌字符串 | well-known 常量: opencode/anthropic/openai/google/... | provider/schema.ts:5-24 |
| C_Provider_03 | ModelID | 带品牌标记的 AI 模型名称标识符 | 品牌字符串 | provider/schema.ts:26-30 |
| C_Provider_04 | Provider.Model | 已解析的语言模型实例 + 元数据 | id, providerID, model(LanguageModelV3), cost, context, capabilities | Provider.Service.getModel 产出 | provider.ts |
| C_Provider_05 | 内置 SDK 提供者 | 与 opencode 捆绑的 AI SDK 包集合 | 18+ 提供者(OpenAI/Anthropic/Google/AWS Bedrock/Groq/... ) | 首次使用时懒加载 | provider.ts:99-125 |
| C_Provider_06 | SSE 超时包装 | SSE 响应读超时保护机制 | wrapSSE(res, ms, ctl) | 应用于提供者 HTTP 客户端 | provider.ts:40-86 |

## 5. Permission 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Perm_01 | Permission.Rule | 单条权限规则：permission类型 + 模式 → 动作 | permission, pattern, action(allow/deny/ask) | 聚合为 Ruleset | permission/index.ts:22-27 |
| C_Perm_02 | Permission.Action | 规则动作判别 | "allow"/"deny"/"ask" | permission/index.ts:19-20 |
| C_Perm_03 | Permission.Ruleset | 有序规则数组（后面覆盖前面） | Rule[] | 附加到 Agent.Info/Session.Info | permission/index.ts:29-30 |
| C_Perm_04 | Permission.Request | 单条权限检查请求模式 | id(PermissionID), sessionID, permission, patterns[], metadata, always[], tool | 发送给 Permission.ask | permission/index.ts:36-50 |
| C_Perm_05 | Permission.Reply | 用户对权限请求的响应 | "once"(本次)/"always"(持久化)/"reject"(拒绝) | 驱动审批持久化逻辑 | permission/index.ts:52-53 |
| C_Perm_06 | Permission.Service | 交互式工具授权管理服务 | ask(AskInput)→void, reply(ReplyInput)→void, list()→Request[] | 依赖 Bus/Database | permission/index.ts:142-143 |
| C_Perm_07 | Permission.evaluate | 纯函数：评估规则集 → 返回匹配规则 | (permission, pattern, ...rulesets)→Rule | 委托给 PermissionV2.evaluate | permission/index.ts:138-140 |
| C_Perm_08 | Permission.merge | 合并多个规则集（后覆盖前） | (..rulesets)→Rule[] | 委托给 PermissionV2.merge | permission/index.ts:302-304 |

## 6. MCP 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_MCP_01 | MCP.Service | Model Context Protocol 服务器管理：启动/标准化/生成服务器，发现工具/资源/提示，处理 OAuth | 传输层(STDIO/SSE/HTTP)、工具发现、资源列表、OAuth | 依赖 Config/Bus/EffectBridge | mcp/index.ts |
| C_MCP_02 | MCP 传输类型 | MCP 服务器通信传输层 | StreamableHTTPClientTransport, SSEClientTransport, StdioClientTransport | mcp/index.ts:4-6 |
| C_MCP_03 | MCP 状态(判别联合) | MCP 服务器连接状态 | StatusConnected/Disabled/Failed/NeedsAuth/NeedsClientRegistration | mcp/index.ts:76-100 |
| C_MCP_04 | MCP Resource | MCP 服务器暴露的模型上下文资源 | name, uri, description, mimeType, client | mcp/index.ts:42-49 |
| C_MCP_05 | MCP 工具转换 | 将 MCP SDK 工具定义转为 opencode 兼容的 AI SDK 工具 | convertMcpTool(mcpTool, client, timeout?)→Tool | mcp/index.ts:157-186 |

## 7. Plugin 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Plugin_01 | Plugin.Service | 插件生命周期管理：加载内外部插件、触发钩子 | trigger(name, input, output)→Output, list()→Hooks[], init()→void | 依赖 Bus/Config/RuntimeFlags | plugin/index.ts:58 |
| C_Plugin_02 | Plugin.Hooks | 插件注册的钩子函数集合 | tool.definition, experimental.chat.system.transform, config, event 等 | 顺序执行以确保确定性 | plugin/index.ts |
| C_Plugin_03 | Plugin.PluginInput | 每个插件初始化时传入的上下文对象 | client(OpencodeClient), project, worktree, directory, experimental_workspace.register, serverUrl | plugin/index.ts:137-152 |
| C_Plugin_04 | 内置插件 | 与 opencode 捆绑的认证提供者插件 | CodexAuth/CopilotAuth/GitlabAuth/PoeAuth/Cloudflare/Azure/DigitalOcean/Xai | RuntimeFlags.disableDefaultPlugins 可禁用 | plugin/index.ts:61-71 |
| C_Plugin_05 | Plugin Loader | 外部插件加载基础设施 | 安装 npm 包、解析入口点、处理错误 | 阶段: install/load/compatibility/entry | plugin/index.ts |

## 8. Skill 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Skill_01 | Skill.Info | 命名、描述的 Markdown 指令文件，提供领域特定指导和流程 | name, description, location(文件路径), content(Markdown全文) | 从磁盘 SKILL.md 发现，经权限过滤 | skill/index.ts:36-42 |
| C_Skill_02 | Skill.Service | 技能发现、加载和提供服务 | get/getByName, require, all, dirs, available(agent?) | 依赖 Discovery/Config/Bus | skill/index.ts:244 |
| C_Skill_03 | Skill Discovery | 多源技能扫描 | ~/.claude/skills/, ~/.agents/skills/, config dir, 自定义路径, 远程 URL | Glob.scan, AppFileSystem | skill/index.ts:173-233 |
| C_Skill_04 | 内置技能 (customize-opencode) | opencode 自配置技能 | name:"customize-opencode", location:"<built-in>" | 磁盘技能同名覆盖 | skill/index.ts:27-34 |

## 9. Config 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Config_01 | Config.Info | 完整 opencode 配置模式 (opencode.json) | shell, logLevel, server, command, skills, reference, plugin, model, small_model, default_agent, agent, provider, permission, instructions, tool_output, experimental... | 从多层 json/jsonc 加载，深度合并 | config.ts:134-200+ |
| C_Config_02 | Config.Service | 配置加载、合并、缓存服务 | get()→Info, directories(), waitForDependencies(), set(k,v) | 依赖 Auth/Env/AppFileSystem/Account | config.ts |
| C_Config_03 | 配置合并 | 多源配置融合：全局/工作区/本地，深度合并 + 指令数组拼接 | mergeConfig, mergeConfigConcatArrays | 指令用 Set 去重 | config.ts:49-61 |
| C_Config_04 | 远程配置 | URL 基础配置加载 + 变量替换 | substituteWellKnownRemoteConfig({value,dir,source,env}) | ${VAR}/${env:VAR} 展开 | config.ts:75-115 |

## 10. Storage/DB 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_DB_01 | Database.Client | 单例 SQLite 数据库连接管理器 | $client(Bun SQLite), WAL模式, Drizzle ORM | Global.Path.data 定位 | db.ts:92-140 |
| C_DB_02 | Database.transaction | 数据库事务管理，通过 LocalContext 嵌套已有事务 | behavior(deferred/immediate/exclusive) | EffectBridge.bind 桥接 Drizzle 同步包装 | db.ts:180-198 |
| C_DB_03 | SessionTable | SQLite 会话记录表 | id(SessionID PK), slug, title, agent, model, data(JSON), timestamps | session.sql.ts:24-45 |
| C_DB_04 | MessageTable | SQLite 消息记录表 | id(MessageID PK), session_id(FK→SessionTable), data(JSON), timestamps | session.sql.ts:61-73 |
| C_DB_05 | PartTable | SQLite 消息部分表 | id(PartID PK), message_id(FK→MessageTable), session_id, data(JSON) | session.sql.ts:75-91 |
| C_DB_06 | TodoTable | SQLite 任务列表表 | session_id(FK), content, status, priority, position | session.sql.ts:93-110 |
| C_DB_07 | PermissionTable | SQLite 持久化审批记录表 | session_id, permission, pattern, action | permission 系统 |

## 11. Effect 基础设施
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Effect_01 | EffectBridge.Shape | 桥接 Effect 代码到外部的 Promise 回调 | promise(effect)→Promise, fork(effect)→Fiber, run(effect)→Effect, bind(fn)→bound fn | 被 plugin tools/DB transactions/Bus subscriptions 使用 | effect/bridge.ts:7-12 |
| C_Effect_02 | InstanceState | 作用域缓存抽象：数据关联到目录/工作区，上下文变更时自动失效 | cache(ScopedCache), make/get/use/useEffect/has/invalidate | 被 Bus/Permission/Agent/ToolRegistry/Skill 等服务使用 | effect/instance-state.ts:8-13 |

## 12. Bus/Event 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_Bus_01 | Bus.Service | 内部发布/订阅事件总线 | 类型化事件定义，跨模块通信 | Permission 请求、Session 更新、Project 变更等事件 | bus/index.ts |
| C_Bus_02 | BusEvent | 类型化事件定义：名称 + Schema | BusEvent.define(name, schema) | 被权限/Session/Project/MCP 模块使用 | bus/bus-event.ts |

## 13. CLI/TUI/Server 系统
| 编号 | 概念名称 | 原文定义 | 属性/字段 | 关系 | 来源 |
|:---|:---|:---|:---|:---|:---|
| C_CLI_01 | CLI (yargs) | 命令行入口：注册全量命令 | run, serve, web, attach, agent, provider, models, mcp, github, pr, acp, session, db, plugin, export, import, generate, debug, stats, upgrade, uninstall, console | index.ts:251 |
| C_CLI_02 | Server HTTP API | Effect HttpApi REST 服务 | 路由: session/project/config/provider/mcp/permission/file/event/question/tui/sync/workspace | server/server.ts |
| C_CLI_03 | TUI | SolidJS 终端 UI 应用 | 分屏布局：输入区、消息显示、文件查看 | cli/cmd/tui/ |

## 概念总计: 65 个核心概念
## 检验: 覆盖核心模块 (Agent/Tool/Session/Provider/Permission/MCP/Plugin/Skill/Config/DB/Effect/Bus/CLI)，无遗漏
