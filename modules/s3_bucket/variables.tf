 variable "region_name" {
    type        = string
    description = "The name of the region where the VPC will be created."
    default = "us-east-1"
 }
 variable "bucket_name" {
   type =string
   
 }
 variable "enable_versioning" {
   type = bool
   default = true
 }
variable "force_destroy" {
   type = bool
   default = false
 }