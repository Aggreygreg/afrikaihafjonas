from django.shortcuts import render, get_object_or_404  # <-- FIXED IMPORT
from django.db.models import Q
from .models import Service, ParentCategory, ServiceCategory

def service_list_view(request):
    # 1. Fetch parent categories for reference
    parent_categories = ParentCategory.objects.all()
    
    # 2. Get currently selected gender (default to "Women's Braids")
    gender_name = request.GET.get('gender', "Women's Braids")
    active_parent = parent_categories.filter(name__icontains=gender_name).first()
    
    # 3. Base Queryset (optimized loading of foreign keys + images)
    services = Service.objects.all().select_related(
        'category__parent'
    ).prefetch_related('images')
    
    # 4. Filter by Gender (Parent Category)
    if active_parent:
        services = services.filter(category__parent=active_parent)
        # Only show subcategories belonging to the active gender in the filter menu
        subcategories = ServiceCategory.objects.filter(parent=active_parent)
    else:
        subcategories = ServiceCategory.objects.none()

    # 5. Search Filter (Title & Description)
    search_query = request.GET.get('q', '').strip()
    if search_query:
        services = services.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    # 6. Braid Type (Subcategory) Filter
    subcategory_id = request.GET.get('category', '')
    if subcategory_id and subcategory_id.isdigit():
        services = services.filter(category_id=int(subcategory_id))

    # 7. Numeric Price Filters (Min & Max)
    price_min = request.GET.get('price_min', '').strip()
    if price_min and price_min.isdigit():
        services = services.filter(base_price__gte=int(price_min))

    price_max = request.GET.get('price_max', '').strip()
    if price_max and price_max.isdigit():
        services = services.filter(base_price__lte=int(price_max))

    # 8. Duration Filter (Max Duration)
    duration_max = request.GET.get('duration_max', '')
    if duration_max and duration_max.isdigit():
        services = services.filter(duration_minutes__lte=int(duration_max))

    # 8b. Discounted Only Filter
    discounted_only = request.GET.get('discounted_only', '')
    if discounted_only:
        services = services.filter(discount_percentage__gt=0)

    # 9. Sort Options
    sort_by = request.GET.get('sort_by', 'popular')
    if sort_by == 'popular':
        services = services.order_by('-is_popular', 'title')
    elif sort_by == 'price_asc':
        services = services.order_by('base_price')
    elif sort_by == 'price_desc':
        services = services.order_by('-base_price')
    elif sort_by == 'newest':
        services = services.order_by('-id')
    elif sort_by == 'discount':
        services = services.filter(discount_percentage__gt=0).order_by('-discount_percentage')

    context = {
        'services': services,
        'parent_categories': parent_categories,
        'subcategories': subcategories,
        'active_gender': gender_name,
        'search_query': search_query,
        'selected_category': subcategory_id,
        'selected_price_min': price_min,
        'selected_price_max': price_max,
        'selected_duration_max': duration_max,
        'selected_sort_by': sort_by,
        'selected_discounted': discounted_only,
    }

    # If it's an HTMX request, render only the partial template
    if request.headers.get('HX-Request'):
        return render(request, 'services/partials/service_grid.html', context)
        
    return render(request, 'services/service_list.html', context)

def service_detail_view(request, pk):
    """
    Displays the detailed page for a single service.
    """
    service = get_object_or_404(
        Service.objects.prefetch_related(
            'images__linked_options', 'options'
        ),
        pk=pk
    )
    
    # Group the options by 'group_name' for the template
    options_grouped = {}
    for option in service.options.all():
        if option.group_name not in options_grouped:
            options_grouped[option.group_name] = []
        options_grouped[option.group_name].append(option)
    
    context = {
        'service': service,
        'grouped_options': options_grouped,
    }
    return render(request, 'services/service_detail.html', context)