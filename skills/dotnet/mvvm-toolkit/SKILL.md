---
name: mvvm-toolkit
description: >-
  Authors and reviews view models with CommunityToolkit.Mvvm 8.x source generators:
  ObservableProperty, RelayCommand, NotifyPropertyChangedFor, and validation. Use when writing MVVM
  view models, properties, or commands in a .NET XAML app.
source: "https://github.com/github/awesome-copilot"
attribution: "github/awesome-copilot by GitHub Community"
license: MIT
version: "1.1.0"
---

> **Attribution:** Sourced from [github/awesome-copilot](https://github.com/github/awesome-copilot) by [GitHub Community](https://github.com/github), licensed MIT. Modified for this collection.

# CommunityToolkit.Mvvm (core)

Use this skill when authoring or reviewing ViewModels, properties,
commands, or validation in apps that use `CommunityToolkit.Mvvm` 8.x.

> **Companion skills.** Load **`mvvm-toolkit-messenger`** for `IMessenger`
> pub/sub patterns. Load **`mvvm-toolkit-di`** for
> `Microsoft.Extensions.DependencyInjection` integration.

> **Quick recap.** On CommunityToolkit.Mvvm 8.4+, use an
> `[ObservableProperty]` partial property when the project uses the .NET 9
> SDK and C# preview language mode required by Toolkit 8.4;
> keep the field form for older language versions. WinUI 3 AOT requires the
> partial-property form. Use `[RelayCommand]` on instance methods; inherit from
> `ObservableObject` (or `ObservableValidator` for input forms,
> `ObservableRecipient` when using `IMessenger`).

---

## Package & setup

```xml
<ItemGroup>
  <PackageReference Include="CommunityToolkit.Mvvm" Version="8.4.2" />
</ItemGroup>
```

Targets: `netstandard2.0`, `netstandard2.1`, `net6.0`+. Works on .NET, .NET
Framework, Mono. Source generators ship in the same NuGet — no extra
analyzer reference required.

Namespaces:

```csharp
using CommunityToolkit.Mvvm.ComponentModel;   // ObservableObject, [ObservableProperty]
using CommunityToolkit.Mvvm.Input;             // [RelayCommand], RelayCommand, AsyncRelayCommand
```

> **Universal rule.** Every type that uses `[ObservableProperty]` or
> `[RelayCommand]` — and every enclosing type, if nested — must be
> declared `partial`. A non-partial containing type triggers `MVVMTK0008`.
> `MVVMTK0042` instead recommends converting an observable field to a
> partial property; `MVVMTK0045` warns that the field form is not AOT-safe
> in WinRT scenarios such as WinUI 3.

---

## Source generators cheat sheet

| Attribute | Applied to | Generates |
|-----------|-----------|-----------|
| `[ObservableProperty]` | partial property (.NET 9 SDK + C# preview for Toolkit 8.4) or field | Implements the property/notification setter + `OnXxxChanging`/`OnXxxChanged` partial-method hooks |
| `[NotifyPropertyChangedFor(nameof(Other))]` | observable property or field | Also raises `PropertyChanged` for the listed property |
| `[NotifyCanExecuteChangedFor(nameof(MyCommand))]` | observable property or field | Calls `MyCommand.NotifyCanExecuteChanged()` on change |
| `[NotifyDataErrorInfo]` | observable property or field on `ObservableValidator` | Calls `ValidateProperty(value)` from the setter |
| `[NotifyPropertyChangedRecipients]` | observable property or field on `ObservableRecipient` | `Broadcast(old, new)` after the change |
| `[RelayCommand]` | instance method | Lazy `RelayCommand` / `AsyncRelayCommand` exposed as `IRelayCommand` / `IAsyncRelayCommand` |
| `[RelayCommand(CanExecute = nameof(CanX))]` | instance method | Wires `CanExecute` to a method or property |
| `[RelayCommand(IncludeCancelCommand = true)]` | async method with `CancellationToken` | Also generates `XxxCancelCommand` |
| `[RelayCommand(AllowConcurrentExecutions = true)]` | async method | Allows queued/parallel invocations (default disables while running) |
| `[RelayCommand(FlowExceptionsToTaskScheduler = true)]` | async method | Surfaces exceptions via `ExecutionTask` instead of awaiting and rethrowing |
| `[property: SomeAttr]` | observable field or `[RelayCommand]` method | Forwards `SomeAttr` onto the generated property (e.g., `[JsonIgnore]`) |

**Naming.** Field `name` / `_name` / `m_name` → `Name`. Method `LoadAsync` →
`LoadCommand` (the `Async` suffix is stripped; a leading `On` is also
stripped).

See [`references/source-generators.md`](references/source-generators.md) for
the full attribute reference with generated-code samples.

---

## ViewModel patterns

### Simple observable property

```csharp
public partial class ContactViewModel : ObservableObject
{
    [ObservableProperty]
    public partial string? Name { get; set; }
}
```

In Toolkit 8.4, the partial-property form requires the .NET 9 SDK and C#
preview language mode. It is preferred because analyzers,
other generators, and WinRT AOT tooling can see the declared property. For a
project pinned to an older language version, the compatible field form remains:

```csharp
[ObservableProperty]
private string? name; // generates public Name
```

### Hooks: `OnXxxChanging` / `OnXxxChanged`

```csharp
[ObservableProperty]
private string? name;

partial void OnNameChanged(string? value) =>
    Logger.LogInformation("Name changed to {Name}", value);
```

Both single-arg `(value)` and two-arg `(oldValue, newValue)` overloads
are available. Implement only the ones you need; unimplemented hooks are
elided by the compiler (zero runtime cost).

### Dependent properties + dependent commands

```csharp
[ObservableProperty]
[NotifyPropertyChangedFor(nameof(FullName))]
[NotifyCanExecuteChangedFor(nameof(SaveCommand))]
private string? firstName;

[ObservableProperty]
[NotifyPropertyChangedFor(nameof(FullName))]
[NotifyCanExecuteChangedFor(nameof(SaveCommand))]
private string? lastName;

public string FullName => $"{FirstName} {LastName}".Trim();
```

### Wrapping a non-observable model

```csharp
public sealed class ObservableUser(User user) : ObservableObject
{
    public string Name
    {
        get => user.Name;
        set => SetProperty(user.Name, value, user, (u, n) => u.Name = n);
    }
}
```

Pass a static lambda (no captured state) to keep the call allocation-free.

---

## Commands

```csharp
[RelayCommand]
private void Refresh() => Items.Reset();

[RelayCommand]
private async Task LoadAsync()
{
    foreach (var item in await service.GetItemsAsync())
        Items.Add(item);
}

[RelayCommand(IncludeCancelCommand = true)]
private async Task DownloadAsync(CancellationToken token)
{
    await using var stream = await http.GetStreamAsync(url, token);
    // ...
}

[RelayCommand(CanExecute = nameof(CanSave))]
private Task SaveAsync() => repo.SaveAsync(Name!);

private bool CanSave() => !string.IsNullOrWhiteSpace(Name);
```

Reach for manual `RelayCommand` / `AsyncRelayCommand` constructors only
when you must own the command's lifetime explicitly or compose it from
non-trivial sources. The attribute style covers ~95% of cases.

See [`references/relaycommand-cookbook.md`](references/relaycommand-cookbook.md)
for sync / async / cancellable / concurrency / error-surfacing recipes.

---

## Base class selection

| Base class | Use when |
|------------|---------|
| `ObservableObject` | Default. `INotifyPropertyChanged` + `INotifyPropertyChanging` + `SetProperty` overloads + `SetPropertyAndNotifyOnCompletion` for `Task` properties |
| `ObservableValidator` | The VM needs `INotifyDataErrorInfo` (forms, settings input) |
| `ObservableRecipient` | The VM sends or receives `IMessenger` messages — see the **`mvvm-toolkit-messenger`** skill |

C# is single-inheritance: `ObservableValidator` and `ObservableRecipient`
both extend `ObservableObject`, so combining them requires composition
(e.g., inject `IMessenger` into an `ObservableValidator`).

---

## Validation

```csharp
using System.ComponentModel.DataAnnotations;

public sealed partial class RegistrationViewModel : ObservableValidator
{
    [ObservableProperty]
    [NotifyDataErrorInfo]
    [Required, MinLength(2), MaxLength(100)]
    private string? name;

    [ObservableProperty]
    [NotifyDataErrorInfo]
    [Required, EmailAddress]
    private string? email;

    [RelayCommand]
    private void Submit()
    {
        ValidateAllProperties();
        if (HasErrors) return;
        // submit...
    }
}
```

Other entry points: `TrySetProperty`, `ValidateProperty(value, name)`,
`ClearAllErrors()`, `GetErrors(propertyName)`. Custom rules support
`[CustomValidation]` methods and custom `ValidationAttribute` subclasses.

See [`references/validation.md`](references/validation.md) for the full
validator surface area.

---

## Top pitfalls

1. **Forgetting `partial`.** Class (and every enclosing type) must be
   `partial`. The containing-type error is `MVVMTK0008`.
2. **Using field syntax in a WinUI 3 AOT app.** `MVVMTK0045` warns that
   generated field-backed properties are not CsWinRT AOT-compatible. Use
   `[ObservableProperty] public partial T Name { get; set; }` with the
   required .NET 9 SDK and C# preview language mode.
3. **PascalCase field name.** `[ObservableProperty] private string Name;`
   collides with the generated property. Use `name`, `_name`, or `m_name`.
4. **`async void` on `[RelayCommand]`.** The generator only wraps
   `Task`-returning methods as `IAsyncRelayCommand`. `async void` becomes
   a sync `RelayCommand` and exceptions are unobserved. Always return
   `Task`.
5. **Forgetting `[NotifyCanExecuteChangedFor]`.** The Save button stays
   disabled even though `CanSave()` would now return `true`.
6. **Mutating the same reference held by an `[ObservableProperty]`
   field.** `EqualityComparer<T>.Default` returns `true`, no notification
   fires. Replace the instance instead of mutating it.

For the full diagnostic table (`MVVMTK0xxx`) and more pitfalls, see
[`references/troubleshooting.md`](references/troubleshooting.md).

---

## End-to-end mini walkthrough

A two-pane Notes app demonstrating generators + commands +
`[NotifyCanExecuteChangedFor]`:

```csharp
public sealed partial class NoteViewModel(INotesService notes,
    IMessenger messenger) : ObservableRecipient(messenger)
{
    [ObservableProperty]
    [NotifyCanExecuteChangedFor(nameof(SaveCommand))]
    [NotifyCanExecuteChangedFor(nameof(DeleteCommand))]
    private string? filename;

    [ObservableProperty]
    [NotifyCanExecuteChangedFor(nameof(SaveCommand))]
    private string? text;

    [RelayCommand(CanExecute = nameof(CanSave))]
    private Task SaveAsync()
    {
        Messenger.Send(new NoteSavedMessage(Filename!));
        return notes.SaveAsync(Filename!, Text!);
    }

    [RelayCommand(CanExecute = nameof(CanDelete))]
    private Task DeleteAsync() => notes.DeleteAsync(Filename!);

    private bool CanSave() =>
        !string.IsNullOrWhiteSpace(Filename) && !string.IsNullOrEmpty(Text);
    private bool CanDelete() => !string.IsNullOrWhiteSpace(Filename);
}
```

For the full sample (DI wiring, View code-behind, XAML, unit tests), see
[`references/end-to-end-walkthrough.md`](references/end-to-end-walkthrough.md).

---

## References & companion skills

| Topic | Where |
|-------|-------|
| Source generator attribute reference | [`references/source-generators.md`](references/source-generators.md) |
| RelayCommand recipes | [`references/relaycommand-cookbook.md`](references/relaycommand-cookbook.md) |
| Validation deep dive | [`references/validation.md`](references/validation.md) |
| Full Notes-app walkthrough | [`references/end-to-end-walkthrough.md`](references/end-to-end-walkthrough.md) |
| `MVVMTK0xxx` diagnostics & pitfalls | [`references/troubleshooting.md`](references/troubleshooting.md) |
| **Messenger pub/sub** | Companion skill: **`mvvm-toolkit-messenger`** |
| **`Microsoft.Extensions.DependencyInjection` wiring** | Companion skill: **`mvvm-toolkit-di`** |

External sources:

- Toolkit overview: <https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/>
- WinUI MVVM Toolkit tutorial: <https://learn.microsoft.com/en-us/windows/apps/tutorials/winui-mvvm-toolkit/intro>
- Source: <https://github.com/CommunityToolkit/dotnet>
- Samples: <https://github.com/CommunityToolkit/MVVM-Samples>
