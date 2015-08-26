from uber.common import *
from hotel._version import __version__
from hotel.config import *
from hotel.models import *
from hotel.automated_emails import *

static_overrides(join(hotel_config['module_root'], 'static'))
template_overrides(join(hotel_config['module_root'], 'templates'))
mount_site_sections(hotel_config['module_root'])
