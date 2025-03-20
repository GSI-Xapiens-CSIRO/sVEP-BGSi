resource "null_resource" "init_script" {
  triggers = {
    script_hash = filesha1("${path.module}/init.sh")
  }

  provisioner "local-exec" {
    command = "bash init.sh"
  }
}

# resource "null_resource" "init_gnomad_script" {
#   triggers = {
#     script_hash = filesha1("${path.module}/lambda/pluginGnomad/init.sh")
#   }

#   provisioner "local-exec" {
#     command = "bash ${path.module}/lambda/pluginGnomad/init.sh"
#   }
# }
