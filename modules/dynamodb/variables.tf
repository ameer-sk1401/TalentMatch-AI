variable "table_name" {
    type = string

}
variable "hash_key" {
    type = string
    default = "resume_id"
}
variable "billing_mode" {
    type = string
    default = "PAY_PER_REQUEST"
}
variable "project_name" {
    type = string
    default = "AWS_Resume_analyzer"
}
variable "environment" {
    type = string
    default = "development"
}