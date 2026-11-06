# 飞书 CLI 与图片本地化 / Feishu CLI and local images

供用户指定飞书资料或要求保存图片时按需读取。独立整理通用操作，不携带来源工程的账号、公司、用户、任务、项目、通讯录、正文、资源标识或图片，不引入其工作流。飞书是可选工具，不增加 happlylong 的 Python 依赖。

## 中文

### 接入自己的 CLI

使用官方 [larksuite/cli](https://github.com/larksuite/cli)。已安装时先核对版本与帮助；未安装时按官方说明选择版本，记录实际版本后使用。以下参数在本机 `lark-cli 1.0.95` 的离线帮助中核对，其他版本须重新核对，不默认升级或改配置。

```bash
lark-cli --version
lark-cli docs +fetch --help
lark-cli docs +media-download --help
lark-cli im +messages-resources-download --help
```

只有用户要求接入自己的账号时才配置或登录。用户可在本机交互执行 `lark-cli config init`；从当前帮助/官方指南核实所需 scope，再用 `lark-cli auth login --scope "$feishu_scopes"` 登录，不默认申请全部领域权限。多个 profile 时，每条命令显式指定已确认的 `--profile`。CLI 认证与浏览器登录分别检查，不能互相替代。

凭据由 CLI 的本机存储管理；不复制其他工程的应用配置、密钥、认证缓存、cookies 或浏览器资料目录，不把凭据写入命令字面量、PRD、日志或公开配置。即使调用 auth status，也只汇报是否可用，不转存身份详情。

限定用户指定资料及当前任务需要的图片，不顺带查询账户列表、用户资料、通讯录、其他任务或项目。读取/下载授权不包含上传、评论、修改或同步远端资料。

### 选对图片的下载入口

| 图片来源 | 定位信息 | 下载命令 |
|---|---|---|
| 文档内嵌图片或素材 | 文档正文中的 media token | `docs +media-download` |
| 消息图片 | 同一条消息返回的 message ID 与 file key | `im +messages-resources-download --type image` |
| 云盘上传的独立图片文件 | 该文件的 file token | `drive +download` |

以下 Bash 变量由本次已授权资料解析得到，不是实际示例账号或预填资源。`hy_image_output` 是已核验迭代 `attach/` 内的未使用文件名；从框架根执行，先创建附件目录。不指定扩展名时 CLI 可推断格式。

```bash
# 读取指定文档，保留图片定位结构。
lark-cli docs +fetch --doc "$feishu_doc_url" --detail with-ids --doc-format xml --as user

# 从正文图片节点取得 media token 后下载。
lark-cli docs +media-download --token "$feishu_media_token" --output "$hy_image_output" --as user

# 仅用于同一条已授权消息的图片。
lark-cli im +messages-resources-download --message-id "$feishu_message_id" --file-key "$feishu_file_key" --type image --output "$hy_image_output" --as user

# 独立云盘文件使用专用入口，先查 drive +download --help。
lark-cli drive +download --file-token "$feishu_file_token" --output "$hy_image_output" --as user
```

三种下载方式按来源选用，不是依次尝试的回退链。不能把网页/文档图片 key 填入消息接口。`--as user` 用于用户自己的授权；明确选择应用身份时另核实其资源权限，不靠切换身份绕过拒绝。IM 下载有输出根目录限制，从框架根调用，保存到已绑定迭代的 `attach/`。

程序调用使用参数数组而非拼接 shell；检查退出码、JSON 对象结构、业务错误和实际保存路径。不能仅因 stdout 可解析或文件存在就算成功。文件名以 CLI 实际返回为准，不预先假定一定是 PNG。原始响应可能含敏感字段，不整包写入文档。

### 正文有了，图片仍可能缺失

- 图片占位文字、预览链接或空附件列表不代表已下载图片；内嵌图可能不列为独立附件。在原文具体位置核对缺图，不能宣布完整导入。
- 下载拒绝或资源不匹配时检查来源类型、身份及 scope；不要尝试无关 key、导出凭据或扩大查询。官方预览入口也需要有效权限，缩略图只标为预览，不能当原图。
- CLI 不支持该素材或正文缺图，且浏览器对该资料已有合法访问时，可用浏览器工具打开对应页面和目标图的大图预览；明确的资源权限拒绝应先停止并解决权限，不把浏览器当绕过手段。限定正文区域，排除头像、评论图和其他图片；确认目标位置、加载状态及尺寸后，优先用页面下载功能保存。
- `blob:` 只在创建它的浏览器上下文有效，不能交给独立 HTTP 工具或当永久链接。工具支持时可在该页面上下文读取目标图字节并保存；不导出 cookies、不抓整页网络记录。无法保存原图时说明缺失，截图替代须先得到用户接受并标注截图。
- 不按全页 DOM 顺序、固定 CSS 选择器或“取前 N 张”猜正文图片。不因 image key 相同而删除原文重复位置。逐张核对对应关系；重开预览仍失败则停止自动尝试并列明缺失。

### 落到当前迭代并验证

先 `python3 happlylong.py session show` 核对绑定；未绑定先完成已有的绑定/新建门禁，再落盘到 `workspace/{project}/iterations/{id}/attach/`。不保存到公共 `shared/`、`examples/` 或业务代码库。确认父目录在框架内且无越界软链，使用自定文件名（如 `reference-01`），不信任远端文件名、不覆盖已有文件。

每张图至少核对：下载成功且非空；内容是可解码、尺寸非零的图片而非登录页/HTML/错误 JSON；实际画面与原文目标一致。用现有图片查看器打开，必要时核对签名和实际格式，不能只看 MIME 或后缀。同一图重复使用可以共用本地文件，但保留全部引用位置。

在 PRD 或 `attach/` 的说明中只记原文位置/图序号、本地相对文件名、验证结果、原图/预览/截图标记和缺失项。PRD 用 Markdown 图片语法引用实际的相对路径，例如 `attach/reference-01.png`，不用临时 URL 或 blob。确需保留来源 URL 时仅存本机并去掉授权参数，不附账号、成员或任务列表。下载不代表 PRD 或测试阶段完成。

认证/权限错误停止自动重试；暂时网络或限流失败仅对同一授权资源做少量退避重试。部分成功如实报告已保存和缺失项。

## English

### Connect the user's own CLI

Use the official CLI linked below and inspect its version and help first. The flags above were checked offline against `lark-cli 1.0.95`; recheck other versions. Feishu is optional and adds no Python dependency. Configure or log in only when requested: the user may run `lark-cli config init` interactively, then use `auth login --scope` with scopes verified for the operation. Do not default to all domains. Explicitly select a confirmed profile when several exist. Browser and CLI authorization are separate.

Keep credentials in the CLI's local store. Never import another project's app configuration, secrets, authentication cache, cookies or browser profile; do not publish identity details or raw responses. Read only user-identified sources and necessary images, without enumerating accounts, contacts, unrelated tasks or projects. Downloads do not authorize remote writes or synchronization. This guide contains methods only, without source-project data.

### Choose a downloader by resource origin

The Bash block above uses variables from the current authorized source rather than preset identifiers. Choose one matching download command:

- Document media: fetch the specified document with `docs +fetch --detail with-ids --doc-format xml`, obtain its image media token, then use `docs +media-download`.
- Message image: use `im +messages-resources-download` with the matching message ID and file key from that same message and `--type image`.
- Standalone uploaded file: use `drive +download` with its file token.

These are alternatives, not endpoint retries. Do not use a document/web image key as a message key or switch identity to evade denial. `--as user` uses the user's authorization; an explicitly selected app identity needs verified access. For IM's output-root restrictions, run from the framework root and save inside the bound iteration's `attach/`.

When wrapping the CLI, use an argument array and check return code, expected JSON structure, business errors and actual saved path. Parsing JSON or finding a file is insufficient. Use the real returned filename and format, and do not copy raw responses into documentation.

### Recover missing images and verify local files

Extracted text, image markers, preview URLs and empty attachment lists do not establish that inline images were downloaded. Verify missing images at their positions in the original. On permission errors, check resource type, identity and scope; never try unrelated keys or export credentials. Label previews as previews.

If the CLI does not support the media or omits inline images, and the browser already has legitimate access, open the exact source and full-size preview there. Stop and resolve explicit resource permission denials rather than treating the browser as a bypass. Select the relevant body area, excluding comments and avatars. Confirm position, loading and dimensions before using the page's download function. A `blob:` URL must be read in its creating browser context using supported tools; it is not a reusable HTTP URL. Never export cookies or broad network captures. Use a screenshot substitute only after user acceptance and label it. Avoid whole-page ordering, fixed-selector assumptions and removing repeated occurrences by image key.

Before local writes, check `python3 happlylong.py session show` and resolve an unbound session through the existing bind/create gate. Save only to `workspace/{project}/iterations/{id}/attach/`, with safe local names, validated non-linked parents and no overwrites. Do not place real downloads in public framework directories or code repositories.

Verify a nonempty file, a decodable image with nonzero dimensions rather than HTML/JSON, and a visual match to the source. Preserve reference positions even when reusing a local file. Record only source position, relative filename, verification result, original/preview/screenshot status and missing items in local iteration notes. Reference actual images relatively from the PRD. Remove authorization parameters from any locally retained source URL. Downloading images does not complete PRD or testing stages.

Stop on authentication/permission errors. Retry transient network/rate-limit failures a few times with backoff for the same resource, and report partial results explicitly.

## 官方参考 / Official references

- [CLI 安装与配置 / Installation and configuration](https://github.com/larksuite/cli)
- [文档读取 / Document fetch](https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-fetch.md)
- [文档媒体下载 / Document media download](https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-media-download.md)
- [消息资源下载 / Message resource download](https://github.com/larksuite/cli/blob/main/skills/lark-im/references/lark-im-messages-resources-download.md)

## 修订历史 / Revision history

| 日期 / Date | 变更 / Change |
|---|---|
| 2026-11-06 | 独立整理接入、图片下载及本地验证经验；不含账号或业务数据。 / Independently authored access, image download and local validation guidance without account or business data. |
