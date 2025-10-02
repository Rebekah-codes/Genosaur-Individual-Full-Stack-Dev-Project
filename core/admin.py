from django.contrib import admin
from .models import Egg, Dinosaur, Trait, RaiseAction, Trade


@admin.register(Egg)
class EggAdmin(admin.ModelAdmin):
    list_display = ("species_name", "element_type", "rarity", "owner", "is_hatched", "created_at")
    list_filter = ("element_type", "rarity", "is_hatched")
    search_fields = ("species_name", "owner__username")


@admin.register(Dinosaur)
class DinosaurAdmin(admin.ModelAdmin):
    list_display = ("name", "species_name", "stage", "mood", "owner", "created_at")
    list_filter = ("stage", "mood")
    search_fields = ("name", "species_name", "owner__username")
    filter_horizontal = ("traits",)


@admin.register(Trait)
class TraitAdmin(admin.ModelAdmin):
    list_display = ("name", "mood_impact")
    search_fields = ("name", "description")


@admin.register(RaiseAction)
class RaiseActionAdmin(admin.ModelAdmin):
    list_display = ("action_type", "dinosaur", "timestamp")
    list_filter = ("action_type", "timestamp")
    search_fields = ("dinosaur__name", "outcome")


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("dinosaur", "sender", "receiver", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("dinosaur__name", "sender__username", "receiver__username")
