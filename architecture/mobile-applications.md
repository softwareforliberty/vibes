# Mobile Application Architecture

How to structure an app for iOS or Android, whether it's built with SwiftUI,
UIKit, Jetpack Compose, Android views or a cross-platform toolkit. Read the
[rules for all software](README.md) first: a core of logic with thin edges,
dependencies pointing inward, and one owner for each piece of state. This
guide builds on them.

A mobile app is a GUI application, so the
[desktop guide](desktop-applications.md) applies to its view models, views,
threads and one-way data flow. What differs is that the operating system
decides how long the app runs. In the background, its process can be killed
to free memory, with no warning and no chance to run more code. The network
comes and goes, and background work runs only when the system allows. Its
natural shape is a local store that holds the truth, screens that observe
it, and sync with the server at the edge. Where the platform's own guidance
is more specific, follow it.

## Scale the structure to the task

- **A small app,** such as a few screens over one API: views, view models
  and a repository for each kind of data.
- **An app with offline use, sync or many features:** everything in this
  guide.

At every size, assume the process can die whenever the app isn't in the
foreground. Code that only works if the process lives rarely fails in
development, and often in the field.

## The layers

```text
view ──events──▶ view model ──▶ repository ──▶ local store ◀── sync ◀──▶ server
 ▲                   │                              │
 └──── UI state ◀────┴──────── observed data ◀──────┘
```

| Layer | Its job | Depends on | Never depends on |
| --- | --- | --- | --- |
| Core | The app's data and its rules | Nothing outside itself | The UI toolkit, the platform SDK |
| Data | Repositories, the local store, the network client and sync | Core, the store and network libraries | View models, views |
| View model | One screen's state, and the events it handles | Repositories, core | Views, UI types such as `Context` or `UIView` |
| View | SwiftUI views or composables that draw the state and send events | Its view model | Repositories, the network, the store |
| Platform | Device services, the keychain or keystore, background scheduling | The platform SDK, the interfaces it implements | View models, views |

These are the desktop guide's layers. Where view models share logic, such
as checking out a basket, put it in a use case between them and the data
layer, as Android's optional domain layer does. It plays the part of the
desktop guide's application layer.

### Core and data

The core holds the model and rules as plain types, with no imports from
UIKit, SwiftUI, Compose or the Android framework, so it's tested on the
development machine.

A repository is the only way to reach one kind of data. Reads come from the
local store, as an observable stream, never straight from the network.
Database records and network messages are converted to core types inside the
data layer, and never reach a view model.

### View models and views

A view model, such as an Android `ViewModel` or an `@Observable` class in
SwiftUI, holds one screen's state as a single immutable value, and has a
function for each event the screen sends. It outlives the view, but not the
process, and never holds a view or an activity, so it can't leak one.

A view draws the state it's given and sends events, with no logic beyond
display, so it renders the same in previews and tests. State only the view
cares about, such as whether a menu is open, can stay in the view.

### Platform

Every device service, such as location, the camera, notifications or
biometrics, sits behind an interface the app owns, so tests and previews run
without the device.

## The lifecycle and process death

- **Save as the user goes,** to the local store, and at the latest when the
  app leaves the foreground. On both platforms, a process in the background
  can be killed with no further callback.
- **Rebuilding a screen is normal.** Android recreates an activity on a
  configuration change, such as rotation, and both platforms rebuild views
  freely, so nothing important lives only in a view.
- **Start from any screen.** After process death, the system can return the
  user to the screen they left, in a new process with nothing in memory.
  Each screen loads what it needs from its arguments and the store.
- **Go quiet in the background.** Pause timers, release shared hardware
  such as the camera, and hide sensitive content before the system takes
  the app switcher's snapshot.

## State that survives

| State | Example | Where it lives |
| --- | --- | --- |
| Data the user would miss | A draft, a basket, settings | The local store, written as it changes |
| Small UI state | The selected tab, a search query, the navigation stack | Saved state: `SavedStateHandle` or `rememberSaveable` on Android, `@SceneStorage` on iOS |
| State that can be rebuilt | Loaded lists, images | Memory, reloaded from the store |

- **Saved state is small.** Both platforms say to keep it light. Save an
  id, not the record.
- **Saved state isn't permanent.** It's discarded when the user removes the
  app from the app switcher, so anything the user would miss belongs in the
  store.
- **Never put secrets in saved state,** which the system stores outside the
  app's control.

## Offline first

- **Read and write the local store first.** Show what's there at once, and
  queue each change for the server, so a dropped connection never loses the
  user's work.
- **Sync at the edge.** A sync component, run as background work, sends
  queued changes, fetches what changed and writes it to the store, which
  updates every screen observing it.
- **Retry with backoff,** only on errors a retry can fix, such as a lost
  connection.
- **Decide how conflicts resolve,** such as last write wins or a merge per
  field, and version each record so the server can tell.

## Background work

Both platforms limit background work, and the limits change between
versions. Design for work that runs late, is cut short, or doesn't run.

- **Use the platform's scheduler,** never a thread or timer that assumes the
  app keeps running. On Android, that's WorkManager, which keeps work across
  restarts and reboots, and runs it under constraints such as an unmetered
  network. On iOS, it's the Background Tasks framework, where the system
  picks when a task runs, and calls its expiration handler when time is up.
- **Ongoing work the user knows about,** such as playing audio, uses the
  platform's mechanism for it, such as a foreground service with a visible
  notification on Android, or a background mode on iOS.
- **Each task can stop at any point and run again.** Save progress as it
  goes, and make each step idempotent.

## Navigation

- **The navigation stack is state,** owned in one place, such as a
  `NavigationStack` path in SwiftUI or the back stack in Jetpack Navigation.
  A view model asks for navigation through an event or a state change, and
  never holds a view.
- **Destinations take ids,** not objects, so a deep link, a notification
  and a stack restored after process death all open a screen the same way.
  Validate deep links like any outside input.

## Permissions

- **Ask at the point of use,** when the user starts the feature that needs
  the permission, never all at once at launch.
- **Explain first** when the reason isn't obvious. On iOS, each protected
  resource also needs a purpose string, or the system terminates the app
  when it asks.
- **Work without it.** When the user says no, the rest of the app works,
  and the feature says what it needs.
- **Check every time.** The user can revoke a permission at any moment, and
  Android resets them for apps left unused for months.

## Secrets

- **Keep secrets in the keychain on iOS,** and on Android in storage
  encrypted with a key from the Android Keystore, never in user defaults,
  shared preferences or plain files.
- **Generate keys inside the keystore or the Secure Enclave** where
  possible, so the key material never enters the app's process.
- **Never ship a server secret in the app.** Anything in the package can be
  extracted, so the server holds the secrets.

## Battery, network and memory

- **Batch network requests,** and defer large transfers to unmetered
  networks or charging, through the scheduler's constraints. Prefer push
  messages to polling.
- **Bound every cache,** and free caches when the system warns of low
  memory.
- **Keep the main thread free,** as the
  [desktop guide](desktop-applications.md#threads) describes.

## Accessibility and localisation

- **Every control has an accessible label** and works with VoiceOver and
  TalkBack, and text scales with the user's font size.
- **Every user-facing string comes from the platform's localisation
  system,** such as string catalogs on iOS or string resources on Android.
  View models expose values or string keys, and the view turns them into
  text.
- **Layouts use leading and trailing,** not left and right, so they follow
  the reading direction.

## Layout

```text
core/              the model and rules, with no platform imports
data/              repositories, the local store, the network client and sync
feature/<name>/    one feature's views and view models
platform/          the interfaces, and their implementations
app/               the entry point, navigation and wiring
```

## Enforce it

- **Make each layer its own module,** such as a Gradle module or a Swift
  package, so the build rejects a forbidden import. Features depend on
  `data` and `core`, never on each other.
- **Typical rules for architecture tests:** the core doesn't import the UI
  toolkit or platform SDK; view models don't import UI types; views don't
  import repositories; only `platform/` uses device APIs.

## Testing

| Layer | Test with |
| --- | --- |
| Core and use cases | Unit tests on the development machine |
| Repositories and sync | Unit tests with a fake network and the real local store |
| View models | Unit tests, with fake repositories and platform services |
| Views | The toolkit's UI test tools, or snapshot tests of each state |
| The whole app | A few end-to-end tests on emulators, simulators and real devices |

- **Test process death:** restore each screen from its saved state alone,
  and on a device, kill the app in the background and return to it.
- **Test the hard conditions:** offline, a connection that drops during a
  sync, permissions denied or revoked, large text, a screen reader and a
  right-to-left language.
