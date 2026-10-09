variable "region" {}
variable "role_arn" {
  default = null
}
variable "subject_claims" {
  type    = list(string)
  default = ["*"]
}
