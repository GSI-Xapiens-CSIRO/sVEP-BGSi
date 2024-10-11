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