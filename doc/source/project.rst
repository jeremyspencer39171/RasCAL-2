Project Widget 
==============

``ProjectWidget``
-----------------

The Project MDI widget itself is a stack of two views:

- The project (non-edit) view (``ProjectWidget.project_tab``)
- The edit view (``ProjectWidget.edit_project_tab``)

which the user goes between with the Edit Project and Save/Cancel buttons. 

The two views don't directly represent the ``Project`` from the MVP Model, but actually
represent a dictionary ``ProjectWidget.draft_project``. This dictionary is used to
defer validation until the user is done editing and saves the project. The draft
project is synchronised with the actual project in two methods:

- ``ProjectWidget.update_project_view`` overwrites the draft project data 
  with the MVP Model project data;
- ``ProjectWidget.save_changes`` validates the draft project, and if successful, overwrites the
  MVP Model project with the draft project data.

As ``ProjectWidget.update_project_view`` is called when changing from the edit view to the non-edit
view, the draft project and MVP Model project will *always* contain equivalent data when the non-edit
view is visible.

The ``ProjectWidget`` also contains a dictionary ``dict[str, list[str]]``
called ``ProjectWidget.tabs``. This is the schema for the structure of the project widget.
The keys are the full set of tabs in the widget, and the values are a list of which 
``Project`` fields are visible in that widget. The actual tab widgets created from this
schema are in ``ProjectWidget.view_tabs`` for the non-edit view and ``ProjectWidget.edit_tabs``
for the edit view; these are both a ``dict[str, ProjectTabWidget]`` where the keys are 
the same as those in ``ProjectWidget.tabs`` and the values are the appropriate tab widget, which
is a ``ProjectTabWidget`` object.

Draft project validation
^^^^^^^^^^^^^^^^^^^^^^^^

When changes to the project are saved, the draft project is validated with the method
``ProjectWidget.validate_draft_project``. In order to stop this function from being huge
and sprawling, it is a generator broken up into smaller sub-generators which ``yield`` relevant
errors for a specific tab of the project, and then ``validate_draft_project`` runs ``yield from``
over all of these sub-generators to get all of the errors. The errors will then be printed in the
terminal widget.

Note that if an invalid project state isn't handled by ``validate_draft_project``, as a fallback 
we run Pydantic validation on the draft project data and raise any Pydantic validation errors 
in the terminal widget. This means that an omission caused by a change in the API 
or a developer mistake doesn't crash RasCAL-2! The reason we have the custom validation is so that
the error messages are more relevant to the GUI rather than to Python source code, e.g. a layers
error would look like "The Thickness field of row 2 of the Layers tab is missing" rather than
something like "Field ``layers.1`` is missing parameter ``thickness``".


``ProjectTabWidget``
--------------------

Each tab of the two ``ProjectWidget`` views is represented by a ``ProjectTabWidget``. Each
``ProjectTabWidget`` is a ``QVBoxLayout`` of 'field widgets' which represent a specific project
field; the list of fields in the tab is taken from ``ProjectWidget.tabs``, and each field
widget can be accessed via the ``self.tables`` dictionary ``dict[str, ProjectFieldWidget]``
where the keys are the names of the project fields in the tab and the values are the relevant
widget for that field.

To update the data in the tab, the method ``ProjectTabWidget.update_model`` takes a
dictionary (always the ``ProjectWidget.draft_project``) and updates all of the field widgets 
in the tab.


Field Widgets
-------------

The field widgets each use a `Model/View architecture <https://doc.qt.io/qt-6/model-view-programming.html>`_
to manage the project field data. 

Models
^^^^^^

Each model represents a ``ClassList``. There are two types of model:

- ``ClassListTableModel`` for data to represent as a table (e.g. parameters). These are all in
  the file ``models.py``.
- ``ClassListItemModel`` for complex data given as pages with a list on the side 
  to change between them (e.g. contrasts). These are all in the file ``lists.py``.

.. warning:: 
   The data in the model, given by ``ClassListTableModel.classlist`` (or the same for item models),
   must be an object reference to the *exact same object* as the draft project classlist it represents! 
   This avoids needing to explicitly update the draft project when updating the model data, 
   and means the models are not tightly coupled to the project, 
   but it means if you need to overwrite the model data, 
   you must set the draft project value to that object.
   See ``LayersModel.set_absorption`` for an example where this happens.

All general item editing, adding, and deleting should be handled in the generic model. Then for a specific
field, you can subclass the ``ClassListTableModel`` (or item model) to handle things specific to
that field (e.g. toggling absorption for the ``LayersModel``, and handling item flags for most models)

Views
^^^^^

The view for these models is then given by a ``ProjectFieldWidget``. These take the initialisation
variable ``field``, which should be the name of the project field represented in this widget. The
model used by a specific subclass of the widget should be given 
as the class attribute ``ProjectFieldWidget.classlist_model``.
The generic ``ProjectFieldWidget`` object handles the display of the widget and the editing of the
model. In particular, there is a method ``ProjectFieldWidget.edit``, which tells the widget that it
should display in edit mode rather than view mode. 
The mode is held in the model attribute ``ClassListTableModel.edit_mode``, which is a boolean.

To create a view for a specific field, you can subclass ``ProjectFieldWidget`` to provide the specific
``classlist_model`` and give any handling specific to the field. In particular, note the method
``ProjectFieldWidget.set_item_delegates``, which you can overwrite to provide specific item delegates
for certain fields.
