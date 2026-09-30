# 免费部署与测试边界

当前网站运行在 Azure for Students 虚拟机，关闭个人电脑不影响网站访问。正式地址：https://pattern-studio-ms-2026.japaneast.cloudapp.azure.com/

- Azure 使用学生赠送额度，不升级付费订阅。额度不是永久免费运行保证；VM、磁盘和公网 IP 会消耗额度，详见 AZURE_STATUS.md。
- Groq 使用现有免费计划，三种模式的真实模型调用已通过。应用限制每天 100 次未缓存请求，没有付费自动回退。专用密钥到期日为 2026-10-31。
- GitHub 仓库已创建并推送，目前为私有，提交前必须解决评审访问权限。
- 用户明确不接受绑卡。当前 AWS Educate 存储课程提供 S3 Simulation，未获得可用于外部应用的真实 S3 凭据。

## 不绑卡的验证方式

隔离测试使用 Moto 模拟 S3 HTTP 接口；Django、PostgreSQL、Redis、Celery、PySpark 和 Groq 均真实运行。正式网站仍使用 Amazon S3，评审者可输入自己获授权的桶凭据。模拟测试不能证明真实 AWS IAM 权限、区域路由或 S3 服务行为全部正确。

请勿把 Moto 写成真实 Amazon S3，也不要把录制的模拟流程描述为真实 S3 演示。真实 AWS 验证仍需另行获得授权的测试资源。

## 重现隔离测试

先按 README 配置 .env、构建正式 API 镜像，并填写有效 Groq 密钥。仅在有足够内存的 Docker 主机运行：

```sh
docker compose build api
docker compose -f compose.integration.yaml up -d
docker compose -f compose.integration.yaml --profile verify run --rm check
docker compose -f compose.integration.yaml stop
```

测试项目使用单独的网络、数据库、Redis 和结果卷，不发布任何端口。`AWS_ENDPOINT_URL_S3` 只在隔离配置中指向 Moto；不修改正式 Compose。测试上传 10,000 行合成 CSV，通过 HTTP 创建异步任务，逐页校验三种模式各 10,000 行、唯一 ID 和原始文件不变。测试会调用真实 LLM，消耗免费配额；停止后保留测试卷便于排查。

本方案不会要求创建收费账户或绑定银行卡。若暂时没有真实 S3 资源，交付记录应明确保留该验证缺口。
