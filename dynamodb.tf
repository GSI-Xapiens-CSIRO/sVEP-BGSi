# References Table
resource "aws_dynamodb_table" "svep_references" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  name         = var.svep-references-table-name
  tags         = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }
}