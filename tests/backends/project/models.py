from django.db import models


class Star(models.Model):  # type: ignore
    name = models.CharField(max_length=255)
