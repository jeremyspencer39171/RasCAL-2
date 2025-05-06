Plotting Widget
===============

Each type of plot available in RasCAL-2 is created as a subclass of the
``AbstractPlotWidget`` widget. This widget handles creating the plot
canvas and the layout of the widget.

The 'public' interface of each of these plot widgets is just the ``plot`` function,
which takes a project and results and redraws the plot. The benefit of this is no
matter how we want to lay out the plots (e.g. in tabs, dialogs, etc.) we can just
create that layout and then hook the plots in by creating a function which calls
``plot`` on all the plot widgets when necessary.

All plot widgets must implement:

- ``AbstractPlotWidget.make_control_layout``: A method which takes no parameters
  and returns the layout of the fit settings for the widget.
- ``AbstractPlotWidget.plot``: A method which takes a Project and Results object
  and runs the plot along with any setup.

I've found it's easiest to use the ``plot`` method for setting up the plot and
saving any relevant parts of the results as an instance attribute,
then calling a ``draw_plot`` method which does the actual plot drawing; this means
that signals that redraw the plot can connect to ``draw_plot`` and
just grab things from the instance attribute and don't need to redo all the setup.

Plot widgets can also reimplement:

- ``AbstractPlotWidget.make_toolbar_widgets``: Returns a list of
  widgets to add to the always-shown toolbar (underneath the fit settings show/hide button),
  e.g. the slider for the y-axis on the reflectivity/SLD plots.
- ``AbstractPlotWidget.make_figure``: Makes the figure object onto which the plot is drawn.
  By default this just returns a standard ``matplotlib.Figure``, but if you want to e.g. have 
  subplots or a pre-existing set of axes, this should be reimplemented to do that.

Most of the Bayesian plot widgets inherit an abstract subclass ``AbstractPanelPlotWidget``; this
abstraction just lets them share the logic for the parameter selection field for selecting subsets
of the fit parameters to plot.
