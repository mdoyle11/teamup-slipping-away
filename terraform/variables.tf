variable "gcp_project_id" {
  type        = string
  description = "Target GCP Project ID"
}

variable "gcp_region" {
  type        = string
  default     = "us-east4"
  description = "GCP Deployment Region"
}

variable "time_zone" {
  type        = string
  default     = "America/New_York"
  description = "Cron Schedule Timezone"
}

variable "sender_email" {
  type        = string
  description = "Email address sending report emails"
}

variable "recipient_email" {
  type        = string
  description = "Email address receiving report summaries"
}

variable "alert_email" {
  type        = string
  description = "Email address receiving failure alert notifications"
}