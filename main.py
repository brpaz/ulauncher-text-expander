"""Ulauncher extension main class """

import sys
import os
import logging
import subprocess
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener

# # pylint: disable=line-too-long
from ulauncher.api.shared.event import KeywordQueryEvent, PreferencesEvent, PreferencesUpdateEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.config import CONFIG_DIR
from lib.text_expander import TextExpander

LOGGER = logging.getLogger(__name__)

PLACEHOLDER_SCRIPTS_PATH = os.path.join(os.path.dirname(__file__), 'scripts',
                                        'placeholders.py')


class TextExpanderExtension(Extension):
    """ Main extension class """

    def __init__(self):
        """ init method """
        super(TextExpanderExtension, self).__init__()
        self.expansions_service = TextExpander(
            self.get_default_expansions_dir())
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent,
                       PreferencesUpdateEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

    def get_default_expansions_dir(self):
        """ Returns the place to look for text expansions"""
        return os.path.join(CONFIG_DIR, 'ext_preferences', 'text-expander',
                            'expansions')

    def show_empty_results_message(self):
        """ shows empty message """
        return RenderResultListAction([
            ExtensionResultItem(icon='images/icon.png',
                                name='No text expansions found for your query',
                                on_enter=HideWindowAction())
        ])

    def show_expansions_list(self, expansions):
        """ Shows the expansions list """

        items = []

        for item in expansions[:8]:
            items.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name=item['normalized_name'],
                    description='Select to fill placeholders and copy the contents to the clipboard',
                    on_enter=ExtensionCustomAction(item, keep_app_open=True)))

        return RenderResultListAction(items)


class KeywordQueryEventListener(EventListener):
    """ Handles Keyboard input """

    def on_event(self, event, extension):
        """ Handles the event """
        expansions = extension.expansions_service.find(event.get_argument())

        if not expansions:
            return extension.show_empty_results_message()

        return extension.show_expansions_list(expansions)


class PreferencesEventListener(EventListener):
    """
    Listener for prefrences event.
    It is triggered on the extension start with the configured preferences
    """

    def on_event(self, event, extension):
        if event.preferences["expansions_dir"] != "":
            extension.expansions_service.set_expansions_dir(
                os.path.expanduser(event.preferences['expansions_dir']))
        else:
            extension.expansions_service.set_expansions_dir(
                os.path.expanduser(extension.get_default_expansions_dir()))


class PreferencesUpdateEventListener(EventListener):
    """
    Listener for "Preferences Update" event.
    It is triggered when the user changes any setting in preferences window
    """

    def on_event(self, event, extension):
        if event.id == 'expansions_dir':
            if event.new_value != "":
                extension.expansions_service.set_expansions_dir(
                    event.new_value)
            else:
                extension.expansions_service.set_expansions_dir(
                    extension.get_default_expansions_dir())


class ItemEnterEventListener(EventListener):
    """ Handles item enter """

    def on_event(self, event, extension):
        data = event.get_data()
        cmd = f"{sys.executable} {PLACEHOLDER_SCRIPTS_PATH} {data['path']} "

        process = subprocess.Popen(cmd,
                                   shell=True,
                                   stdin=None,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   close_fds=True)

        (out, err) = process.communicate()

        if process.returncode != 0:
            LOGGER.error(err)

        out = out.decode('utf-8')

        return CopyToClipboardAction(out)


if __name__ == '__main__':
    TextExpanderExtension().run()
