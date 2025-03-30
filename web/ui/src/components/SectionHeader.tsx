import { JSXElement, onMount, onCleanup } from "solid-js"

interface SectionHeaderProps {
	title: string
	tooltip?: string | JSXElement
}

function Tooltip(props: { message: string | JSXElement }) {
	let detailsRef: HTMLDetailsElement | undefined = undefined

	const close = () => {
		if (detailsRef === undefined) {
			return
		}

		;(detailsRef as HTMLDetailsElement).removeAttribute("open")
	}

	onMount(() => {
		document.addEventListener("click", close)
	})

	onCleanup(() => {
		document.removeEventListener("click", close)
	})

	return (
		<div class="relative">
			<details class="group" ref={detailsRef}>
				<summary class="cursor-pointer list-none flex-none tracking-tightest text-xs tracking-[-0.25em] no-marker">[+]</summary>
				<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
					<div class="max-w-[80vw] md:max-w-[33vw] px-8 py-8 bg-[#fcc6be] text-[#2A0D04] textsm border border-[#2A0D04] max-h-[90vh] md:max-h-[50vh] overflow-y-auto overflow-x-hidden">
						<div class="justify-end w-full text-right mb-2">
							<button class="cursor-pointer" onClick={close}>
								<mark>[&times; Close]</mark>
							</button>
						</div>
						<div onClick={(e) => e.stopPropagation()}>{props.message}</div>
					</div>
				</div>
			</details>
		</div>
	)
}

export default function SectionHeader(props: SectionHeaderProps) {
	return (
		<header class="flex items-center">
			<div class="flex-none">
				<mark class="uppercase p-1 tracking-widest text-lg">{props.title}</mark>
			</div>
			<div class="flex-1 ml-2">{props.tooltip ? <Tooltip message={props.tooltip} /> : null}</div>
		</header>
	)
}
