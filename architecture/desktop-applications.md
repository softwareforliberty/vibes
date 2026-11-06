# Desktop Application Architecture

How to structure a desktop application, or any other application with a
graphical interface, in any language and toolkit, such as Qt, GTK, AppKit,
WinUI or wxWidgets. Read the [rules for all software](README.md) first: a
core of logic with thin edges, dependencies pointing inward, and one owner
for each piece of state. This guide builds on them.

A desktop application has no request and response. It runs for a long time,
holds state in memory, reacts to events on one UI thread, and talks to the
operating system directly. Its natural shape is a document or data model at
the core, commands that change it, and views that show it.

Each toolkit has its own pattern for this, such as Qt's model/view classes,
MVC with view controllers in AppKit, or MVVM with data binding in WinUI.
Follow the toolkit's pattern, mapped onto the layers below.

## Scale the structure to the task

- **A small utility,** such as a single window with a form: a core module of
  plain functions and types, and the window that calls it.
- **An application with documents, editing or several windows:** everything
  in this guide.

At every size, keep the core free of the GUI toolkit, so it can be tested
and reused without a display.

## The layers

```text
input ─▶ view ─▶ view model ─▶ command ─▶ application ─▶ core
          ▲          ▲                                     │
          └──────────┴───────── change notifications ◀─────┘
```

| Layer | Its job | Depends on | Never depends on |
| --- | --- | --- | --- |
| Core | The data or document and its rules | Nothing outside itself | The toolkit's GUI modules, the platform |
| Application | Commands, undo, opening and saving, use cases | Core, platform interfaces | View models, views |
| View model | One view's state and display logic | Application, core | Widgets |
| View | Widgets, layout, drawing and input | Its view model, the toolkit | The core's internals, the platform |
| Platform | Files, settings, clipboard, notifications, OS integration | The OS, the interfaces it implements | View models, views |

### Core

The core holds the application's data, such as a document, a project or a
library of records, and every rule about it.

- **It doesn't depend on the GUI toolkit's widget or graphics modules.**
  Using the toolkit's non-GUI base library, such as Qt Core or GLib, is fine
  where it's the idiom for the language.
- **It notifies observers when it changes,** through the toolkit's signal
  mechanism or a plain observer interface, and never knows who's listening.
- **It reports errors as values,** never by showing a dialog or writing
  user-facing text.
- **Its model is separate from its file formats.** Each format has its own
  reader and writer, versioned, so the model can change without breaking
  saved files.

### Application

The application layer holds the use cases: open, save, edit, export and
undo.

- **Every user action is a command.** A command object changes the core and
  knows how to undo the change, so menus, toolbars, shortcuts, drag and drop,
  scripting and undo all share one path. Use the toolkit's undo stack where
  it has one.
- **Whether a command is available comes from the state,** never from a
  view remembering to disable a button.
- **Requests from the operating system,** such as opening a file from the
  file manager or a second launch of the application, go through the same
  commands as the menu does.
- **Saving is safe.** Write to a temporary file in the same directory, flush
  it to disk, then rename it over the original, so a crash never leaves a
  half-written file. Unsaved changes come from the undo stack's position, not
  a separate flag.

### View models

A view model holds the state of one view, such as the selection, the
filter, what's expanded and what's enabled, and turns core data into what the
view displays.

- **It has no widgets,** so it can be tested without a display.
- **It turns user input into commands,** rather than changing the core
  itself.
- **User-facing text lives here or in the view,** translated through the
  toolkit's localisation system. The core returns error values, and the view
  model turns them into messages.

### Views

A view is the widgets, layout and drawing for one window, panel or dialog.

- **It binds to its view model** and holds no logic beyond display: no
  rules, no file access and no direct changes to the core.
- **It uses the toolkit's accessibility support,** with every control
  labelled and reachable from the keyboard.
- **An immediate-mode interface,** such as Dear ImGui, draws the whole view
  from the view model every frame. The layers stay the same.

### Platform

Everything that touches the operating system sits behind interfaces the
application layer owns: files and file dialogs, settings, the clipboard,
notifications, the system tray, printing and integration with the desktop.

- **Each platform's code lives in its own files,** one directory per
  operating system, chosen by the build, behind the shared interface.
- **Settings are a typed object with defaults,** stored through the
  platform's settings store, with a version so older settings can be
  migrated.

## Threads

- **The UI thread owns every widget and view model.** Only it touches them.
- **Never block the UI thread** on files, the network or long calculations.
  Run that work on a worker thread or task pool, and post the result back to
  the UI thread through the toolkit's event loop, such as a queued signal in
  Qt, `g_idle_add` in GLib or the main dispatch queue in AppKit.
- **Long work can be cancelled and reports progress.** Closing a window or
  the application cancels its work and waits for it, before the objects it
  uses are destroyed.
- **The core is changed on one thread.** Worker threads compute from a copy
  or a snapshot, and the result is applied on the owning thread.

## Data flows one way

Input goes from the view to the view model, which runs a command, which
changes the core. The core then notifies the view models, which update the
views. A view never changes the core, and a view model never pushes changes
into another view model directly.

## Ownership and lifetimes

- **Every object has one owner,** such as a parent in the toolkit's object
  tree, or a smart pointer in C++. In C++, no raw pointer owns anything.
- **A connection never outlives its receiver.** Connect signals with a
  receiver whose destruction disconnects them, as Qt does with a context
  object, or disconnect in the receiver's destructor.
- **Observers hold weak references** to what they observe, or are removed
  before it's destroyed.
- **One place builds and wires everything at startup,** in `main`: the core,
  the platform implementations, the application layer and the main window.
  There are no global singletons apart from the toolkit's own application
  object.

## Plugins

When the application loads plugins:

- **Plugins see a small, versioned interface,** never the application's
  internals.
- **A C++ application uses a C interface at the plugin boundary,** or the
  toolkit's plugin system, because C++ has no stable binary interface across
  compilers and versions.
- **A plugin's failures stay contained.** Check its interface version
  before using it, and catch its errors at the boundary. Where a plugin
  crash mustn't take down the application, run plugins in a separate
  process.

## Layout

```text
src/
├── core/        the data model and its rules, with no GUI
├── app/         commands, undo and the use cases
├── ui/          views and their view models
├── platform/    the interfaces, and a directory per operating system
└── main.cpp     builds and wires everything
```

## Enforce it

- **Build each layer as its own library or module.** In C and C++, give each
  layer its own CMake target, and link the GUI toolkit's widget modules only
  into `ui`. The core then can't even find the widget headers, so a
  forbidden include fails to build.
- **Typical rules for architecture tests:** the core and the application
  layer don't use the toolkit's GUI modules; views don't use the core's
  internals or the platform; only `platform/` uses OS-specific APIs.

## Testing

| Layer | Test with |
| --- | --- |
| Core and application | Unit tests, with no display and fake platform interfaces |
| View models | Unit tests, with no display |
| Views | The toolkit's test tools, on an off-screen display where it has one |
| Platform | Integration tests on each operating system |
| The whole application | A few end-to-end tests that drive the interface |

- **Test undo for every command:** doing and then undoing it leaves the
  core exactly as it was.
- **Test file formats both ways,** and test reading files saved by earlier
  versions.
