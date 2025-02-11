resource "null_resource" "init_script" {
  triggers = {
    script_hash = filesha1("${path.module}/init.sh")
  }

  provisioner "local-exec" {
    command = "bash init.sh"
  }
}
