from .models import SiteConfiguration

def site_config(request):
    """
    Makes the SiteConfiguration object available to all templates
    as a global variable named 'config'.
    """
    try:
        config = SiteConfiguration.objects.get()
    except SiteConfiguration.DoesNotExist:
        # In case the object hasn't been created in the admin yet
        config = None
    
    return {'config': config}