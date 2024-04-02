import base64
import hashlib
import os
import zipfile
from contextlib import contextmanager
from io import BytesIO

from selenium.common.exceptions import (InvalidArgumentException,
                                        WebDriverException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.html5.application_cache import ApplicationCache
from selenium.webdriver.common.utils import keys_to_typing
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.errorhandler import ErrorHandler
from selenium.webdriver.remote.file_detector import (
    LocalFileDetector,
    FileDetector,
)
from selenium.webdriver.remote.mobile import Mobile
from selenium.webdriver.remote.switch_to import SwitchTo
from selenium.webdriver.remote.webelement import isDisplayed_js, getAttribute_js

from arsenic.clients import Client
from arsenic.connection import RemoteConnection


class RemoteWebElement:
    def __init__(self, parent, id_, w3c=False):
        self._parent = parent
        self._id = id_
        self._w3c = w3c

    def __repr__(self):
        return '<{0.__module__}.{0.__name__} (session="{1}", element="{2}")>'.format(
            type(self), self._parent.session_id, self._id)

    async def get_tag_name(self):
        """This element's ``tagName`` property."""
        return (await self._execute(Command.GET_ELEMENT_TAG_NAME))['value']

    async def get_text(self):
        """The text of the element."""
        return (await self._execute(Command.GET_ELEMENT_TEXT))['value']

    async def click(self):
        """Clicks the element."""
        await self._execute(Command.CLICK_ELEMENT)

    async def submit(self):
        """Submits a form."""
        if self._w3c:
            form = await self.find_element(By.XPATH, "./ancestor-or-self::form")
            await self._parent.execute_script(
                "var e = arguments[0].ownerDocument.createEvent('Event');"
                "e.initEvent('submit', true, true);"
                "if (arguments[0].dispatchEvent(e)) { arguments[0].submit() }", form)
        else:
            await self._execute(Command.SUBMIT_ELEMENT)

    async def clear(self):
        """Clears the text if it's a text entry element."""
        await self._execute(Command.CLEAR_ELEMENT)

    async def get_property(self, name):
        """
        Gets the given property of the element.

        :Args:
            - name - Name of the property to retrieve.

        Example::

            # Check if the "active" CSS class is applied to an element.
            text_length = target_element.get_property("text_length")
        """
        try:
            return (await self._execute(Command.GET_ELEMENT_PROPERTY, {"name": name}))["value"]
        except WebDriverException:
            # if we hit an end point that doesnt understand getElementProperty lets fake it
            return await self.parent.execute_script('return arguments[0][arguments[1]]', self, name)

    async def get_attribute(self, name):
        """Gets the given attribute or property of the element.

        This method will first try to return the value of a property with the
        given name. If a property with that name doesn't exist, it returns the
        value of the attribute with the same name. If there's no attribute with
        that name, ``None`` is returned.

        Values which are considered truthy, that is equals "true" or "false",
        are returned as booleans.  All other non-``None`` values are returned
        as strings.  For attributes or properties which do not exist, ``None``
        is returned.

        :Args:
            - name - Name of the attribute/property to retrieve.

        Example::

            # Check if the "active" CSS class is applied to an element.
            is_active = "active" in target_element.get_attribute("class")

        """

        attributeValue = ''
        if self._w3c:
            attributeValue = await self.parent.execute_script(
                "return (%s).apply(null, arguments);" % getAttribute_js,
                self, name)
        else:
            resp = await self._execute(Command.GET_ELEMENT_ATTRIBUTE, {'name': name})
            attributeValue = resp.get('value')
            if attributeValue is not None:
                if name != 'value' and attributeValue.lower() in ('true', 'false'):
                    attributeValue = attributeValue.lower()
        return attributeValue

    async def is_selected(self):
        """Returns whether the element is selected.

        Can be used to check if a checkbox or radio button is selected.
        """
        return (await self._execute(Command.IS_ELEMENT_SELECTED))['value']

    async def is_enabled(self):
        """Returns whether the element is enabled."""
        return (await self._execute(Command.IS_ELEMENT_ENABLED))['value']

    async def find_element_by_id(self, id_):
        """Finds element within this element's children by ID.

        :Args:
            - id\_ - ID of child element to locate.
        """
        return await self.find_element(by=By.ID, value=id_)

    async def find_elements_by_id(self, id_):
        """Finds a list of elements within this element's children by ID.

        :Args:
            - id\_ - Id of child element to find.
        """
        return await self.find_elements(by=By.ID, value=id_)

    async def find_element_by_name(self, name):
        """Finds element within this element's children by name.

        :Args:
            - name - name property of the element to find.
        """
        return await self.find_element(by=By.NAME, value=name)

    async def find_elements_by_name(self, name):
        """Finds a list of elements within this element's children by name.

        :Args:
            - name - name property to search for.
        """
        return await self.find_elements(by=By.NAME, value=name)

    async def find_element_by_link_text(self, link_text):
        """Finds element within this element's children by visible link text.

        :Args:
            - link_text - Link text string to search for.
        """
        return await self.find_element(by=By.LINK_TEXT, value=link_text)

    async def find_elements_by_link_text(self, link_text):
        """Finds a list of elements within this element's children by visible link text.

        :Args:
            - link_text - Link text string to search for.
        """
        return await self.find_elements(by=By.LINK_TEXT, value=link_text)

    async def find_element_by_partial_link_text(self, link_text):
        """Finds element within this element's children by partially visible link text.

        :Args:
            - link_text - Link text string to search for.
        """
        return await self.find_element(by=By.PARTIAL_LINK_TEXT, value=link_text)

    async def find_elements_by_partial_link_text(self, link_text):
        """Finds a list of elements within this element's children by link text.

        :Args:
            - link_text - Link text string to search for.
        """
        return await self.find_elements(by=By.PARTIAL_LINK_TEXT, value=link_text)

    async def find_element_by_tag_name(self, name):
        """Finds element within this element's children by tag name.

        :Args:
            - name - name of html tag (eg: h1, a, span)
        """
        return await self.find_element(by=By.TAG_NAME, value=name)

    async def find_elements_by_tag_name(self, name):
        """Finds a list of elements within this element's children by tag name.

        :Args:
            - name - name of html tag (eg: h1, a, span)
        """
        return await self.find_elements(by=By.TAG_NAME, value=name)

    async def find_element_by_xpath(self, xpath):
        """Finds element by xpath.

        :Args:
            xpath - xpath of element to locate.  "//input[@class='myelement']"

        Note: The base path will be relative to this element's location.

        This will select the first link under this element.

        ::

            myelement.find_elements_by_xpath(".//a")

        However, this will select the first link on the page.

        ::

            myelement.find_elements_by_xpath("//a")

        """
        return await self.find_element(by=By.XPATH, value=xpath)

    async def find_elements_by_xpath(self, xpath):
        """Finds elements within the element by xpath.

        :Args:
            - xpath - xpath locator string.

        Note: The base path will be relative to this element's location.

        This will select all links under this element.

        ::

            myelement.find_elements_by_xpath(".//a")

        However, this will select all links in the page itself.

        ::

            myelement.find_elements_by_xpath("//a")

        """
        return await self.find_elements(by=By.XPATH, value=xpath)

    async def find_element_by_class_name(self, name):
        """Finds element within this element's children by class name.

        :Args:
            - name - class name to search for.
        """
        return await self.find_element(by=By.CLASS_NAME, value=name)

    async def find_elements_by_class_name(self, name):
        """Finds a list of elements within this element's children by class name.

        :Args:
            - name - class name to search for.
        """
        return await self.find_elements(by=By.CLASS_NAME, value=name)

    async def find_element_by_css_selector(self, css_selector):
        """Finds element within this element's children by CSS selector.

        :Args:
            - css_selector - CSS selctor string, ex: 'a.nav#home'
        """
        return await self.find_element(by=By.CSS_SELECTOR, value=css_selector)

    async def find_elements_by_css_selector(self, css_selector):
        """Finds a list of elements within this element's children by CSS selector.

        :Args:
            - css_selector - CSS selctor string, ex: 'a.nav#home'
        """
        return await self.find_elements(by=By.CSS_SELECTOR, value=css_selector)

    async def send_keys(self, *value):
        """Simulates typing into the element.

        :Args:
            - value - A string for typing, or setting form fields.  For setting
              file inputs, this could be a local file path.

        Use this to send simple key events or to fill out form fields::

            form_textfield = driver.find_element_by_name('username')
            form_textfield.send_keys("admin")

        This can also be used to set file inputs.

        ::

            file_input = driver.find_element_by_name('profilePic')
            file_input.send_keys("path/to/profilepic.gif")
            # Generally it's better to wrap the file path in one of the methods
            # in os.path to return the actual path to support cross OS testing.
            # file_input.send_keys(os.path.abspath("path/to/profilepic.gif"))

        """
        # transfer file to another machine only if remote driver is used
        # the same behaviour as for java binding
        if self.parent._is_remote:
            local_file = self.parent.file_detector.is_local_file(*value)
            if local_file is not None:
                value = await self._upload(local_file)

        await self._execute(Command.SEND_KEYS_TO_ELEMENT,
                      {'text': "".join(keys_to_typing(value)),
                       'value': keys_to_typing(value)})

    # RenderedWebElement Items
    async def is_displayed(self):
        """Whether the element is visible to a user."""
        # Only go into this conditional for browsers that don't use the atom themselves
        if self._w3c and self.parent.capabilities['browserName'] == 'safari':
            return await self.parent.execute_script(
                "return (%s).apply(null, arguments);" % isDisplayed_js,
                self)
        else:
            return (await self._execute(Command.IS_ELEMENT_DISPLAYED))['value']

    async def get_location_once_scrolled_into_view(self):
        """THIS PROPERTY MAY CHANGE WITHOUT WARNING. Use this to discover
        where on the screen an element is so that we can click it. This method
        should cause the element to be scrolled into view.

        Returns the top lefthand corner location on the screen, or ``None`` if
        the element is not visible.

        """
        if self._w3c:
            old_loc = (await self._execute(Command.W3C_EXECUTE_SCRIPT, {
                'script': "arguments[0].scrollIntoView(true); return arguments[0].getBoundingClientRect()",
                'args': [self]}))['value']
            return {"x": round(old_loc['x']),
                    "y": round(old_loc['y'])}
        else:
            return (await self._execute(Command.GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW))['value']

    async def get_size(self):
        """The size of the element."""
        size = {}
        if self._w3c:
            size = (await self._execute(Command.GET_ELEMENT_RECT))['value']
        else:
            size = (await self._execute(Command.GET_ELEMENT_SIZE))['value']
        new_size = {"height": size["height"],
                    "width": size["width"]}
        return new_size

    async def value_of_css_property(self, property_name):
        """The value of a CSS property."""
        return (await self._execute(Command.GET_ELEMENT_VALUE_OF_CSS_PROPERTY, {
            'propertyName': property_name}))['value']

    async def get_location(self):
        """The location of the element in the renderable canvas."""
        if self._w3c:
            old_loc = (await self._execute(Command.GET_ELEMENT_RECT))['value']
        else:
            old_loc = (await self._execute(Command.GET_ELEMENT_LOCATION))['value']
        new_loc = {"x": round(old_loc['x']),
                   "y": round(old_loc['y'])}
        return new_loc

    async def get_rect(self):
        """A dictionary with the size and location of the element."""
        return (await self._execute(Command.GET_ELEMENT_RECT))['value']

    async def get_screenshot_as_base64(self):
        """
        Gets the screenshot of the current element as a base64 encoded string.

        :Usage:
            img_b64 = element.screenshot_as_base64
        """
        return (await self._execute(Command.ELEMENT_SCREENSHOT))['value']

    async def get_screenshot_as_png(self):
        """
        Gets the screenshot of the current element as a binary data.

        :Usage:
            element_png = element.screenshot_as_png
        """
        return base64.b64decode((await self.screenshot_as_base64).encode('ascii'))

    async def get_screenshot(self, filename):
        """
        Gets the screenshot of the current element. Returns False if there is
           any IOError, else returns True. Use full paths in your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to.

        :Usage:
            element.screenshot('/Screenshots/foo.png')
        """
        png = await self.get_screenshot_as_png()
        try:
            with open(filename, 'wb') as f:
                f.write(png)
        except IOError:
            return False
        finally:
            del png
        return True

    @property
    def parent(self):
        """Internal reference to the WebDriver instance this element was found from."""
        return self._parent

    @property
    def id(self):
        """Internal ID used by selenium.

        This is mainly for internal use. Simple use cases such as checking if 2
        webelements refer to the same element, can be done using ``==``::

            if element1 == element2:
                print("These 2 are equal")

        """
        return self._id

    def __eq__(self, element):
        return hasattr(element, 'id') and self._id == element.id

    def __ne__(self, element):
        return not self.__eq__(element)

    # Private Methods
    async def _execute(self, command, params=None):
        """Executes a command against the underlying HTML element.

        Args:
          command: The name of the command to _execute as a string.
          params: A dictionary of named parameters to send with the command.

        Returns:
          The command's JSON response loaded into a dictionary object.
        """
        if not params:
            params = {}
        params['id'] = self._id
        return await self._parent.execute(command, params)

    async def find_element(self, by=By.ID, value=None):
        if self._w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value

        return (await self._execute(Command.FIND_CHILD_ELEMENT,
                             {"using": by, "value": value}))['value']

    async def find_elements(self, by=By.ID, value=None):
        if self._w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value

        return (await self._execute(Command.FIND_CHILD_ELEMENTS,
                             {"using": by, "value": value}))['value']

    def __hash__(self):
        return int(hashlib.md5(self._id.encode('utf-8')).hexdigest(), 16)

    async def _upload(self, filename):
        fp = BytesIO()
        zipped = zipfile.ZipFile(fp, 'w', zipfile.ZIP_DEFLATED)
        zipped.write(filename, os.path.split(filename)[1])
        zipped.close()
        content = base64.encodebytes(fp.getvalue())
        if not isinstance(content, str):
            content = content.decode('utf-8')
        try:
            return (await self._execute(Command.UPLOAD_FILE, {'file': content}))['value']
        except WebDriverException as e:
            if "Unrecognized command: POST" in e.__str__():
                return filename
            elif "Command not found: POST " in e.__str__():
                return filename
            elif '{"status":405,"value":["GET","HEAD","DELETE"]}' in e.__str__():
                return filename
            else:
                raise e


class RemoteDriver:
    """
    Controls a browser by sending commands to a remote server.
    This server is expected to be running the WebDriver wire protocol
    as defined at
    https://github.com/SeleniumHQ/selenium/wiki/JsonWireProtocol

    :Attributes:
     - session_id - String ID of the browser session started and controlled by this WebDriver.
     - capabilities - Dictionaty of effective capabilities of this browser session as returned
         by the remote server. See https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities
     - command_executor - remote_connection.RemoteConnection object used to execute commands.
     - error_handler - errorhandler.ErrorHandler object used to handle errors.
    """

    _web_element_cls = RemoteWebElement

    def __init__(self,
                 client: Client,
                 *,
                 desired_capabilities,
                 command_executor='http://127.0.0.1:4444/wd/hub',
                 browser_profile=None, proxy=None,
                 file_detector=None):
        """
        Create a new driver that will issue commands using the wire protocol.

        :Args:
         - command_executor - Either a string representing URL of the remote server or a custom
             remote_connection.RemoteConnection object. Defaults to 'http://127.0.0.1:4444/wd/hub'.
         - desired_capabilities - A dictionary of capabilities to request when
             starting the browser session. Required parameter.
         - browser_profile - A selenium.webdriver.firefox.firefox_profile.FirefoxProfile object.
             Only used if Firefox is requested. Optional.
         - proxy - A selenium.webdriver.common.proxy.Proxy object. The browser session will
             be started with given proxy settings, if possible. Optional.
         - keep_alive - Whether to configure remote_connection.RemoteConnection to use
             HTTP keep-alive. Defaults to False.
         - file_detector - Pass custom file detector object during instantiation. If None,
             then default LocalFileDetector() will be used.
        """
        self.command_executor = command_executor
        if type(self.command_executor) is bytes or isinstance(self.command_executor, str):
            self.command_executor = RemoteConnection(
                client,
                remote_server_addr=command_executor
            )
        self._is_remote = True
        self.session_id = None
        self.capabilities = {}
        self.error_handler = ErrorHandler()
        self._switch_to = SwitchTo(self)
        self._mobile = Mobile(self)
        self.file_detector = file_detector or LocalFileDetector()
        self._browser_profile = browser_profile
        self._desired_capabilities  = desired_capabilities

    async def async_setup(self):
        await self.start_client()
        await self.command_executor.initialize()
        await self.start_session(self._desired_capabilities)

    @classmethod
    async def async_init(cls, client, **kwargs):
        instance = cls(client, **kwargs)
        await instance.async_setup()
        return instance

    def __repr__(self):
        return '<{0.__module__}.{0.__name__} (session="{1}")>'.format(
            type(self), self.session_id)

    @contextmanager
    def file_detector_context(self, file_detector_class, *args, **kwargs):
        """
        Overrides the current file detector (if necessary) in limited context.
        Ensures the original file detector is set afterwards.

        Example:

        with webdriver.file_detector_context(UselessFileDetector):
            someinput.send_keys('/etc/hosts')

        :Args:
         - file_detector_class - Class of the desired file detector. If the class is different
             from the current file_detector, then the class is instantiated with args and kwargs
             and used as a file detector during the duration of the context manager.
         - args - Optional arguments that get passed to the file detector class during
             instantiation.
         - kwargs - Keyword arguments, passed the same way as args.
        """
        last_detector = None
        if not isinstance(self.file_detector, file_detector_class):
            last_detector = self.file_detector
            self.file_detector = file_detector_class(*args, **kwargs)
        try:
            yield
        finally:
            if last_detector is not None:
                self.file_detector = last_detector

    @property
    def mobile(self):
        return self._mobile

    @property
    def name(self):
        """Returns the name of the underlying browser for this instance.

        :Usage:
         - driver.name
        """
        if 'browserName' in self.capabilities:
            return self.capabilities['browserName']
        else:
            raise KeyError('browserName not specified in session capabilities')

    async def start_client(self):
        """
        Called before starting a new session. This method may be overridden
        to define custom startup behavior.
        """
        pass

    async def stop_client(self):
        """
        Called after executing a quit command. This method may be overridden
        to define custom shutdown behavior.
        """
        pass

    async def start_session(self, capabilities):
        """
        Creates a new session with the desired capabilities.

        :Args:
         - browser_name - The name of the browser to request.
         - version - Which browser version to request.
         - platform - Which platform to request the browser on.
         - javascript_enabled - Whether the new session should support JavaScript.
         - browser_profile - A selenium.webdriver.firefox.firefox_profile.FirefoxProfile object. Only used if Firefox is requested.
        """
        if not isinstance(capabilities, dict):
            raise InvalidArgumentException("Capabilities must be a dictionary")
        w3c_caps = {"firstMatch": [], "alwaysMatch": {}}
        w3c_caps["alwaysMatch"].update(capabilities)
        parameters = {"capabilities": w3c_caps,
                      "desiredCapabilities": capabilities}
        response = await self.execute(Command.NEW_SESSION, parameters)
        if 'sessionId' not in response:
            response = response['value']
        self.session_id = response['sessionId']
        self.capabilities = response.get('value')

        # if capabilities is none we are probably speaking to
        # a W3C endpoint
        if self.capabilities is None:
            self.capabilities = response.get('capabilities')

        # Double check to see if we have a W3C Compliant browser
        self.w3c = response.get('status') is None

    def _wrap_value(self, value):
        if isinstance(value, dict):
            converted = {}
            for key, val in value.items():
                converted[key] = self._wrap_value(val)
            return converted
        elif isinstance(value, self._web_element_cls):
            return {'ELEMENT': value.id, 'element-6066-11e4-a52e-4f735466cecf': value.id}
        elif isinstance(value, list):
            return list(self._wrap_value(item) for item in value)
        else:
            return value

    def create_web_element(self, element_id):
        """Creates a web element with the specified `element_id`."""
        return self._web_element_cls(self, element_id, w3c=self.w3c)

    def _unwrap_value(self, value):
        if isinstance(value, dict) and ('ELEMENT' in value or 'element-6066-11e4-a52e-4f735466cecf' in value):
            wrapped_id = value.get('ELEMENT', None)
            if wrapped_id:
                return self.create_web_element(value['ELEMENT'])
            else:
                return self.create_web_element(value['element-6066-11e4-a52e-4f735466cecf'])

        elif isinstance(value, list):
            return list(self._unwrap_value(item) for item in value)
        else:
            return value

    async def execute(self, driver_command, params=None):
        """
        Sends a command to be executed by a command.CommandExecutor.

        :Args:
         - driver_command: The name of the command to execute as a string.
         - params: A dictionary of named parameters to send with the command.

        :Returns:
          The command's JSON response loaded into a dictionary object.
        """
        if self.session_id is not None:
            if not params:
                params = {'sessionId': self.session_id}
            elif 'sessionId' not in params:
                params['sessionId'] = self.session_id

        params = self._wrap_value(params)
        response = await self.command_executor.execute(driver_command, params)
        if response:
            self.error_handler.check_response(response)
            response['value'] = self._unwrap_value(
                response.get('value', None))
            return response
        # If the server doesn't send a response, assume the command was
        # a success
        return {'success': 0, 'value': None, 'sessionId': self.session_id}

    async def get(self, url):
        """
        Loads a web page in the current browser session.
        """
        await self.execute(Command.GET, {'url': url})

    async def title(self):
        """Returns the title of the current page.

        :Usage:
            driver.title
        """
        resp = await self.execute(Command.GET_TITLE)
        return resp['value'] if resp['value'] is not None else ""

    async def find_element_by_id(self, id_):
        """Finds an element by id.

        :Args:
         - id\_ - The id of the element to be found.

        :Usage:
            driver.find_element_by_id('foo')
        """
        return await self.find_element(by=By.ID, value=id_)

    async def find_elements_by_id(self, id_):
        """
        Finds multiple elements by id.

        :Args:
         - id\_ - The id of the elements to be found.

        :Usage:
            driver.find_elements_by_id('foo')
        """
        return await self.find_elements(by=By.ID, value=id_)

    async def find_element_by_xpath(self, xpath):
        """
        Finds an element by xpath.

        :Args:
         - xpath - The xpath locator of the element to find.

        :Usage:
            driver.find_element_by_xpath('//div/td[1]')
        """
        return await self.find_element(by=By.XPATH, value=xpath)

    async def find_elements_by_xpath(self, xpath):
        """
        Finds multiple elements by xpath.

        :Args:
         - xpath - The xpath locator of the elements to be found.

        :Usage:
            driver.find_elements_by_xpath("//div[contains(@class, 'foo')]")
        """
        return await self.find_elements(by=By.XPATH, value=xpath)

    async def find_element_by_link_text(self, link_text):
        """
        Finds an element by link text.

        :Args:
         - link_text: The text of the element to be found.

        :Usage:
            driver.find_element_by_link_text('Sign In')
        """
        return await self.find_element(by=By.LINK_TEXT, value=link_text)

    async def find_elements_by_link_text(self, text):
        """
        Finds elements by link text.

        :Args:
         - link_text: The text of the elements to be found.

        :Usage:
            driver.find_elements_by_link_text('Sign In')
        """
        return await self.find_elements(by=By.LINK_TEXT, value=text)

    async def find_element_by_partial_link_text(self, link_text):
        """
        Finds an element by a partial match of its link text.

        :Args:
         - link_text: The text of the element to partially match on.

        :Usage:
            driver.find_element_by_partial_link_text('Sign')
        """
        return await self.find_element(by=By.PARTIAL_LINK_TEXT, value=link_text)

    async def find_elements_by_partial_link_text(self, link_text):
        """
        Finds elements by a partial match of their link text.

        :Args:
         - link_text: The text of the element to partial match on.

        :Usage:
            driver.find_element_by_partial_link_text('Sign')
        """
        return await self.find_elements(by=By.PARTIAL_LINK_TEXT, value=link_text)

    async def find_element_by_name(self, name):
        """
        Finds an element by name.

        :Args:
         - name: The name of the element to find.

        :Usage:
            driver.find_element_by_name('foo')
        """
        return await self.find_element(by=By.NAME, value=name)

    async def find_elements_by_name(self, name):
        """
        Finds elements by name.

        :Args:
         - name: The name of the elements to find.

        :Usage:
            driver.find_elements_by_name('foo')
        """
        return await self.find_elements(by=By.NAME, value=name)

    async def find_element_by_tag_name(self, name):
        """
        Finds an element by tag name.

        :Args:
         - name: The tag name of the element to find.

        :Usage:
            driver.find_element_by_tag_name('foo')
        """
        return await self.find_element(by=By.TAG_NAME, value=name)

    async def find_elements_by_tag_name(self, name):
        """
        Finds elements by tag name.

        :Args:
         - name: The tag name the use when finding elements.

        :Usage:
            driver.find_elements_by_tag_name('foo')
        """
        return await self.find_elements(by=By.TAG_NAME, value=name)

    async def find_element_by_class_name(self, name):
        """
        Finds an element by class name.

        :Args:
         - name: The class name of the element to find.

        :Usage:
            driver.find_element_by_class_name('foo')
        """
        return await self.find_element(by=By.CLASS_NAME, value=name)

    async def find_elements_by_class_name(self, name):
        """
        Finds elements by class name.

        :Args:
         - name: The class name of the elements to find.

        :Usage:
            driver.find_elements_by_class_name('foo')
        """
        return await self.find_elements(by=By.CLASS_NAME, value=name)

    async def find_element_by_css_selector(self, css_selector):
        """
        Finds an element by css selector.

        :Args:
         - css_selector: The css selector to use when finding elements.

        :Usage:
            driver.find_element_by_css_selector('#foo')
        """
        return await self.find_element(by=By.CSS_SELECTOR, value=css_selector)

    async def find_elements_by_css_selector(self, css_selector):
        """
        Finds elements by css selector.

        :Args:
         - css_selector: The css selector to use when finding elements.

        :Usage:
            driver.find_elements_by_css_selector('.foo')
        """
        return await self.find_elements(by=By.CSS_SELECTOR, value=css_selector)

    async def execute_script(self, script, *args):
        """
        Synchronously Executes JavaScript in the current window/frame.

        :Args:
         - script: The JavaScript to execute.
         - \*args: Any applicable arguments for your JavaScript.

        :Usage:
            driver.execute_script('document.title')
        """
        converted_args = list(args)
        command = None
        if self.w3c:
            command = Command.W3C_EXECUTE_SCRIPT
        else:
            command = Command.EXECUTE_SCRIPT

        return (await self.execute(command, {
            'script': script,
            'args': converted_args}))['value']

    async def execute_async_script(self, script, *args):
        """
        Asynchronously Executes JavaScript in the current window/frame.

        :Args:
         - script: The JavaScript to execute.
         - \*args: Any applicable arguments for your JavaScript.

        :Usage:
            driver.execute_async_script('document.title')
        """
        converted_args = list(args)
        if self.w3c:
            command = Command.W3C_EXECUTE_SCRIPT_ASYNC
        else:
            command = Command.EXECUTE_ASYNC_SCRIPT

        return (await self.execute(command, {
            'script': script,
            'args': converted_args}))['value']

    async def get_current_url(self):
        """
        Gets the URL of the current page.

        :Usage:
            driver.current_url
        """
        return (await self.execute(Command.GET_CURRENT_URL))['value']

    async def get_page_source(self):
        """
        Gets the source of the current page.

        :Usage:
            driver.page_source
        """
        return (await self.execute(Command.GET_PAGE_SOURCE))['value']

    async def close(self):
        """
        Closes the current window.

        :Usage:
            driver.close()
        """
        await self.execute(Command.CLOSE)

    async def quit(self):
        """
        Quits the driver and closes every associated window.

        :Usage:
            driver.quit()
        """
        try:
            await self.execute(Command.QUIT)
        finally:
            await self.command_executor.finalize()
            await self.stop_client()

    async def get_current_window_handle(self):
        """
        Returns the handle of the current window.

        :Usage:
            driver.current_window_handle
        """
        if self.w3c:
            return (await self.execute(Command.W3C_GET_CURRENT_WINDOW_HANDLE))['value']
        else:
            return (await self.execute(Command.GET_CURRENT_WINDOW_HANDLE))['value']

    async def get_window_handles(self):
        """
        Returns the handles of all windows within the current session.

        :Usage:
            driver.window_handles
        """
        if self.w3c:
            return (await self.execute(Command.W3C_GET_WINDOW_HANDLES))['value']
        else:
            return (await self.execute(Command.GET_WINDOW_HANDLES))['value']

    async def maximize_window(self):
        """
        Maximizes the current window that webdriver is using
        """
        command = Command.MAXIMIZE_WINDOW
        if self.w3c:
            command = Command.W3C_MAXIMIZE_WINDOW
        await self.execute(command, {"windowHandle": "current"})

    @property
    def switch_to(self):
        raise NotImplementedError()
        return self._switch_to

    # Navigation
    async def back(self):
        """
        Goes one step backward in the browser history.

        :Usage:
            driver.back()
        """
        await self.execute(Command.GO_BACK)

    async def forward(self):
        """
        Goes one step forward in the browser history.

        :Usage:
            driver.forward()
        """
        await self.execute(Command.GO_FORWARD)

    async def refresh(self):
        """
        Refreshes the current page.

        :Usage:
            driver.refresh()
        """
        await self.execute(Command.REFRESH)

    # Options
    async def get_cookies(self):
        """
        Returns a set of dictionaries, corresponding to cookies visible in the current session.

        :Usage:
            driver.get_cookies()
        """
        return (await self.execute(Command.GET_ALL_COOKIES))['value']

    async def get_cookie(self, name):
        """
        Get a single cookie by name. Returns the cookie if found, None if not.

        :Usage:
            driver.get_cookie('my_cookie')
        """
        cookies = await self.get_cookies()
        for cookie in cookies:
            if cookie['name'] == name:
                return cookie
        return None

    async def delete_cookie(self, name):
        """
        Deletes a single cookie with the given name.

        :Usage:
            driver.delete_cookie('my_cookie')
        """
        await self.execute(Command.DELETE_COOKIE, {'name': name})

    async def delete_all_cookies(self):
        """
        Delete all cookies in the scope of the session.

        :Usage:
            driver.delete_all_cookies()
        """
        await self.execute(Command.DELETE_ALL_COOKIES)

    async def add_cookie(self, cookie_dict):
        """
        Adds a cookie to your current session.

        :Args:
         - cookie_dict: A dictionary object, with required keys - "name" and "value";
            optional keys - "path", "domain", "secure", "expiry"

        Usage:
            driver.add_cookie({'name' : 'foo', 'value' : 'bar'})
            driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/'})
            driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/', 'secure':True})

        """
        await self.execute(Command.ADD_COOKIE, {'cookie': cookie_dict})

    # Timeouts
    async def implicitly_wait(self, time_to_wait):
        """
        Sets a sticky timeout to implicitly wait for an element to be found,
           or a command to complete. This method only needs to be called one
           time per session. To set the timeout for calls to
           execute_async_script, see set_script_timeout.

        :Args:
         - time_to_wait: Amount of time to wait (in seconds)

        :Usage:
            driver.implicitly_wait(30)
        """
        if self.w3c:
            await self.execute(Command.SET_TIMEOUTS, {
                'implicit': int(float(time_to_wait) * 1000)})
        else:
            await self.execute(Command.IMPLICIT_WAIT, {
                'ms': float(time_to_wait) * 1000})

    async def set_script_timeout(self, time_to_wait):
        """
        Set the amount of time that the script should wait during an
           execute_async_script call before throwing an error.

        :Args:
         - time_to_wait: The amount of time to wait (in seconds)

        :Usage:
            driver.set_script_timeout(30)
        """
        if self.w3c:
            await self.execute(Command.SET_TIMEOUTS, {
                'script': int(float(time_to_wait) * 1000)})
        else:
            await self.execute(Command.SET_SCRIPT_TIMEOUT, {
                'ms': float(time_to_wait) * 1000})

    async def set_page_load_timeout(self, time_to_wait):
        """
        Set the amount of time to wait for a page load to complete
           before throwing an error.

        :Args:
         - time_to_wait: The amount of time to wait

        :Usage:
            driver.set_page_load_timeout(30)
        """
        try:
            await self.execute(Command.SET_TIMEOUTS, {
                'pageLoad': int(float(time_to_wait) * 1000)})
        except WebDriverException:
            await self.execute(Command.SET_TIMEOUTS, {
                'ms': float(time_to_wait) * 1000,
                'type': 'page load'})

    async def find_element(self, by=By.ID, value=None):
        """
        'Private' method used by the find_element_by_* methods.

        :Usage:
            Use the corresponding find_element_by_* instead of this.

        :rtype: WebElement
        """
        if self.w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value
        return (await self.execute(Command.FIND_ELEMENT, {
            'using': by,
            'value': value}))['value']

    async def find_elements(self, by=By.ID, value=None):
        """
        'Private' method used by the find_elements_by_* methods.

        :Usage:
            Use the corresponding find_elements_by_* instead of this.

        :rtype: list of WebElement
        """
        if self.w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value

        return (await self.execute(Command.FIND_ELEMENTS, {
            'using': by,
            'value': value}))['value']

    @property
    def desired_capabilities(self):
        """
        returns the drivers current desired capabilities being used
        """
        return self.capabilities

    async def get_screenshot_as_file(self, filename):
        """
        Gets the screenshot of the current window. Returns False if there is
           any IOError, else returns True. Use full paths in your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to.

        :Usage:
            driver.get_screenshot_as_file('/Screenshots/foo.png')
        """
        png = await self.get_screenshot_as_png()
        try:
            with open(filename, 'wb') as f:
                f.write(png)
        except IOError:
            return False
        finally:
            del png
        return True

    async def save_screenshot(self, filename):
        """
        Gets the screenshot of the current window. Returns False if there is
           any IOError, else returns True. Use full paths in your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to.

        :Usage:
            driver.save_screenshot('/Screenshots/foo.png')
        """
        return await self.get_screenshot_as_file(filename)

    async def get_screenshot_as_png(self):
        """
        Gets the screenshot of the current window as a binary data.

        :Usage:
            driver.get_screenshot_as_png()
        """
        return base64.b64decode(await self.get_screenshot_as_base64().encode('ascii'))

    async def get_screenshot_as_base64(self):
        """
        Gets the screenshot of the current window as a base64 encoded string
           which is useful in embedded images in HTML.

        :Usage:
            driver.get_screenshot_as_base64()
        """
        return (await self.execute(Command.SCREENSHOT))['value']

    async def set_window_size(self, width, height, windowHandle='current'):
        """
        Sets the width and height of the current window. (window.resizeTo)

        :Args:
         - width: the width in pixels to set the window to
         - height: the height in pixels to set the window to

        :Usage:
            driver.set_window_size(800,600)
        """
        command = Command.SET_WINDOW_SIZE
        if self.w3c:
            command = Command.W3C_SET_WINDOW_SIZE
        await self.execute(command, {
            'width': int(width),
            'height': int(height),
            'windowHandle': windowHandle})

    async def get_window_size(self, windowHandle='current'):
        """
        Gets the width and height of the current window.

        :Usage:
            driver.get_window_size()
        """
        command = Command.GET_WINDOW_SIZE
        if self.w3c:
            command = Command.W3C_GET_WINDOW_SIZE
        size = await self.execute(command, {'windowHandle': windowHandle})

        if size.get('value', None) is not None:
            return size['value']
        else:
            return size

    async def set_window_position(self, x, y, windowHandle='current'):
        """
        Sets the x,y position of the current window. (window.moveTo)

        :Args:
         - x: the x-coordinate in pixels to set the window position
         - y: the y-coordinate in pixels to set the window position

        :Usage:
            driver.set_window_position(0,0)
        """
        if self.w3c:
            return await self.execute(Command.W3C_SET_WINDOW_POSITION, {
                                'x': int(x),
                                'y': int(y)
                                })
        else:
            await self.execute(Command.SET_WINDOW_POSITION,
                         {
                             'x': int(x),
                             'y': int(y),
                             'windowHandle': windowHandle
                         })

    async def get_window_position(self, windowHandle='current'):
        """
        Gets the x,y position of the current window.

        :Usage:
            driver.get_window_position()
        """
        if self.w3c:
            return (await self.execute(Command.W3C_GET_WINDOW_POSITION))['value']
        else:
            return (await self.execute(Command.GET_WINDOW_POSITION, {
                'windowHandle': windowHandle}))['value']

    async def get_window_rect(self):
        """
        Gets the x, y coordinates of the window as well as height and width of
        the current window.

        :Usage:
            driver.get_window_rect()
        """
        return (await self.execute(Command.GET_WINDOW_RECT))['value']

    async def set_window_rect(self, x=None, y=None, width=None, height=None):
        """
        Sets the x, y coordinates of the window as well as height and width of
        the current window.

        :Usage:
            driver.set_window_rect(x=10, y=10)
            driver.set_window_rect(width=100, height=200)
            driver.set_window_rect(x=10, y=10, width=100, height=200)
        """
        if (x is None and y is None) and (height is None and width is None):
            raise InvalidArgumentException("x and y or height and width need values")

        return (await self.execute(Command.SET_WINDOW_RECT, {"x": x, "y": y,
                                                      "width": width,
                                                      "height": height}))['value']

    @property
    def file_detector(self):
        return self._file_detector

    @file_detector.setter
    def file_detector(self, detector):
        """
        Set the file detector to be used when sending keyboard input.
        By default, this is set to a file detector that does nothing.

        see FileDetector
        see LocalFileDetector
        see UselessFileDetector

        :Args:
         - detector: The detector to use. Must not be None.
        """
        if detector is None:
            raise WebDriverException("You may not set a file detector that is null")
        if not isinstance(detector, FileDetector):
            raise WebDriverException("Detector has to be instance of FileDetector")
        self._file_detector = detector

    async def get_orientation(self):
        """
        Gets the current orientation of the device

        :Usage:
            orientation = driver.orientation
        """
        return (await self.execute(Command.GET_SCREEN_ORIENTATION))['value']

    async def set_orientation(self, value):
        """
        Sets the current orientation of the device

        :Args:
         - value: orientation to set it to.

        :Usage:
            driver.orientation = 'landscape'
        """
        allowed_values = ['LANDSCAPE', 'PORTRAIT']
        if value.upper() in allowed_values:
            await self.execute(Command.SET_SCREEN_ORIENTATION, {'orientation': value})
        else:
            raise WebDriverException("You can only set the orientation to 'LANDSCAPE' and 'PORTRAIT'")

    @property
    def application_cache(self):
        """ Returns a ApplicationCache Object to interact with the browser app cache"""
        return ApplicationCache(self)

    async def get_log_types(self):
        """
        Gets a list of the available log types

        :Usage:
            driver.log_types
        """
        return (await self.execute(Command.GET_AVAILABLE_LOG_TYPES))['value']

    async def get_log(self, log_type):
        """
        Gets the log for a given log type

        :Args:
         - log_type: type of log that which will be returned

        :Usage:
            driver.get_log('browser')
            driver.get_log('driver')
            driver.get_log('client')
            driver.get_log('server')
        """
        return (await self.execute(Command.GET_LOG, {'type': log_type}))['value']
