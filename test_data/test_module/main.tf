
module "test" {
  source         = "../../"
  gh_org_name    = "infrahouse"
  repo_name      = "test"
  subject_claims = var.subject_claims
}
