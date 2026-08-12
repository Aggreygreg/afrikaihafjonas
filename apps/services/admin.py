from django.contrib import admin, messages
from django.utils.html import format_html

from .models import (
    ParentCategory,
    Service,
    ServiceCategory,
    ServiceImage,
    ServiceOption,
)

# NOTE: The dynamic M2M admin form (grouped option dropdowns for
# ServiceImage.linked_options) requires StackedInline to render.
# Currently using TabularInline for compactness; linked_options is
# editable via each ServiceImage's own change form. The dynamic
# form code (DynamicServiceImageForm + ServiceImageInlineFormSet)
# is preserved in git history for future activation.


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    ordering = ("order",)


class ServiceOptionInline(admin.TabularInline):
    model = ServiceOption
    extra = 1


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "target_audience",
        "base_price",
        "discount_percentage",
        "discount_display",
        "duration_minutes",
        "is_popular",
    )
    list_filter = (
        "category__parent",
        "category",
        "target_audience",
        "is_popular",
        "discount_percentage",
    )
    list_editable = ("discount_percentage",)  # Quick-edit in list view
    search_fields = ("title", "description")
    filter_horizontal = ("providers",)
    inlines = [ServiceImageInline, ServiceOptionInline]

    fieldsets = (
        (None, {
            "fields": ("title", "description", "category", "is_popular"),
        }),
        ("Suitability & Requirements", {
            "fields": ("target_audience", "best_for_hair_types", "suitability_warning"),
        }),
        ("Pricing & Duration", {
            "fields": ("base_price", "discount_percentage", "duration_minutes"),
            "description": (
                "Set discount_percentage > 0 to activate seasonal pricing. "
                "Discounted price is calculated automatically."
            ),
        }),
        ("Providers", {
            "fields": ("providers",),
        }),
        ("Optional Video", {
            "fields": ("video_url",),
            "classes": ("collapse",),
        }),
    )

    actions = ["apply_discount_bulk", "clear_discounts"]

    # ── Seasonal Discount Bulk Actions ────────────────────────

    @admin.action(description="🏷️ Apply 15% seasonal discount to selected")
    def apply_discount_bulk(self, request, queryset):
        updated = queryset.update(discount_percentage=15)
        messages.success(
            request,
            f"Applied 15% seasonal discount to {updated} service(s).",
        )

    @admin.action(description="🔄 Clear all discounts on selected")
    def clear_discounts(self, request, queryset):
        updated = queryset.update(discount_percentage=0)
        messages.success(
            request,
            f"Cleared discounts on {updated} service(s).",
        )

    # ── Display Helpers ───────────────────────────────────────

    def discount_display(self, obj):
        if obj.discount_percentage > 0:
            return format_html(
                '<strong style="color: #ef4444;">-{}%</strong><br>'
                '<span style="font-size: 11px; color: #6b7280;">'
                "{:,} \u2192 {:,} Ft</span>",
                obj.discount_percentage,
                int(obj.base_price),
                int(obj.discounted_price),
            )
        return "\u2014"
    discount_display.short_description = "Discount"


@admin.register(ParentCategory)
class ParentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    list_filter = ("parent",)
    search_fields = ("name",)
    ordering = ("parent", "name")
