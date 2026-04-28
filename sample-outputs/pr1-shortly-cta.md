# PR Review: DavidStone244/short.ly#10

## Summary

This PR hides the bottom call-to-action (CTA) section from authenticated users on the landing page of a URL shortener app. It adds `useAuth()` to the `HomePage` component and wraps the CTA section in a conditional `{!isAuthed && (...)}` check. The change is clean, focused, and follows the existing authentication pattern used elsewhere in the codebase.

## Identified Risks

- **No loading/error state handling**: `useAuth()` may return `undefined` or `null` for `token` during an initial loading state. If `token` starts as `undefined` (not `null`), `Boolean(undefined)` is `false`, which would briefly flash the CTA to signed-in users before the auth state resolves. Consider checking for a loading state or initializing `token` to `null` to avoid a flash of unwanted content.
- **Hardcoded auth dependency**: The PR assumes all consumers of this page have `useAuth()` available in the component tree. If the auth provider isn't mounted above this page, it will throw at runtime.

## Improvement Suggestions

- **Add a loading guard**: Introduce a `loading` state from `useAuth()` (if available) and only render the conditional after the initial auth check completes. For example:
  ```tsx
  const { token, loading } = useAuth();
  if (loading) return null; // or a skeleton
  ```
- **Consider a composable pattern**: Instead of repeating `!isAuthed` guards in individual page components, extract a `SignedOut` wrapper component that conditionally renders children. This keeps the auth logic reusable and colocated.
- **Add a test case for auth state**: Ensure the page renders correctly when `token` is `null`, `undefined`, and a valid string. A snapshot test would catch regressions.

## Confidence Score

**Medium** — The change is simple and logically sound, but the lack of loading-state handling introduces a potential UI flash that cannot be assessed without understanding the `useAuth()` implementation details.
