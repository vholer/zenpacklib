***********************
Create a Modeler Plugin
***********************

Now that we've created a `WundergroundLocation` component type, we need to
create a modeler plugin to create locations in the database. We're dealing with
a custom HTTP API, so we'll want to base our modeler plugin on the
`PythonPlugin` class. This gives us full control of both the collection and
processing of the modeling data.

The modeler plugin will pass each location the user has specified in the
`zWundergroundLocations` property to Weather Underground's `AutoComplete` API to
retrieve some basic information about the location, and very importantly the `l`
(*link*) that uniquely identifies the location. The *link* will later be used to
monitor the alerts and conditions for the location.

Use the following steps to create our modeler plugin.

1. Make the directory that will contain our modeler plugin.

   .. code-block:: bash

      mkdir -p $ZP_DIR/modeler/plugins/WeatherUnderground

2. Create ``__init__.py`` or *dunder-init* files.

   .. code-block:: bash

      touch $ZP_DIR/modeler/__init__.py
      touch $ZP_DIR/modeler/plugins/__init__.py
      touch $ZP_DIR/modeler/plugins/WeatherUnderground/__init__.py

   These empty ``__init__.py`` files are mandatory if we ever expect Python to
   import modules from these directories.

3. Create ``$ZP_DIR/modeler/plugins/WeatherUnderground/Locations.py`` with the
   following contents.

   .. code-block:: python

      """Models locations using the Weather Underground API."""
      
      # stdlib Imports
      import json
      
      # Twisted Imports
      from twisted.internet.defer import inlineCallbacks, returnValue
      from twisted.web.client import getPage
      
      # Zenoss Imports
      from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
      
      
      class Locations(PythonPlugin):
      
          """Weather Underground locations modeler plugin."""
      
          relname = 'wundergroundLocations'
          modname = 'ZenPacks.training.WeatherUnderground.WundergroundLocation'
      
          requiredProperties = (
              'zWundergroundAPIKey',
              'zWundergroundLocations',
              )
      
          deviceProperties = PythonPlugin.deviceProperties + requiredProperties
      
          @inlineCallbacks
          def collect(self, device, log):
              """Asynchronously collect data from device. Return a deferred."""
              log.info("%s: collecting data", device.id)
      
              apikey = getattr(device, 'zWundergroundAPIKey', None)
              if not apikey:
                  log.error(
                      "%s: %s not set. Get one from http://www.wunderground.com/weather/api",
                      device.id,
                      'zWundergroundAPIKey')
      
                  returnValue(None)
      
              locations = getattr(device, 'zWundergroundLocations', None)
              if not locations:
                  log.error(
                      "%s: %s not set.",
                      device.id,
                      'zWundergroundLocations')
      
                  returnValue(None)
      
              rm = self.relMap()
      
              for location in locations:
                  try:
                      response = yield getPage(
                          'http://autocomplete.wunderground.com/aq?query={query}'
                          .format(query=location))
      
                      response = json.loads(response)
                  except Exception, e:
                      log.error(
                          "%s: %s", device.id, e)
      
                      returnValue(None)
      
                  for result in response['RESULTS']:
                      rm.append(self.objectMap({
                          'id': self.prepId(result['zmw']),
                          'title': result['name'],
                          'api_link': result['l'],
                          'country_code': result['c'],
                          'timezone': result['tzs'],
                          }))
      
              returnValue(rm)
      
          def process(self, device, results, log):
              """Process results. Return iterable of datamaps or None."""
              return results

   While it looks like there's quite a bit of code in this modeler plugin, a
   lot of that is the kind of error handling you'd want to do in a real modeler
   plugin. Let's walk through some of the highlights.

   1. Imports

      We import the standard `json` module because the Weather Underground API
      returns json-encoded responses that we'll want to convert to Python data
      structures.

      We import `inlineCallBacks` and `returnValue` because the
      `PythonPlugin.collect` method should return a `Deferred` so that it can
      be executed asynchronously by zenmodeler. You don't need to use
      `inlineCallbacks`, but I find it to be a nice way to make Twisted's
      asynchronous callback-based code look more procedural and be easier to
      understand. I recommend Dave Peticolas' excellent `Twisted Introduction`_
      for learning more about Twisted. `inlineCallback` is covered in part 17.

      We also import Twisted's `getPage` function. This is an extremely easy to
      use function for asynchronously fetching a URL.

      We import `PythonPlugin` because it will be the base class for our
      modeler plugin class. It's the best choice for modeling data from HTTP
      APIs.

      .. _Twisted Introduction: http://krondo.com/?page_id=1327

   2. `Locations` Class

      Remember that your modeler plugin's class name must match the filename or
      Zenoss won't be able to load it. So because we named the file
      ``Locations.py`` we must name the class ``Locations``.

   3. `relname` and `modname` Properties

      These should be defined in this way for modeler plugins that fill a
      single relationship like we're doing in this case. It states that this
      modeler plugin creates objects in the device's `wundergroundLocations`
      relationship, and that it creates objects of the
      `ZenPacks.training.WeatherUnderground.WundergroundLocation` type within
      this relationship.

      Where does relname come from? It comes from the
      ``[WundergroundDevice]++-[WundergroundLocation]`` relationship we defined
      in ``__init__.py``. Because it's a *to-many* relationship to the
      `WundergroundLocation` type, `zenpacklib` will name the relationship by
      lowercasing the first letter and adding an "s" to the end to make it
      plural.

      Where does modname come from? It will be <name-of-zenpack>.<name-of-
      class>. So because we defined the `WundergroundLocation` class in
      ``__init__.py``, and the ZenPack's name is
      `ZenPacks.training.WeatherUnderground`, the modname will be
      `ZenPacks.training.WeatherUnderground.WundergroundLocation`.

   4. `deviceProperties` Properties

      The class' `deviceProperties` property provides a way to get additional
      device properties available to your modeler plugin's `collect` and
      `process` methods. The default properties that will be available for a
      `PythonPlugin` are: `id`, `manageIp`, `_snmpLastCollection`,
      `_snmpStatus`, and `zCollectorClientTimeout`. Our modeler plugin will
      also need to know what values the user has set for `zWundergroundAPIKey`
      and `zWundergroundLocations`. So we add those to the defaults.

   5. `collect` Method

      The `collect` method is something `PythonPlugin` has, but other base
      modeler plugin types like `SnmpPlugin` don't. This is because you must
      write the code to collect the data to be processed, and that's exactly
      what you should do in the `collect` method.

      While the `collect` method can return either normal results or a
      `Deferred`, it is highly recommend to return a `Deferred` to keep
      zenmodeler from blocking while your `collect` method executes. In this
      example we've decorated the method with ``@inlineCallbacks`` and have
      returned out data at the end with ``returnValue(rm)``. This causes it to
      return a `Deferred`. By decorating the method with ``@inlineCallbacks``
      we're able to make an asynchronous request to the Weather Underground API
      with ``response = yield getPage(...)``.

      The first thing we do in the `collect` method is log an informational
      message to let the user know what we're doing. This log will appear in
      ``zenmodeler.log``, or on the console if we run `zenmodeler` in the
      foreground, or in the web interface when the user manually remodels the
      device.

      Next we make sure that the user has configured a value for
      `zWundergroundAPIKey`. This isn't strictly necessary here because the
      modeler plugin only uses Weather Underground's `AutoComplete` API which
      doesn't require an API key. I put this check here because I didn't want
      to get into a situation where the locations modeled successfully, but
      then failed to collect because an API key wasn't set.

      Next we make suer that the user as configured at least one location in
      `zWundergroundLocations`. This is mandatory because this controls what
      locations will be modeled.

      Next we create `rm` which is a common convention we use in modeler
      plugins and stands for `RelationshipMap`. Because we set the `relname`
      and `modname` class properties this will create a `RelationshipMap` with
      it's `relname` and `modname` set to the same.

      Now we iterate through each location making a call to the `AutoComplete`
      API for each. For each matching location in the response we will append
      an `ObjectMap` to `rm` with some key properties set.

      - `id` is mandatory and should be set to a value unique to all components
        on the device. If you look back the example `AutoComplete` response
        you'll see that the `zmw` property is useful for this purpose. Note
        that `prepId` should always be used for `id`. It will make any string
        safe to use as a Zenoss `id`.

      - `title` will default to the value of `id` if it isn't set. It's usually
        a good idea to explicitly set it as we're doing here. It should be a
        human-friendly label for the component. The location's `name` is a
        good candidate for this. It will look something like "Austin, Texas".

      - `api_link` is a property we defined for the `WundergroundLocation`
        class in ``__init__.py``. This is where we'll store the returned
        *link* or `l` property. This will be important for monitoring the
        alerts and conditions of the location later on.

      - `country_code` is another property we defined. It's purely
        informational and will simply be shown to the user when they're viewing
        the location in the web interface.

      - `timezeone` is another property we defined just for informational
        purposes.

   6. `process` Method

      The `process` method is usually where you take the data in the `results`
      argument and process it into DataMaps to return. However, in the case of
      `PythonPlugin` modeler plugins, the data returned from the `collect`
      method will be passed into `process` as the `results` argument. In this
      case that is already completely processed data. So we just return it.

4. Restart Zenoss.

   After adding a new modeler plugin you must restart Zenoss. If you're
   following the :ref:`running-a-minimal-zenoss` instructions you really only
   need to restart `zopectl` and `zenhub`.

That's it. The modeler plugin has been created. Now we just need to do some
Zenoss configuration to allow us to use it.
