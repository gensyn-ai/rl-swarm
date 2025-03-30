import { children, ParentProps } from "solid-js"
import Leaderboard from "./components/Leaderboard"
import Rewards from "./components/Rewards"
import Gossip from "./components/Gossip"
import { useSwarm } from "./SwarmContext"

export default function Swarm() {
	const ctx = useSwarm()
	const premadeTweet = encodeURIComponent("Running RL Swarm on @gensynai testnet 🔥\n\nhttps://testnet.gensyn.ai")

	return (
		<main class="tracking-wider !font-normal !antialiased max-w-[876px] p-2 md:pt-12 md:pl-12 md:pr-0 flex flex-col justify-between md:min-h-screen ml-auto mr-auto">
			<header class="mb-8">
				<h1 class="uppercase text-2xl tracking-[0.25em] mb-4">Gensyn Testnet</h1>
				<Banner>
					<p class="text-lg uppercase mt-4 mb-4">Join by running an RL Swarm node to train your local model using swarm intelligence. Track your contributions below.</p>
					<p class="uppercase mt-8 mb-8">
						<a href="https://github.com/gensyn-ai/rl-swarm" class="border border-gensyn-brown p-2 bg-[rgba(0,0,0,0.05)]">
							Join the swarm
						</a>
						<a target="_blank" rel="noopener noreferrer" href={`https://x.com/intent/tweet?text=${premadeTweet}`} class="ml-8 underline">
							Share on X
						</a>
					</p>
				</Banner>
			</header>

			<article class="flex flex-col align-top flex-1">
				<Leaderboard />
				<hr class="h-4 bg-[url('/images/line-asterisk.svg')] bg-repeat-x bg-left border-0 w-full mt-8 mb-8" />

				<div class="flex-none mb-2 border border-2 border-dotted p-2">
					Round: {ctx.currentRound()} Stage: {ctx.currentStage()}
				</div>

				<div class="flex flex-col md:flex-row gap-4 mb-8 mt-4">
					<div class="w-full md:w-1/2">
						<Rewards />
					</div>
					<div class="w-full md:w-1/2">
						<Gossip />
					</div>
				</div>

				<Banner>
					<div class="flex flex-row justify-between">
						<div class="my-8 uppercase flex items-center">
							<ul class="list-none flex gap-8 flex-col md:flex-row">
								<li>
									<a class="underline" href="https://gensyn-testnet.explorer.alchemy.com/" target="_blank" rel="noopener noreferrer">
										Block Explorer
									</a>
								</li>
								<li>
									<a class="underline" href="https://www.gensyn.ai/articles/rl-swarm" target="_blank" rel="noopener noreferrer">
										RL Swarm Overview
									</a>
								</li>
								<li>
									<a class="underline" href="">
										Testnet Blog
									</a>
								</li>
							</ul>
						</div>
						<div class="flex items-center flex-col md:flex-row">
							<a class="flex items-center" href="https://gensyn.ai" target="_blank" rel="noopener noreferrer">
								<img class="h-[50px]" src="/images/logo.gif" alt="A spinning gensyn logo" />
								<img class="h-[30px]" src="/images/gen-logotype-dark-rgb.svg" alt="The gensyn name" />
							</a>
							<div class="ml-8 uppercase">gensyn &copy;2025</div>
						</div>
					</div>
				</Banner>

				<footer class="flex items-center mt-8">
					<a target="_blank" rel="noopener noreferrer" href="https://x.com/gensynai">
						<img class="h-[30px]" src="/images/x-logo.svg" alt="X logo" />
					</a>
					<a class="ml-8" target="_blank" rel="noopener noreferrer" href="https://warpcast.com/gensyn">
						<img class="h-[30px]" src="/images/farcaster-logo.svg" alt="X logo" />
					</a>
				</footer>
			</article>
		</main>
	)
}

function Banner(props: ParentProps) {
	const resolvedChildren = children(() => props.children)
	return (
		<>
			<hr class="h-4 bg-[url('/images/line-asterisk.svg')] bg-repeat-x bg-left border-0 flex-shrink-0" />
			{resolvedChildren()}
			<hr class="h-4 bg-[url('/images/line-oblique.svg')] bg-repeat-x bg-left border-0 flex-shrink-0" />
		</>
	)
}
