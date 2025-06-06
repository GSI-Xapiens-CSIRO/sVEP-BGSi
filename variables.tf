variable "region" {
  type        = string
  description = "Deployment region of the webapp."
  default     = "ap-southeast-2"
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

variable "gtf_file_base" {
  type        = string
  description = "Base name for the GTF reference file"
  default     = "Homo_sapiens.GRCh38"
}

variable "splice_file_base" {
  type        = string
  description = "Base name for the splice GTF reference file"
  default     = "splice.Homo_sapiens.GRCh38"
}

variable "fasta_file_base" {
  type        = string
  description = "Base name for the FASTA reference file"
  default     = "Homo_sapiens.GRCh38.dna.chromosome"
}

variable "mirna_file_base" {
  type        = string
  description = "Base name for the miRNA reference file"
  default     = "mirna"
}

# Throttling variables
variable "method-max-request-rate" {
  type        = number
  description = "Number of requests allowed per second per method."
  default     = 100
}

variable "method-queue-size" {
  type        = number
  description = "Number of requests allowed to be queued per method."
  default     = 1000
}

variable "web_acl_arn" {
  type        = string
  description = "arn of the WAF Web ACL to associate with the API's cloudfront distribution"
  default     = null
}

# cognito variables
variable "cognito-user-pool-arn" {
  type        = string
  description = "Cognito user pool ARN"
}

# external dynamodb tables
variable "dynamo-project-users-table" {
  type        = string
  description = "Dynamo project users table"
}

variable "dynamo-project-users-table-arn" {
  type        = string
  description = "Dynamo project users table ARN"
}

variable "dynamo-clinic-jobs-table" {
  type        = string
  description = "Dynamo clinic jobs table"
}

variable "dynamo-clinic-jobs-table-arn" {
  type        = string
  description = "Dynamo clinic jobs table ARN"
}

variable "dynamo-clinic-jobs-stream-arn" {
  type        = string
  description = "Dynamo clinic jobs stream ARN"
}

variable "clinic-job-email-lambda-function-arn" {
  type        = string
  description = "Lambda function ARN for sending Clinic Job emails"
}

variable "cognito-user-pool-id" {
  type        = string
  description = "Cognito user pool Id."
}

variable "svep-references-table-name" {
  type        = string
  description = "Name of the references table"
}

# Hub configurations
variable "hub_name" {
  type        = string
  description = "Configuration for the hub"
  default     = "NONE"
}

variable "filters" {
  type = object({
    clinvar_exclude = optional(list(string), [])
    # highest consequence rank to include, e.g. 12 for protein_altering_variant.
    # see svep/lambda/pluginConsequence/consequence/constants.pm for values.
    consequence_rank = optional(number, 99)
    genes            = optional(list(string), [])
    max_maf          = optional(number, 1)
    min_qual         = optional(number, 0)
  })
  description = "Filters to apply to the svep records"
}
