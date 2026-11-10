terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ------------------------------------------------------------------------------
# 1. Dedicated Artifact Registry Repository for this pipeline
# ------------------------------------------------------------------------------
resource "google_artifact_registry_repository" "etl_repo" {
  location      = var.gcp_region
  repository_id = "slipping-away-etl-repo" # Unique name to separate from existing repo
  description   = "Docker repository for Slipping Away ETL container"
  format        = "DOCKER"
}

# ------------------------------------------------------------------------------
# 2. Existing Secret Manager Data Sources (Shared Secrets)
# ------------------------------------------------------------------------------
data "google_secret_manager_secret" "m2m_token" {
  secret_id = "teamup-m2m-token"
}

data "google_secret_manager_secret" "app_password" {
  secret_id = "email-app-password"
}

# ------------------------------------------------------------------------------
# 3. Dedicated IAM & Service Account for this Cloud Run Job
# ------------------------------------------------------------------------------
resource "google_service_account" "etl_runner" {
  account_id   = "slipping-away-runner" # Unique service account
  display_name = "Slipping Away ETL Cloud Run Service Account"
}

# Grant this new Service Account access to the shared secrets
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each = {
    m2m_token    = data.google_secret_manager_secret.m2m_token.secret_id
    app_password = data.google_secret_manager_secret.app_password.secret_id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.etl_runner.email}"
}

resource "google_project_iam_member" "etl_runner_logging" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.etl_runner.email}"
}

# ------------------------------------------------------------------------------
# 4. Independent Cloud Run Job
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_job" "etl_job" {
  name     = "slipping-away-etl-job" # Unique job name
  location = var.gcp_region

  template {
    template {
      service_account = google_service_account.etl_runner.email
      timeout         = "600s"

      containers {
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.etl_repo.repository_id}/slipping-away-etl:latest"

        env {
          name  = "SENDER_EMAIL"
          value = var.sender_email
        }
        env {
          name  = "RECIPIENT_EMAIL"
          value = var.recipient_email
        }

        # Inject Shared Secrets
        env {
          name = "M2M_TOKEN"
          value_source {
            secret_key_ref {
              secret  = data.google_secret_manager_secret.m2m_token.secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "APP_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = data.google_secret_manager_secret.app_password.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.secret_access]
}

# ------------------------------------------------------------------------------
# 5. Independent Cloud Scheduler
# ------------------------------------------------------------------------------
resource "google_service_account" "scheduler_sa" {
  account_id   = "slipping-away-scheduler" # Unique scheduler SA
  display_name = "Slipping Away Scheduler Invoker Service Account"
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  location = google_cloud_run_v2_job.etl_job.location
  name     = google_cloud_run_v2_job.etl_job.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

resource "google_cloud_scheduler_job" "weekly_trigger" {
  name             = "weekly-slipping-away-sync" # Unique schedule name
  description      = "Triggers Slipping Away ETL pipeline"
  schedule         = "0 6 * * 3"
  time_zone        = var.time_zone
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "https://${var.gcp_region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.gcp_project_id}/jobs/${google_cloud_run_v2_job.etl_job.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
}

# ------------------------------------------------------------------------------
# 6. Independent Monitoring Alerting Policy
# ------------------------------------------------------------------------------
resource "google_monitoring_notification_channel" "email_alert" {
  display_name = "Slipping Away ETL Failure Notification"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

resource "google_monitoring_alert_policy" "job_failure_alert" {
  display_name = "Slipping Away ETL Job Execution Failure"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run Job Failure"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_job\" AND resource.labels.job_name = \"${google_cloud_run_v2_job.etl_job.name}\" AND metric.type = \"run.googleapis.com/job/completed_execution_count\" AND metric.labels.result = \"failed\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email_alert.name]
}