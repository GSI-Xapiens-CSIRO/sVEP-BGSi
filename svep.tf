locals {
    region = var.region
}

module "svep-backend" {
    source      = "./backend"
    region      = local.region
    common-tags = merge(var.common-tags, {
        "NAME"  = "svep-backend"
    })
}

module "svep-frontend" {
    source      = "./frontend/terraform-aws"
    region      = local.region
    common-tags = merge(var.common-tags, {
        "NAME"  = "svep-frontend"
    })
    backend_api_url = module.svep-backend.api_url
}