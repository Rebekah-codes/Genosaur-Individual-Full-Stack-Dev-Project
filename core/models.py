from django.db import models
from django.conf import settings


class Egg(models.Model):
    species_name = models.CharField(max_length=100)
    element_type = models.CharField(max_length=50)   # e.g. Fire, Water, Earth
    rarity = models.CharField(max_length=50)         # e.g. Common, Rare, Legendary
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='eggs'
    )
    is_hatched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Nest materials for hatching
    twigs = models.PositiveIntegerField(default=0)
    leaves = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"🥚 {self.species_name} Egg ({self.rarity})"


class Trait(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    mood_impact = models.CharField(
        max_length=50,
        blank=True,
        help_text="How this trait influences mood (e.g. +Playful, -Calm)"
    )

    def __str__(self):
        return f"{self.name} ({self.mood_impact})" if self.mood_impact else self.name


class Dinosaur(models.Model):
    STAGE_CHOICES = [
        ('hatchling', 'Hatchling'),
        ('juvenile', 'Juvenile'),
        ('adult', 'Adult'),
    ]

    MOOD_CHOICES = [
        ('happy', 'Happy'),
        ('hungry', 'Hungry'),
        ('playful', 'Playful'),
        ('tired', 'Tired'),
    ]

    name = models.CharField(max_length=100)
    species_name = models.CharField(max_length=100)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='hatchling')
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='happy')
    traits = models.ManyToManyField(Trait, blank=True, related_name='dinosaurs')
    egg = models.OneToOneField(
        Egg,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dinosaur'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dinosaurs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    level = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"🦕 {self.name} ({self.stage}, {self.mood})"

    def get_sprite(self):
        """Return the relative static path for the dino's current stage sprite."""
        stage_sprites = {
            "hatchling": "images/hatchling.png",
            "juvenile": "images/juvenile.png",
            "adult": "images/adult.png",
        }
        return stage_sprites.get(self.stage, "images/hatchling.png")

    def level_up(self, amount=1):
        """Increase level but cap at 100."""
        self.level = min(self.level + amount, 100)
        self.save()


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

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_trades'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_trades'
    )
    dinosaur = models.ForeignKey(Dinosaur, on_delete=models.CASCADE, related_name='trades')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trade: {self.dinosaur.name} from {self.sender} to {self.receiver} ({self.status})"
