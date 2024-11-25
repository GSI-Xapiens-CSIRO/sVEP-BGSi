variable "region" {
  type          = string
  description   = "Deployment region of the webapp."
  default       = "ap-southeast-2"
}

variable "common-tags" {
    type        = map(string)
    description = "A set of tags to attach to every created sVEP resource."
    default = {
        "PROJECT" = "SVEP"
    }
}


variable "data_portal_bucket_arn" {
  type        = string
  description = "ARN of the data portal bucket"
}

variable "data_portal_bucket_name" {
  type        = string
  description = "Name of the data portal bucket"
}