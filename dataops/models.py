from django.db import models


class DataJob(models.Model):
    name = models.CharField(max_length=200)
    config_yaml = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class DataRun(models.Model):
    job = models.ForeignKey(DataJob, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, default="queued")
    output_path = models.CharField(max_length=500, blank=True)
    message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

class DataRecord(models.Model):
    run = models.ForeignKey(DataRun, on_delete=models.CASCADE)
    data = models.JSONField()
