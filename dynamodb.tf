locals {
  clinic_jobs_project_name_index = "project-name-index"
}

# References Table
resource "aws_dynamodb_table" "svep_references" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  name         = var.svep-references-table-name

  tags = merge(var.common-tags, var.common-tags-backup)

  attribute {
    name = "id"
    type = "S"
  }
}
