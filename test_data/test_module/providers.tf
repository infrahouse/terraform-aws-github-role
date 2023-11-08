provider "aws" {
  assume_role {
    role_arn = "arn:aws:iam::303467602807:role/github-role-tester"
  }
  region = "us-west-1"
  default_tags {
    tags = {
      "created_by" : "infrahouse/terraform-aws-github-role" # GitHub repository that created a resource
    }
  }
}
