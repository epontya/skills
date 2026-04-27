---
name: aspnet-core
description: Build, review, refactor, or architect ASP.NET Core web applications using current official guidance for .NET web development. Use when working on Blazor Web Apps, Razor Pages, MVC, Minimal APIs, controller-based Web APIs, SignalR, gRPC, middleware, dependency injection, configuration, authentication, authorization, testing, performance, deployment, or ASP.NET Core upgrades.
---

# ASP.NET Core

## Overview

Choose the right ASP.NET Core application model, compose the host and request pipeline correctly, and implement features in the framework style Microsoft documents today.

Load the smallest set of references that fits the task. Do not load every reference by default.

## Workflow

1. Confirm the target framework, SDK, and current app model.
2. Open [references/stack-selection.md](references/stack-selection.md) first for new apps or major refactors.
3. Open [references/program-and-pipeline.md](references/program-and-pipeline.md) next for `Program.cs`, DI, configuration, middleware, routing, logging, and static assets.
4. Open exactly one primary app-model reference:
   - [references/ui-blazor.md](references/ui-blazor.md)
   - [references/ui-razor-pages.md](references/ui-razor-pages.md)
   - [references/ui-mvc.md](references/ui-mvc.md)
   - [references/apis-minimal-and-controllers.md](references/apis-minimal-and-controllers.md)
5. Add cross-cutting references only as needed:
   - [references/data-state-and-services.md](references/data-state-and-services.md)
   - [references/security-and-identity.md](references/security-and-identity.md)
   - [references/realtime-grpc-and-background-work.md](references/realtime-grpc-and-background-work.md)
   - [references/testing-performance-and-operations.md](references/testing-performance-and-operations.md)
6. Open [references/versioning-and-upgrades.md](references/versioning-and-upgrades.md) before introducing new platform APIs into an older solution or when migrating between major versions.
7. Use [references/source-map.md](references/source-map.md) when you need the Microsoft Learn section that corresponds to a task not already covered by the focused references.

## Default Operating Assumptions

- Prefer the latest stable ASP.NET Core and .NET unless the repository or user request pins an older target.
- As of March 2026, prefer .NET 10 / ASP.NET Core 10 for new production work. Treat ASP.NET Core 11 as preview unless the user explicitly asks for preview features.
- Prefer `WebApplicationBuilder` and `WebApplication`. Avoid older `Startup` and `WebHost` patterns unless the codebase already uses them or the task is migration.
- Prefer built-in DI, options/configuration, logging, ProblemDetails, OpenAPI, health checks, rate limiting, output caching, and Identity before adding third-party infrastructure.
- Keep feature slices cohesive so the page, component, endpoint, controller, validation, service, data access, and tests are easy to trace.
- Respect the existing app model.

## Personal Notes

- I primarily work with Minimal APIs and Blazor Server; lean toward those patterns in examples unless the task clearly calls for something else.
- When generating new projects, default to enabling nullable reference types and implicit usings in the `.csproj`.
- Prefer `IResult`-returning endpoint handlers and `TypedResults` over raw `Results` for better OpenAPI inference.
