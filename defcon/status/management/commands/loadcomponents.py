"""Component commands."""
from django.core.management import base
from django.conf import settings

from defcon.status import models


class Command(base.BaseCommand):
    """Load components from settings."""

    help = 'Load components from settings'

    def add_arguments(self, _):
        """Add arguments."""
        pass

    def handle(self, *args, **options):
        """Run the command."""
        existing_components = set(
            models.Component.objects.all().values_list('id', flat=True))
        updated_components = set()

        components = sorted(settings.DEFCON_COMPONENTS.items())
        for cid, component in components:
            self.add_component(cid, component)
            updated_components.add(cid)

        removed_components = existing_components - updated_components
        for cid in removed_components:
            models.Component.objects.filter(id=cid).delete()
            print('Removed %s' % cid)

    def add_component(self, cid, component):
        """Add one component."""
        plugins = component['plugins']
        del component['plugins']
        component_obj, created = models.Component.objects.update_or_create(
            id=cid,
            defaults=component
        )

        action = 'Created' if created else 'Updated'
        print('%s %s' % (action, component_obj))
        component_obj.save()

        existing_plugins = set(
            component_obj.plugins.values_list('plugin__id', flat=True))
        updated_plugins = set()

        plugins = sorted(plugins.items())
        for plugin_id, config in plugins:
            self.configure_plugin(component_obj, plugin_id, config)
            updated_plugins.add(plugin_id)

        removed_plugins = existing_plugins - updated_plugins
        for plugin_id in removed_plugins:
            component_obj.plugins.filter(plugin__id=plugin_id).delete()
            print('Removed %s:%s' % (component_obj.name, plugin_id))

    def configure_plugin(self, component_obj, plugin_id, config):
        """Configure a plugin for a component."""
        try:
            plugin_obj = models.Plugin.objects.get(id=plugin_id)
        except models.Plugin.DoesNotExist:
            raise base.CommandError('Plugin "%s" does not exist' % plugin_id)

        pinstance_obj, created = component_obj.plugins.update_or_create(
            plugin=plugin_obj, defaults={'config': config}
        )
        pinstance_obj.save()

        action = 'Created' if created else 'Updated'
        print('%s %s:%s config' % (action, component_obj.name, plugin_obj.name))