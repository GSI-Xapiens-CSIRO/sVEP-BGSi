locals {
    region = var.region
}

module "svep-backend" {
    source      = "./backend"
    region      = local.region
    common-tags = merge(var.common-tags, {
        "NAME"  = "svep-backend"
    })
    data_portal_bucket_arn = "arn:aws:s3:::sbeacon-backend-dataportal-20241107003128459300000004"
}

module "svep-frontend" {
    source      = "./frontend/terraform-aws"
    region      = local.region
    common-tags = merge(var.common-tags, {
        "NAME"  = "svep-frontend"
    })
    backend_api_url = module.svep-backend.api_url
    user_pool_id = "ap-southeast-2_tQPsAYY7s"
    identity_pool_id = "ap-southeast-2:aa202e68-2f2e-498b-8b42-fa893381054f"
    data_portal_bucket = "sbeacon-backend-dataportal-20241107003128459300000004"
    user_pool_web_client_id = "4eonbhd063ejtuj4a4t9mj1msa"
    api_endpoint_sbeacon = "https://bc7h3fkcl2.execute-api.ap-southeast-2.amazonaws.com/prod/"
}