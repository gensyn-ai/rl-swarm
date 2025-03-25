import ts from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser'
import prettierConfig from 'eslint-config-prettier'
import solidPlugin from 'eslint-plugin-solid'

export default [
	{
		files: ['src/**/*.{js,jsx,ts,tsx}'],
		plugins: {
			'@typescript-eslint': ts,
			'solid': solidPlugin,
		},
		languageOptions: {
			parser: tsParser,
			ecmaVersion: 'latest',
			sourceType: 'module',
		},
		rules: {
			...ts.configs.recommended.rules, // Load recommended TypeScript rules
			...prettierConfig.rules,
			'brace-style': ['error', '1tbs'], // Enforce 1tbs brace style
			curly: ['error', 'all'], // Enforce curly braces
			'indent': ['error', 'tab', {
				"SwitchCase": 1,  // This ensures switch cases are indented
				"ignoredNodes": ["ConditionalExpression"]
			}],
			'max-lines-per-function': 'off', // Disable max lines per function
			'nonblock-statement-body-position': ['error', 'below'],
			'@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
			'solid/reactivity': 'warn',
			'solid/no-destructure': 'warn',
			'solid/jsx-no-undef': 'error',
			'no-mixed-spaces-and-tabs': ['error', 'smart-tabs'],
		},
	},
]
