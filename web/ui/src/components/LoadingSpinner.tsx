import { createSignal, onMount, onCleanup } from "solid-js"

export default function LoadingSpinner(props: { message?: string }) {
	const [spinnerIndex, setSpinnerIndex] = createSignal(0)
	const spinnerChars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

	let spinnerInterval: ReturnType<typeof setInterval> | undefined

	onMount(() => {
		spinnerInterval = setInterval(() => {
			setSpinnerIndex((prev) => (prev + 1) % spinnerChars.length)
		}, 80)
	})

	onCleanup(() => {
		if (spinnerInterval) {
			clearInterval(spinnerInterval)
		}
	})

	return (
		<div class="uppercase">
			<span>{spinnerChars[spinnerIndex()]}</span>&nbsp;{props.message || "&lt; Loading &gt;"}
		</div>
	)
}
