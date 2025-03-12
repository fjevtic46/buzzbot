variable "name" {}
variable "location" {}
variable "runtime" {}
variable "entry_point" {}
variable "source_bucket" {}
variable "source_object" {}
variable "envs" {
  type = map(string)
}