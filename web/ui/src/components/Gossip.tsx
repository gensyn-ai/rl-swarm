import { onMount, createEffect } from "solid-js"
import { useSwarm } from "../SwarmContext"
import SectionHeader from "./SectionHeader"
import LoadingSpinner from "./LoadingSpinner"

export default function Gossip() {
	const ctx = useSwarm()

	let containerRef: HTMLDivElement | undefined

	const scrollToBottom = () => {
		if (containerRef) {
			// Use requestAnimationFrame to ensure DOM has updated
			// Ensures we scroll after the browser paints new content
			requestAnimationFrame(() => {
				containerRef!.scrollTop = containerRef!.scrollHeight
			})
		}
	}

	onMount(() => {
		scrollToBottom()
	})

	createEffect(() => {
		// @ts-expect-error - Intentionally unused variable
		const _ = ctx.gossipMessages()
		scrollToBottom()
	})

	const GossipTooltip = () => {
		return (
			<div class="uppercase">
				Gossip shows the outputs from the agents throughout the game, including their responses to 
				the dataset prompts and to each other.
			</div>
		)
	}

	return (
		<section class="flex flex-grow flex-col gap-2">
			<SectionHeader title="gossip" tooltip={GossipTooltip()} />

			<div ref={containerRef} class="overflow-scroll overflow-x-hidden flex-grow min-h-0 max-h-[300px]" id="gossip-container">
				<ul class="list-none">
					{ctx.gossipMessages().length > 0 ? (
						ctx.gossipMessages().map((msg) => {
							return (
								<li class="mt-4">
									<NodeMessage id={msg.node} message={msg.message} />
								</li>
							)
						})
					) : (
						<span>
							<LoadingSpinner message="Fetching gossip..." />
						</span>
					)}
				</ul>
			</div>
		</section>
	)
}

function NodeMessage(props: { id: string; message: string }) {
	const reAnswer = new RegExp(/Answer:.+$/)

	const match = props.message.match(reAnswer)

	let mainText = props.message
	let answer = ""

	if (match) {
		mainText = mainText.slice(0, props.message.length - match[0].length)
		answer = match[0]
	}

	return (
		<p class="uppercase">
			<span class="text-gensyn-green">[{props.id}]</span> {mainText} <strong>{answer}</strong>
		</p>
	)
}
