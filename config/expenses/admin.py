from django.contrib import admin
from .models import Settlement


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "from_user", "to_user", "amount", "date")
    list_filter = ("group",)
    search_fields = ("from_user__email", "to_user__email", "note")
    readonly_fields = ("date",)
