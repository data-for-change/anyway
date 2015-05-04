class TrainingStep extends Backbone.Model
    defaults:
        title: null
        content: null
        path: null
        element: null
        orphan: null
        placement: null
        duration: null
        backdrop: null

    initialize: ->
        @set('orphan',!(@get('element')?))


class TrainingSteps extends Backbone.Collection
    model: TrainingStep

    buildTrainingUrl: ->
      # Choose the appropriate language
      lang = "#{window.pageModel.get('flow')}"
      if navigator.languages.indexOf("he") == -1
        lang = "en"
      return "#{window.pageModel.get('baseURL')}/api/training/"+lang+"?rand=#{Math.random()}"

    initialize: (models) ->
        @fetch(dataType: window.pageModel.get('dataType'), reset: true)

    url: ->
        @buildTrainingUrl()


class TrainingView extends Backbone.View

    initialize: ->
        if not @checkStorage('localStorage')
            # Disable the tour if window.localStorage isn't available.
            # Bootstrap Tour requires localStorage to function properly in
            # multi-page tours and to identify first visits to the page.
            $(@el).hide()
            return

        window.pageModel.on 'ready-budget-bubbles', => @loadTour()
        window.pageModel.on 'ready-budget-history', => @loadTour()
        window.pageModel.on 'ready-changegroup', => @loadTour()

    events:
        "click": "onTrainingButtonClick"

    loadTour: ->
        console.log "loadTour", window.pageModel.get('flow')
        if window.location.hash.length < 2
            console.log "not starting tour for hash ",window.location.hash
            return
        @steps = new TrainingSteps([])
        @steps.on 'reset', => @onTourLoaded(_.map(@steps.models, (i)->i.toJSON()))

    createTourOptions: (name, steps) ->
        options =
            name: name
            steps: steps
            keyboard: false # Disabled since the buttons are hard-coded to ltr.
            backdrop: true
            backdropPadding: 5
            template: JST.tour_dialog()
            debug: true
            redirect: (x) ->
                console.log "want to redirect to <<#{x}>>"
                if x!='/' then window.location.href = x
            onShow: (x) -> console.log "onshow",x
        return options

    onTourLoaded: (steps) =>
        console.log "got #{steps.length} steps"

        @replaceNullWithUndefined(step) for step in steps

        # options.basePath substitute: Only redirect if step.path is non-blank.
        for step in steps
            if step.path? and step.path != ''
                step.path = document.location.pathname + step.path

        #console.log "step 0", steps[0], steps[0].path
        #console.log "step 1", steps[1], steps[1].path

        # Split the steps into the redirection tour step and the rest.
        # TODO: This will only work with the 'main' flow, unless we add the redirection
        # step to each flow.
        @redirectionTourSteps = [steps[0]]
        @mainTourSteps = steps[1..]

        if 'redirect=1' in @getUrlParamArray()
            @startRedirectionTour()
        else
            @startMainTour()

    startRedirectionTour: () =>
        console.log "initializing redirection tour"

        options = @createTourOptions("tour-redirection", @redirectionTourSteps)
        options.onEnd = () => @startMainTour()

        tour = @startTour(options)
        if not @isTourRunning(tour)
            @startMainTour()

    startMainTour: () =>
        console.log "initializing main tour"

        options = @createTourOptions("tour-#{window.pageModel.get('flow')}",
                                     @mainTourSteps)
        options.onEnd = () =>
            # Show popover under the הדרכה link on top
            $("#intro-link").popover({
              content: "לחץ כאן בכל שלב על מנת לחזור על ההדרכה",
              placement: "bottom"
              })
              .data('bs.popover')
              .tip()
              .addClass("tour-reminder");
            $("#intro-link").popover('show');
            # Destroy the popover after 3 seconds
            setTimeout(() =>
                $("#intro-link").popover('destroy');
            , 3000);
            # Check if the forceTour parameter is present at the end of the tour.
            params = @getUrlParamArray()
            if 'forceTour=1' in params
                # Redirect to the current page, but without the forceTour parameter.
                # This gets rid of forceTour to prevent it from persisting and causing
                # unexpected starting of the tour upon moving to another page.
                params = @filterArray(params, 'forceTour=1')
                newSearch = @paramArrayToSearchString(params)
                newUrl = [document.location.pathname, newSearch, document.location.hash].join('')
                console.log "Tour: Redirecting to #{newUrl}"
                document.location.href = newUrl

        @tour = @startTour(options)
        if not @isTourRunning(@tour) and 'forceTour=1' in @getUrlParamArray()
            console.log "forcing the tour"
            @tour.restart()

    startTour: (options) =>
        tour = new Tour(options)
        # If we're in the middle of a multi-page tour, init() will automatically
        # start the tour.
        # Otherwise, if the tour was never shown, start() will start it.
        # start() has no effect if the tour is already displayed.
        tour.init()
        tour.start()
        return tour

    isTourRunning: (tour) ->
        # Assumes that the tour is initialized.
        console.log "isTourRunning", tour.ended(), tour.getCurrentStep()
        return not tour.ended() and tour.getCurrentStep() != null

    replaceNullWithUndefined: (obj) ->
        for own key, value of obj
            if value is null
                obj[key] = undefined

    onTrainingButtonClick: (event) ->
        event.preventDefault()
        # Don't start the tour if it wasn't initialized (due to loading failure)
        # or is already running.
        if (not @tour?) or @isTourRunning(@tour)
            console.log "not initialized!", @tour, @isTourRunning(@tour)
            return
        @tour.restart()

    checkStorage: (storageName) ->
        # Checks that the storage is enabled and writable.
        # The storage is passed by name since under Chrome even accessing
        # window.localStorage throws an exception if it's disabled .
        try
            storage = window[storageName]
            key = 'tour_storage_test'
            storage.setItem(key, 'test')
            storage.removeItem(key)
            return true
        catch
            return false

    searchStringToParamArray: (searchStr) ->
        if searchStr.indexOf('?') == 0
            searchStr = searchStr.substr(1)
        return (s for s in searchStr.split('&') when s != '')

    paramArrayToSearchString: (params) ->
        if params.length > 0
            return '?' + params.join('&')
        else
            return ''

    getUrlParamArray: () =>
        return @searchStringToParamArray(document.location.search)

    filterArray: (array, value) ->
        return (item for item in array when item != value)


$( ->
        console.log "initializing the training view"
        window.trainingView = new TrainingView({el: $("#intro-link"), model: window.pageModel})
)