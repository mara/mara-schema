def MARA_CONFIG_MODULES():
    from . import config
    return [config]


def MARA_CLICK_COMMANDS():
    return []


def MARA_FLASK_BLUEPRINTS():
    from .ui import views
    return [views.blueprint]


def MARA_AUTOMIGRATE_SQLALCHEMY_MODELS():
    return []


def MARA_ACL_RESOURCES():
    from .ui import views
    return {
        'Schema': views.acl_resource_schema
    }


def MARA_NAVIGATION_ENTRIES():
    from .ui import views
    return {
        'Schema': views.schema_navigation_entry()
    }

