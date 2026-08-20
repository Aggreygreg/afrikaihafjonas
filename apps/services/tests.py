from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.html import escape

from apps.services.models import (
    ParentCategory, ParentCategoryTranslation,
    ServiceCategory, ServiceCategoryTranslation,
    Service, ServiceOption, ServiceOptionTranslation, ServiceTranslation,
)

# NOTE: responses render in the project default language (hu) when compiled
# .mo catalogs are present, so never assert on {% trans %} literals — assert
# on markup structure or response.context instead. Category names come from
# the DB and are HTML-escaped in output (apostrophes become &#x27;).
E = escape


def make_service(category, title, price=10000, duration=120, discount=0,
                 description="", popular=False):
    svc = Service.objects.create(
        category=category,
        target_audience="Adults",
        base_price=price,
        discount_percentage=discount,
        duration_minutes=duration,
        is_popular=popular,
    )
    ServiceTranslation.objects.create(
        service=svc, language="hu",
        title=title,
        description=description or f"Description for {title}",
    )
    return svc



def make_parent_category(name, language="hu"):
    """Create a ParentCategory + HU translation (replaces old .create(name=))."""
    pc = ParentCategory.objects.create()
    ParentCategoryTranslation.objects.create(
        parent_category=pc, language=language, name=name)
    return pc


def make_service_category(parent, name, language="hu"):
    """Create a ServiceCategory + HU translation (replaces old .create(name=))."""
    sc = ServiceCategory.objects.create(parent=parent)
    ServiceCategoryTranslation.objects.create(
        service_category=sc, language=language, name=name)
    return sc


def make_service_option(service, group_name, value, additional_price=0, language="hu"):
    """Create a ServiceOption + HU translation (replaces old .create(value=))."""
    opt = ServiceOption.objects.create(
        service=service, group_name=group_name, additional_price=additional_price)
    ServiceOptionTranslation.objects.create(
        service_option=opt, language=language, group_name=group_name, value=value)
    return opt


def _inline_data(prefix, total, initial=0, rows=None):
    """Build inline formset management-form + row data for admin POST tests."""
    data = {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": str(initial),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }
    if rows:
        for index, row in rows.items():
            for key, val in row.items():
                data[f"{prefix}-{index}-{key}"] = str(val)
    return data


class CatalogFixtureMixin:
    """Classic trio of ParentCategories in creation order (Women -> Men ->
    Children), mirroring the production seed order, plus one service each."""

    @classmethod
    def setUpTestData(cls):
        cls.women = ParentCategory.objects.create()
        ParentCategoryTranslation.objects.create(parent_category=cls.women, language="hu", name="Women's Braids")
        cls.men = ParentCategory.objects.create()
        ParentCategoryTranslation.objects.create(parent_category=cls.men, language="hu", name="Men's Braids")
        cls.children = ParentCategory.objects.create()
        ParentCategoryTranslation.objects.create(parent_category=cls.children, language="hu", name="Children's Braids")

        cls.womens_cat = ServiceCategory.objects.create(parent=cls.women)
        ServiceCategoryTranslation.objects.create(service_category=cls.womens_cat, language="hu", name="Knotless Box Braids")
        cls.mens_cat = ServiceCategory.objects.create(parent=cls.men)
        ServiceCategoryTranslation.objects.create(service_category=cls.mens_cat, language="hu", name="Men's Cornrows")
        cls.childrens_cat = ServiceCategory.objects.create(parent=cls.children)
        ServiceCategoryTranslation.objects.create(service_category=cls.childrens_cat, language="hu", name="Kids Cornrows")

        cls.womens_service = make_service(
            cls.womens_cat, "Knotless Box Braids - Medium", price=45000,
            description="Classic knotless braids", popular=True)
        cls.mens_service = make_service(
            cls.mens_cat, "Two Strand Twists Men", price=20000,
            description="Twists for men")
        cls.childrens_service = make_service(
            cls.childrens_cat, "Kids Cornrows Simple", price=15000,
            description="Simple cornrows for kids", discount=10)


class DynamicCategoryTabsTests(CatalogFixtureMixin, TestCase):
    """The top-level tabs on /services/ are generated from ParentCategory
    records (admin-driven), selected by ID — never by name."""

    def test_existing_categories_render_as_tabs(self):
        """All existing ParentCategories appear as tabs, in creation order."""
        response = self.client.get("/services/")
        self.assertEqual(response.status_code, 200)
        for name in ("Women's Braids", "Men's Braids", "Children's Braids"):
            self.assertContains(response, E(name))
        html = response.content.decode()
        self.assertTrue(html.index(E("Women's Braids")) < html.index(E("Men's Braids"))
                        < html.index(E("Children's Braids")),
                        "Tabs must render in creation order (Women -> Men -> Children)")

    def test_newly_created_category_appears_automatically(self):
        """An admin-created ParentCategory becomes a tab with no code change."""
        bridal = make_parent_category("Bridal")
        response = self.client.get("/services/")
        self.assertContains(response, "Bridal")
        self.assertContains(response, 'data-cat-tab="%d"' % bridal.pk)

    def test_tabs_use_id_based_selection(self):
        """Tab buttons carry the category pk; no name-based switching remains."""
        response = self.client.get("/services/")
        self.assertContains(response, 'data-cat-tab="%d"' % self.women.pk)
        self.assertContains(response, "switchCategory('%d')" % self.women.pk)
        self.assertNotContains(response, "switchGender")
        self.assertNotContains(response, 'name="gender"')

    def test_default_view_selects_first_category(self):
        """No `cat` param -> first category in creation order is active and
        its services shown (legacy default: Women's Braids)."""
        response = self.client.get("/services/")
        self.assertContains(response, self.womens_service.display_title)
        self.assertNotContains(response, self.mens_service.display_title)
        self.assertNotContains(response, self.childrens_service.display_title)

    def test_hidden_input_carries_active_pk(self):
        response = self.client.get("/services/", {"cat": self.men.pk})
        self.assertContains(response, 'name="cat" id="cat-input" value="%d"' % self.men.pk)

    def test_invalid_or_unknown_cat_falls_back_to_default(self):
        """Bad values degrade to the default tab instead of erroring."""
        for bad in ("abc", "-1", "99999", ""):
            response = self.client.get("/services/", {"cat": bad})
            self.assertEqual(response.status_code, 200, "cat=%r must not crash" % bad)
            self.assertContains(response, self.womens_service.display_title)

    def test_legacy_gender_param_is_ignored(self):
        """The removed name-based `gender` param must NOT filter (and must
        never resolve Men's -> Women's again)."""
        response = self.client.get("/services/", {"gender": "Men's Braids"})
        self.assertContains(response, self.womens_service.display_title)
        self.assertNotContains(response, self.mens_service.display_title)


class CategoryFilteringTests(CatalogFixtureMixin, TestCase):
    """Selecting a category filters via ParentCategory -> ServiceCategory ->
    Service, with no name-substring collisions."""

    def test_mens_never_resolves_to_womens(self):
        """THE regression: 'Men's Braids' icontains-matched 'Women's Braids'
        (substring). ID-based selection must never cross-match."""
        response = self.client.get("/services/", {"cat": self.men.pk})
        self.assertContains(response, self.mens_service.display_title)
        self.assertNotContains(
            response, self.womens_service.display_title,
            msg_prefix="'Men's Braids' resolved to 'Women's Braids' — substring collision")

    def test_substring_named_categories_do_not_collide(self):
        """Categories whose names are substrings of each other stay isolated."""
        long_cat_parent = make_parent_category("Braids")
        short_cat_parent = make_parent_category("Long Braids")
        c1 = make_service_category(long_cat_parent, "Sub A")
        c2 = make_service_category(short_cat_parent, "Sub B")
        s1 = make_service(c1, "Service In Braids")
        s2 = make_service(c2, "Service In Long Braids")
        r1 = self.client.get("/services/", {"cat": long_cat_parent.pk})
        self.assertContains(r1, s1.display_title)
        self.assertNotContains(r1, s2.display_title)
        r2 = self.client.get("/services/", {"cat": short_cat_parent.pk})
        self.assertContains(r2, s2.display_title)
        self.assertNotContains(r2, s1.display_title)

    def test_each_category_filters_correctly(self):
        pairs = [
            (self.women, self.womens_service),
            (self.men, self.mens_service),
            (self.children, self.childrens_service),
        ]
        for parent, service in pairs:
            response = self.client.get("/services/", {"cat": parent.pk})
            self.assertContains(response, service.display_title,
                                msg_prefix="service for %s missing" % parent.display_name)
            for other_parent, other_service in pairs:
                if other_parent is not parent:
                    self.assertNotContains(response, other_service.display_title)

    def test_subcategory_sidebar_follows_selected_parent(self):
        """Sidebar dropdown lists ONLY the active parent's subcategories."""
        response = self.client.get("/services/", {"cat": self.men.pk})
        self.assertContains(response, E(self.mens_cat.display_name))
        self.assertNotContains(response, E(self.womens_cat.display_name))
        self.assertNotContains(response, E(self.childrens_cat.display_name))

    def test_subcategory_filter_applies_within_parent(self):
        """?cat=X&category=Y filters to subcategory Y under parent X."""
        second_womens = make_service_category(self.women, "Goddess Locs")
        make_service(second_womens, "Goddess Locs Style", price=30000)
        response = self.client.get("/services/", {
            "cat": self.women.pk, "category": self.womens_cat.pk})
        self.assertContains(response, self.womens_service.display_title)
        self.assertNotContains(response, "Goddess Locs Style")

    def test_search_sort_price_still_work(self):
        """Search, price bounds and sort keep working under a category scope."""
        knot_womens = make_service(self.womens_cat, "Goddess Locs Premium", price=90000)
        # Search within Women's tab
        r = self.client.get("/services/", {"cat": self.women.pk, "q": "Knotless"})
        self.assertContains(r, self.womens_service.display_title)
        self.assertNotContains(r, knot_womens.display_title)
        # Price ceiling excludes the premium style
        r = self.client.get("/services/", {"cat": self.women.pk, "price_max": "50000"})
        self.assertContains(r, self.womens_service.display_title)
        self.assertNotContains(r, knot_womens.display_title)
        # Sort ascending by price: Knotless (45000) first, then Goddess (90000)
        r = self.client.get("/services/", {"cat": self.women.pk, "sort_by": "price_asc"})
        html = r.content.decode()
        self.assertLess(html.index(self.womens_service.display_title), html.index(knot_womens.display_title))
        # Discounted-only: only the Children's service has a discount
        r = self.client.get("/services/", {"cat": self.children.pk, "discounted_only": "1"})
        self.assertContains(r, self.childrens_service.display_title)

    def test_new_category_tab_filters_to_its_own_services(self):
        """An admin-created category shows only its own services (empty state
        included) when selected."""
        bridal = make_parent_category("Bridal")
        r = self.client.get("/services/", {"cat": bridal.pk})
        self.assertEqual(list(r.context["services"]), [])
        self.assertNotContains(r, self.womens_service.display_title)


class EmptyCatalogTests(TestCase):
    """Degenerate DB states must render safely."""

    def test_no_parent_categories_renders_unfiltered(self):
        """Zero ParentCategories: page renders, no tab bar, services shown."""
        orphan_cat = make_service_category(None, "Orphan Type")
        orphan = make_service(orphan_cat, "Orphan Service")
        response = self.client.get("/services/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-cat-tab="')
        self.assertContains(response, orphan.display_title)

    def test_completely_empty_database(self):
        response = self.client.get("/services/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["services"]), [])

    def test_no_categories_invalid_cat_param(self):
        response = self.client.get("/services/", {"cat": "42"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["services"]), [])


class ServiceListHTMXTests(CatalogFixtureMixin, TestCase):
    """Regression tests for the catalog HTMX wiring.

    Bug fixed 2026-08-18: service_list.html used hx-get / hx-trigger and called
    htmx.trigger() without ever loading the HTMX runtime, so live filtering
    (category tabs, debounced search) was dead. The runtime must be included on
    this template (the base template intentionally does not bundle it).
    """

    def test_htmx_runtime_loaded_on_catalog_page(self):
        """The HTMX <script> include must be present — without it, category
        tabs throw `htmx is not defined` and search/filter triggers are inert."""
        response = self.client.get("/services/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "htmx.org", count=1)

    def test_htmx_request_returns_partial_only(self):
        """HX-Request header must render the partial whose root is
        #services-wrapper (the hx-target), not the full page."""
        response = self.client.get("/services/", HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "services/partials/service_grid.html")
        self.assertTemplateNotUsed(response, "services/service_list.html")
        self.assertContains(response, 'id="services-wrapper"', count=1)
        # Base page chrome must NOT be swapped into the target
        self.assertNotContains(response, "<!DOCTYPE html>")

    def test_plain_request_returns_full_page(self):
        """Non-HTMX (native form fallback / direct navigation) still gets the
        full page — the no-JS "Apply Filters" submit path depends on this."""
        response = self.client.get("/services/")
        self.assertTemplateUsed(response, "services/service_list.html")

    def test_category_param_flows_in_both_modes(self):
        """The `cat` pk param must drive filtering in BOTH the HTMX partial
        and the native full-page response."""
        partial = self.client.get(
            "/services/", {"cat": self.children.pk}, HTTP_HX_REQUEST="true"
        )
        self.assertContains(partial, self.childrens_service.display_title)
        self.assertNotContains(partial, self.womens_service.display_title)

        full = self.client.get("/services/", {"cat": self.children.pk})
        self.assertContains(full, self.childrens_service.display_title)
        self.assertNotContains(full, self.womens_service.display_title)


class AdminCategoryCrudTests(CatalogFixtureMixin, TestCase):
    """Admin CRUD keeps working and admin-created categories flow into the
    catalog automatically (the dynamic-tab contract)."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = get_user_model().objects.create_superuser(
            "catadmin", "catadmin@example.com", "pw-12345")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_parent_category_changelist_loads(self):
        response = self.client.get("/admin/services/parentcategory/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, E("Women's Braids"))

    def test_admin_can_create_parent_category(self):
        data = _inline_data("translations", 3,
            rows={0: {"language": "hu", "name": "Locs"}})
        data["_save"] = "Save"
        response = self.client.post(
            "/admin/services/parentcategory/add/",
            data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ParentCategory.objects.filter(translations__name="Locs").exists())

        # New category immediately selectable on the catalog page
        catalog = self.client.get("/services/")
        self.assertContains(catalog, "Locs")

    def test_admin_can_rename_parent_category(self):
        trans = self.children.translations.get(language="hu")
        data = _inline_data("translations", 4, initial=1,
            rows={0: {"id": trans.pk, "parent_category": self.children.pk,
                      "language": "hu", "name": "Kids Braids"}})
        data["_save"] = "Save"
        response = self.client.post(
            "/admin/services/parentcategory/%d/change/" % self.children.pk,
            data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        catalog = self.client.get("/services/")
        self.assertContains(catalog, "Kids Braids")
        # Renaming must not break filtering: pk unchanged
        self.assertContains(catalog, 'data-cat-tab="%d"' % self.children.pk)

    def test_admin_can_delete_parent_category(self):
        response = self.client.post(
            "/admin/services/parentcategory/%d/delete/" % self.children.pk,
            {"post": "yes"}, follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ParentCategory.objects.filter(pk=self.children.pk).exists())
        # Catalog still renders; children's services disappear with the cascade
        catalog = self.client.get("/services/")
        self.assertNotContains(catalog, "Children's Braids")
        self.assertContains(catalog, self.womens_service.display_title)


class ServiceImageDropdownTests(CatalogFixtureMixin, TestCase):
    """Regression tests for the ServiceImage admin inline dropdown rendering.

    Bug fixed 2026-08-19: ``DynamicServiceImageForm`` built per-group
    dropdown fields (``_opt_{slug}``) in ``__init__``, but
    ``ServiceImageInline`` had no ``get_fieldsets`` override — Django's
    default fieldset only listed ``Meta.fields`` (``["image", "order"]``),
    so the dropdowns never rendered in the admin change form.  The fix
    overrides ``get_fieldsets`` to inject the dynamic field names computed
    from the parent Service's option groups.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = get_user_model().objects.create_superuser(
            "imgadmin", "imgadmin@example.com", "pw-12345")
        # Two option groups on the women's service
        make_service_option(cls.womens_service, "Color", "Black", additional_price=0)
        make_service_option(cls.womens_service, "Color", "Brown", additional_price=2000)
        make_service_option(cls.womens_service, "Length", "Shoulder", additional_price=0)
        make_service_option(cls.womens_service, "Length", "Waist", additional_price=5000)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_dropdown_fields_render_in_admin_change_form(self):
        """The ``_opt_color`` and ``_opt_length`` select fields must appear
        in the Service admin change form's ServiceImage inline."""
        response = self.client.get(
            "/admin/services/service/%d/change/" % self.womens_service.pk)
        self.assertEqual(response.status_code, 200)
        # Admin inline prefixes field names (e.g. ``images-0-_opt_color``),
        # so we check for the field name as a substring.
        self.assertContains(response, "_opt_color")
        self.assertContains(response, "_opt_length")
        # Both the existing form (index 0) and the empty/add form
        # (__prefix__) must render the dropdowns.
        self.assertContains(response, "images-0-_opt_color")
        self.assertContains(response, "images-__prefix__-_opt_color")

    def test_dropdown_includes_option_values(self):
        """Dropdown option labels include the option values."""
        response = self.client.get(
            "/admin/services/service/%d/change/" % self.womens_service.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Black")
        self.assertContains(response, "Brown")
        self.assertContains(response, "Shoulder")
        self.assertContains(response, "Waist")

    def test_service_without_options_renders_without_dropdowns(self):
        """A Service with no options must still render the inline — no
        crash, no orphan ``_opt_`` fields."""
        response = self.client.get(
            "/admin/services/service/%d/change/" % self.mens_service.pk)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="_opt_')
