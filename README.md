
## API仕様書

- [開発環境](https://s3.ap-northeast-1.amazonaws.com/juv-shun.website-hosting/unitemate-api/dev/redoc.html)
- [本番環境](https://s3.ap-northeast-1.amazonaws.com/juv-shun.website-hosting/unitemate-api/prd/redoc.html)

## システム構成図

![システム構成図](./docs/infra.png)

## 構築方法

### 事前インフラ構築

下記インフラリソースは本リポジトリでは管理しないため、事前に用意すること。

- ドメインを取得し、Route53のホストが作成されていること。
- 取得したドメインに対してCertificate Managerで証明書が発行済であること。
- 取得した証明書のCertificate ARNをパラメータストアに保存済みであること。

### カスタムドメイン作成

```sh
sls create_domain -s {env}
```

### デプロイ

```sh
sls deploy -s {env}
```
