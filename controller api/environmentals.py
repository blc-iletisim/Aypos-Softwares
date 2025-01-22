import os


def define_environmentals():
    os.environ["OS_USER_DOMAIN_NAME"] = "Default"
    os.environ["OS_PROJECT_NAME"] = "admin"
    os.environ["OS_TENANT_NAME"] = "admin"
    os.environ["OS_USERNAME"] = "admin"
    os.environ["OS_PASSWORD"] = "WHMFjzLBHf1N6FxPnZpCDsXYdXewgjsvwju385Mk"
    os.environ["OS_AUTH_URL"] = "http://10.150.1.251:35357/v3"
    os.environ["OS_INTERFACE"] = "internal"
    os.environ["OS_ENDPOINT_TYPE"] = "internalURL"
    os.environ["OS_IDENTITY_API_VERSION"] = "3"
    os.environ["OS_REGION_NAME"] = "RegionOne"
    os.environ["OS_AUTH_PLUGIN"]="password"
    os.environ["OS_PROJECT_DOMAIN_NAME"] = "Default"
