def MARA_CONFIG_MODULES():
    from . import config
    return [config]


def MARA_CLICK_COMMANDS():
    from . import cli
    return [cli.create_mondrian_schema]


def MARA_FLASK_BLUEPRINTS():
    from . import views
    return [views.blueprint]


def MARA_AUTOMIGRATE_SQLALCHEMY_MODELS():
    return []


def MARA_ACL_RESOURCES():
    from . import views
    return {
        'Metadata': views.acl_resource_metadata
    }


def MARA_NAVIGATION_ENTRIES():
    from . import views
    return {
        'Metadata': views.metadata_navigation_entry()
    }

