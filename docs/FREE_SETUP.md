# 免绑卡方案（历史备选说明）

**当前状态：Azure Japan East 学生虚拟机已创建，Docker 29.1.3 和 Compose 2.40.3 已安装。应用尚未部署。下文是已撤回的本地托管方案，不代表当前部署状态。实际配置、费用与待办以 [AZURE_STATUS.md](AZURE_STATUS.md) 为准。**

> 2026-09-30 更新：下述个人电脑 + ngrok 路线已撤回，不用于提交。用户已确认在校且有学校邮箱，现在优先申请 [Azure for Students](https://azure.microsoft.com/en-us/free/students/)。该计划免信用卡，提供 100 美元额度、12 个月使用期限；资格与可用资源以审核结果为准。注册成功后，先核算 VM、磁盘、公网 IP 和流量成本，再部署现有 Linux Docker Compose 栈。服务器运行不依赖用户电脑在线。不要升级付费订阅；额度耗尽或到期会停用服务，不能把 12 个月额度有效期理解为服务器免费运行一年。参见 [订阅停用规则](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/azurestudents-subscription-disabled)。真实 S3 测试资源仍待解决。以下本地部署步骤保留作历史备选，无需执行。

核实日期：2026-09-30。用户已有 GitHub、Google 账号，不希望绑定银行卡。**目前没有注册新账号、创建云资源、启动公网隧道或产生服务费用。**

## 选定的可行路线

| 部分 | 方案 | 边界 |
| --- | --- | --- |
| 源码 | 现有 GitHub 账号 | 仓库仍需创建和推送 |
| LLM | Groq Free，`openai/gpt-oss-20b` | 免费额度有限，以账号 Limits 页为准；没有付费服务自动回退 |
| Django / Redis / Celery / Spark | 个人电脑 Docker Desktop | 需安装、首次验收；运行消耗自己的电力/网络 |
| 公网 HTTPS | ngrok Free 分配的固定开发域名 | 电脑、Docker 和隧道必须持续运行；有首次访问提示和月度配额 |
| 真实 S3 测试 | 已获授权的课程/学校/他人测试桶 | 尚未获得；AWS 常规注册要求支付信息，不能承诺免绑卡完成 |

这不是独立云服务器。评审期间关机、睡眠、断网都会导致链接不可用。是否接受本地托管需由申请人确认；题目没有规定托管厂商，但公共可访问性必须实际满足。若无法保持电脑在线，需要已有的可用服务器或重新讨论部署预算。

## 现在先做：免费 LLM

1. 打开 [Groq Console](https://console.groq.com/)，使用现有账号支持的登录方式注册/登录。保持 Free，不升级到付费计划；若页面要求不愿提供的信息，暂停。
2. 在 API Keys 中创建一个用于这个项目的 key。
3. 在本项目根目录的 `.env` 中填写 `GROQ_API_KEY=`。不要把 key 发到聊天或 GitHub。
4. 默认配置已设为 `LLM_PROVIDER=groq`、`LLM_MODEL=openai/gpt-oss-20b`、`LLM_DAILY_CALL_LIMIT=100`。
5. 程序只把自然语言转换描述发送到该服务，不发送整份 CSV/Excel。每日上限按 UTC 日期统计，命中缓存不占调用预算；失败调用也计入预算。这个限制是额外保护，不取代服务商配额。

`openai/gpt-oss-20b` 是这里使用的 Groq 模型 ID；请求发往 Groq，不需要购买 OpenAI API 额度。只有明确切换 `LLM_PROVIDER=openai` 才使用旧的 OpenAI 配置。

## 第二步：安装本地 Docker

使用 [Docker 官方 Windows 安装指南](https://docs.docker.com/desktop/setup/install/windows-install/)。个人使用属于免费许可范围。用户需自行完成安装器的协议、管理员确认以及可能的重启；不要为了此项目购买订阅。当前未安装或验收 Docker。

在项目目录执行：

```sh
python scripts/check_ready.py
docker compose up --build -d
docker compose exec worker pytest -q
```

先用 `http://localhost:8080` 做本地验收。不要在 Docker 尚未成功运行时启动公网访问。

## 第三步：公网访问（先准备，尚未启动）

1. 在 [ngrok](https://dashboard.ngrok.com/) 注册/登录 Free 账号，获取 assigned dev domain 和 authtoken。只需要 HTTPS 隧道，不需要要求银行卡验证的 TCP 功能或付费自定义域名。
2. 将 token 填在 `.env` 的 `NGROK_AUTHTOKEN=`；不要贴到聊天或命令行历史。
3. 用实际分配的域名执行下列配置命令（示例域名不可直接使用）：

```sh
python scripts/set_public_url.py https://YOUR-ASSIGNED-DOMAIN.ngrok-free.app
```

4. 本地全栈验收后，明确准备公开时才执行：

```sh
docker compose -f compose.yaml -f compose.tunnel.yaml up --build -d
```

这个操作会公开本应用。隧道通过 ngrok 转发并终止外部 HTTPS；AWS 凭据提交属于应用流量，ngrok 是访问链路中的第三方。配置禁用了 agent HTTP inspection，避免把请求内容留在本地调试查看器；这不代表隧道服务商无法处理流量。使用专门的低权限测试凭据。

配置 HTTPS 后 Cookie 为 Secure，本地普通 HTTP 登录流程不再适用；从实际 HTTPS 地址测试。默认 Compose 不包含隧道，也没有替你修改电脑睡眠设置。

ngrok 当前 Free 限额包括 1 GB/月出口、20,000 HTTP 请求/月、一个分配的开发域名，首次访问会显示提示页。一次长任务的轮询也会消耗请求数。达到配额后暂停，不自动购买升级。见 [官方限制](https://ngrok.com/docs/pricing-limits/free-plan-limits)。

## 真实 S3 的剩余障碍

招聘 PDF 明确要求用户凭据连接 Amazon S3，并在视频中展示。MinIO、模拟接口或公开文件下载不能冒充这项验收。

免你本人绑卡的可能途径是：已有课程实验账号/学校云资源，或由确有权限的账号所有者提供专门测试桶的临时只读访问。是否允许这种用途及能提供什么权限，必须由资源所有者确认；不能保证学校一定有。仅需 ListBucket 和 GetObject，测试数据只用生成的虚构数据。

若没有这样的资源且不注册 AWS，仍能继续开发和模拟测试，但最终真实联调/演示要求会保持未完成。可以准备询问招聘方是否能提供临时测试桶的邮件草稿；未经你的明确发送指示，不会联系对方。

## 官方核实来源

- [Groq API 兼容接口](https://console.groq.com/docs/openai)，[免费额度](https://console.groq.com/docs/rate-limits)。
- [Docker Personal](https://www.docker.com/products/personal/)。
- [ngrok Free 限制](https://ngrok.com/docs/pricing-limits/free-plan-limits)。
- [AWS 注册](https://docs.aws.amazon.com/accounts/latest/reference/getting-started.html)。

未采用方案：Oracle Always Free 通常涉及账号验证且有容量限制；Hugging Face 当前创建 Docker Space 需要付费计划；GitHub Pages 只能托管静态内容，不能运行本题的 Django/Celery/Spark 服务。免费政策以后可能变化，注册时再次核对实际页面。
