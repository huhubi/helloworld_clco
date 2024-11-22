import pulumi
from pulumi_azure_native import resources, storage, web
from pulumi import AssetArchive, FileArchive

# Create an Azure Resource Group
resource_group = resources.ResourceGroup("resource_group", location="West Europe")

# Create a Storage Account
storage_account = storage.StorageAccount(
    "storageaccount",
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
    kind=storage.Kind.STORAGE_V2,
)

# Upload the app code as a zip file
app_code = AssetArchive({".": FileArchive(".")})
blob = storage.Blob(
    "appzip",
    resource_group_name=resource_group.name,
    account_name=storage_account.name,
    container_name="$web",  # Static website container
    source=app_code,
)

# Create a Web App Service Plan
app_service_plan = web.AppServicePlan(
    "appserviceplan",
    resource_group_name=resource_group.name,
    sku=web.SkuDescriptionArgs(
        tier="Free",
        name="F1",
    ),
)

# Create the Web App
web_app = web.WebApp(
    "webapp",
    resource_group_name=resource_group.name,
    server_farm_id=app_service_plan.id,
    site_config=web.SiteConfigArgs(
        app_settings=[
            web.NameValuePairArgs(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE", value="false"),
        ],
        linux_fx_version=pulumi.Config().require("webapp:runtime"),
    ),
)

pulumi.export("resource_group_name", resource_group.name)
pulumi.export("web_app_url", web_app.default_host_name)
