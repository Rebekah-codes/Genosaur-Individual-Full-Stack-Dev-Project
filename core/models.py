from django.db import models
from django.conf import settings

class Egg(models.Model):
    species_name = models.CharField(max_length=100)
    element_type = models.CharField(max_length=50)
    rarity = models.CharField(max_length=50)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='eggs')
    is_hatched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.species_name} ({self.rarity})"


class Trait(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Dinosaur(models.Model):
    name = models.CharField(max_length=100)
    species_name = models.CharField(max_length=100)
    stage = models.CharField(max_length=50)
    mood = models.CharField(max_length=50)
    traits = models.ManyToManyField(Trait, blank=True, related_name='dinosaurs')
    egg = models.ForeignKey(Egg, on_delete=models.SET_NULL, null=True, related_name='dinosaur')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dinosaurs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.stage})"


class RaiseAction(models.Model):
    ACTION_CHOICES = [
        ('feed', 'Feed'),
        ('play', 'Play'),
        ('train', 'Train'),
    ]

    dinosaur = models.ForeignKey(Dinosaur, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    outcome = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} → {self.dinosaur.name}"


class Trade(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_trades')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_trades')
    dinosaur = models.ForeignKey(Dinosaur, on_delete=models.CASCADE, related_name='trades')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trade: {self.dinosaur.name} from {self.sender} to {self.receiver} ({self.status})"
