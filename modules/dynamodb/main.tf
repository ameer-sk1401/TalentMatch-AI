resource "aws_dynamodb_table" "main" {
    name = var.table_name
    billing_mode = var.billing_mode
    hash_key = var.hash_key

    attribute {
    name = "resume_id"
    type = "S"
    }
    attribute {
    name = "role"
    type = "S"
    }

    global_secondary_index {
        name = "role-index"
        hash_key = "role"
        projection_type = "ALL"
        
    }
    point_in_time_recovery {
        enabled = true
    }
    tags = {
        Name = "${var.table_name}-metadata"
    }
}