import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  // Custom rule overrides
  {
    rules: {
      // Allow explicit any temporarily - TODO: gradually type these properly
      "@typescript-eslint/no-explicit-any": "warn",
      // Allow unused vars with underscore prefix and variables named 'error'
      "@typescript-eslint/no-unused-vars": ["warn", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_|^error$|^results$"
      }],
      // Allow setState in effects (React pattern used in this codebase)
      "react-hooks/set-state-in-effect": "off",
      // Relax React hooks rules for deployment
      "react-hooks/exhaustive-deps": "warn",
      "react-hooks/preserve-manual-memoization": "off",
    },
  },
]);

export default eslintConfig;
