import pulumi
from pulumi_azure_native import resources, storage, web
from pulumi import AssetArchive, FileArchive
from pulumi_command import local
# Create an Azure Resource Group
resource_group = resources.ResourceGroup("resource_group", location="eastasia")

# Create a Storage Account
storage_account = storage.StorageAccount(
    "storageaccount",
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
    kind=storage.Kind.STORAGE_V2,
    allow_blob_public_access=True,  # Enable public access at the storage account level
)

# Create a Blob Container
container = storage.BlobContainer(
    "appcontainer",
    account_name=storage_account.name,
    resource_group_name=resource_group.name,
    public_access=storage.PublicAccess.CONTAINER,  # Enable public access
)
# Upload the application code as a zip file to the Blob
app_code = AssetArchive({".": FileArchive(".")})  # Archive current directory
blob = storage.Blob(
    "appzip",
    resource_group_name=resource_group.name,
    account_name=storage_account.name,
    container_name=container.name,
    source=app_code,
)

# Get the Blob URL
blob_url = pulumi.Output.concat(
    "https://",
    storage_account.name,
    ".blob.core.windows.net/",
    container.name,
    "/",
    blob.name,
)

# Create a Web App Service Plan
app_service_plan = web.AppServicePlan(
    "appserviceplan",
    resource_group_name=resource_group.name,
    kind="Linux",  # Set to Linux
    reserved=True,
    sku=web.SkuDescriptionArgs(
        tier="Basic",
        name="B1",  # Adjust based on requirements
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
            web.NameValuePairArgs(name="WEBSITE_RUN_FROM_PACKAGE", value=blob_url),
        ],
        linux_fx_version="PYTHON|3.11",
    ),
)


# Export outputs
#pulumi.export("resource_group_name", resource_group.name)
pulumi.export("web_app_url", pulumi.Output.concat("http://", web_app.default_host_name))
#pulumi.export("blob_url", blob_url)
pulumi.export("scm_web_app_url", pulumi.Output.concat("http://", web_app.default_host_name.apply(lambda name: name.replace(".azurewebsites.net", ".scm.azurewebsites.net"))))
pulumi.export("log_tail_command", pulumi.Output.all(web_app.name, resource_group.name).apply(lambda args: f"az webapp log tail --name {args[0]} --resource-group {args[1]}"))

# Log the web app URL to the info column
web_app.default_host_name.apply(lambda url: pulumi.log.info(f"Web App URL: http://{url}"))
