from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.text import slugify

from .models import (
    ParentCategory,
    Service,
    ServiceCategory,
    ServiceImage,
    ServiceOption,
)


# ── Dynamic M2M Admin Form ──────────────────────────────────────
# Generates a <select> dropdown for every ServiceOption group,
# allowing the salon owner to map which options an image represents
# without dealing with a raw M2M widget.


class DynamicServiceImageForm(forms.ModelForm):
    """
    Dynamic form that adds a dropdown for each ServiceOption group.

    Instead of a raw M2M widget, the salon owner sees dropdowns like:
        Color:    [--- Any Color ---] [Black] [Brown] ...
        Length:   [--- Any Length ---] [Shoulder] [Waist] ...

    On save, selected option IDs are collected and set on linked_options.
    """

    class Meta:
        model = ServiceImage
        fields = ["image", "order"]

    def __init__(self, *args, parent_service=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent_service = parent_service
        self._group_fields = []  # [(field_name, group_name), ...]

        if parent_service and parent_service.pk:
            grouped = parent_service.get_options_grouped()
            for group in grouped:
                group_name = group["group_name"]
                field_name = f"_opt_{slugify(group_name)}"
                if field_name in self.fields:
                    continue  # skip duplicates from slug collisions

                choices = [("", f"— Any {group_name} —")]
                for opt in group["options"]:
                    label = opt.value
                    if opt.additional_price > 0:
                        label += f" (+{int(opt.additional_price):,} Ft)"
                    choices.append((opt.id, label))

                self.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    required=False,
                    label=group_name,
                )
                self._group_fields.append((field_name, group_name))

                # Pre-populate current selection
                if self.instance and self.instance.pk:
                    current = (
                        self.instance.linked_options.filter(
                            group_name=group_name
                        )
                        .values_list("id", flat=True)
                        .first()
                    )
                    if current:
                        self.initial[field_name] = str(current)

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and instance.pk and self._group_fields:
            selected_ids = []
            for field_name, _group_name in self._group_fields:
                opt_id = self.cleaned_data.get(field_name)
                if opt_id:
                    selected_ids.append(int(opt_id))
            instance.linked_options.set(selected_ids)
        return instance


class ServiceImageInlineFormSet(forms.BaseInlineFormSet):
    """Passes the parent Service to each inline form for dynamic fields."""

    def _construct_form(self, i, **kwargs):
        kwargs["parent_service"] = self.instance
        return super()._construct_form(i, **kwargs)


class ServiceImageInline(admin.StackedInline):
    model = ServiceImage
    extra = 1
    ordering = ("order",)
    form = DynamicServiceImageForm
    formset = ServiceImageInlineFormSet

    # Read-only preview of the uploaded image
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj and obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; '
                'border-radius: 8px;" />',
                obj.image.url,
            )
        return "—"
    image_preview.short_description = "Preview"


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
