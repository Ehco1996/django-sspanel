from django.db import models


class OpenAPIKey(models.Model):
    name = models.CharField(max_length=32)
    key = models.CharField(max_length=32)
    
