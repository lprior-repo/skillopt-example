# React-TypeScript Skill Bundle

TypeScript strict mode plus React 18 hooks lint rules for production-grade UI code.

## Hard Rules

- Never use `any`; use a typed alternative or `unknown` with a narrowing guard
- Never use `unknown` as a public surface; narrow to a concrete type before exposing
- Never use `console.log` in production paths; route through a typed logger
- Never use `@ts-ignore`; use `@ts-expect-error` with a justification comment when unavoidable
- Never use `@ts-nocheck` on a file; address the type errors instead
- Never use `as unknown as`; rely on `in`, `instanceof`, or discriminated unions for narrowing
- Every React component declares explicit prop and state types; no inferred `JSX.Element`
- Every `useEffect` carries a complete dependency array; no exhaustive-deps disables
- Every `useMemo` and `useCallback` returns a value the consumer actually needs

## Strict Compiler Settings

The recommended `tsconfig.json` enables:

- `strict: true`
- `noUncheckedIndexedAccess: true`
- `exactOptionalPropertyTypes: true`
- `noImplicitOverride: true`
- `noFallthroughCasesInSwitch: true`
- `noPropertyAccessFromIndexSignature: true`

## Required Coverage Gates

Every change must pass:

- `tsc --noEmit` for type checking
- `eslint --max-warnings=0` with the project rule set
- `vitest run --coverage` for unit and integration tests
- `vitest run --typecheck` for type-aware tests
- A Storybook or Chromatic visual regression run for shared components

## React-Specific Rules

- Function components only; no class components
- One component per file unless the helper is sub-50 LOC and only used by its sibling
- Hooks follow the rules of hooks; no conditional hook calls
- Context providers wrap a typed default value plus a typed reducer signature
- Refs use `useRef<HTMLElement | null>(null)` and assert before use

## No Periods

This skill bundle is prose, but every prose sentence in source code, error messages, and CLI descriptions ends without a period; the period rule is enforced by the harness.