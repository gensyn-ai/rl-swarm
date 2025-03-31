import { createMemo, createEffect, onMount } from "solid-js"
import { useSwarm } from "../SwarmContext"
import * as d3 from "d3"
import SectionHeader from "./SectionHeader"

export default function Rewards() {
	const ctx = useSwarm()

	// Create a memoized value for the rewards data
	const rewardsHistoryData = createMemo(() => ctx.rewardsHistory() ?? { leaders: [] })

	return (
		<section class="flex flex-col gap-2">
			<SectionHeader title="Training Rewards" tooltip={<RewardsTooltip />} />
			<RewardsGraph data={rewardsHistoryData()} />
		</section>
	)
}

function RewardsTooltip() {
	return (
		<div class="uppercase">
			<p>Training Rewards are based on your agent's actions within the swarm, including:</p>
			<ul class="mt-4 list-decimal pl-8">
				<li class="mb-2"><strong>Getting the right answer</strong> &mdash; Submitting a factually correct answer</li>
				<li class="mb-2"><strong>Following instructions</strong> &mdash; Using the correct XML format in responses</li>
				<li class="mb-2"><strong>Showing work</strong> &mdash; Including proper reasoning in the &lt;think&gt; tags</li>
				<li class="mb-2"><strong>Making good judgments</strong> &mdash; Correctly evaluating other agents' solutions</li>
				<li><strong>Building consensus</strong> &mdash; Agreeing with the majority on the best solution</li>
			</ul>
			<p class="mt-4">The leaderboard shows cumulative training rewards, while the graph shows rewards since you loaded the page.</p>
		</div>
	)
}

function RewardsGraph(props: { data: { leaders: { id: string; values: { x: number; y: number }[] }[] } }) {
	let svgRef: SVGSVGElement | undefined

	// Props aren't automatically reactive, so we need to turn the props into a signal.
	// createMemo automatically updates when props.data changes, opposed to createSignal which is manually reactive.
	const chartData = createMemo(() => props.data)

	// TODO: Set dimensions magically
	const margin = { top: 10, right: 10, bottom: 30, left: 50 }
	const width = 400 - margin.left - margin.right
	const height = 300 - margin.top - margin.bottom

	onMount(() => {
		drawChart()
	})

	createEffect(() => {
		updateChart()
	})

	function drawChart() {
		if (!svgRef) {
			return
		}

		const svg = d3
			.select(svgRef)
			.attr("width", width + margin.left + margin.right)
			.attr("height", height + margin.top + margin.bottom)
			.append("g")
			.attr("transform", `translate(${margin.left},${margin.top})`) // push the chart a bit to account for labels/legends

		// Define scales.
		// Scales map data space into SVG space.
		const xScale = d3.scaleLinear().domain([0, 0]).range([0, width])
		const yScale = d3.scaleLinear().domain([0, 0]).range([height, 0])

		// Set scales based on data.
		const allXs = chartData().leaders.flatMap((leader) => leader.values.map((d) => d.x))
		const allYs = chartData().leaders.flatMap((leader) => leader.values.map((d) => d.y))

		yScale.domain([d3.min(allYs)!, d3.max(allYs)!])
		xScale.domain([d3.min(allXs)!, d3.max(allXs)!])

		const xTicksCount = Math.min(5, allXs.length)
		const minX = d3.min(allXs)!

		// Horizontal grid lines
		// Setting a tick size to a negative width here extends the ticks across the chart.
		svg.append("g")
			.attr("class", "grid")
			.call(
				d3
					.axisLeft(yScale)
					.tickSize(-width)
					.tickFormat(() => "")
					.ticks(5),
			)
			.selectAll(".tick line")
			.attr("stroke", () => "rgba(0, 0, 0, 0.3)")
			.attr("stroke-dasharray", "3,3")
			.filter((_, i, _nodes) => i === 6)
			.attr("stroke", "none")

		// Vertical grid lines
		svg.append("g")
			.attr("class", "grid")
			.attr("transform", `translate(0,${height})`)
			.call(
				d3
					.axisBottom(xScale)
					.tickSize(-height)
					.tickFormat(() => "")
					.ticks(xTicksCount),
			)
			.selectAll("line")
			.attr("stroke", () => "rgba(0, 0, 0, 0.3)")
			.attr("stroke-dasharray", "3,3")

		// Define color scale
		const color = (i: number) => {
			const cs = ["#2A0D04", "#14BD4A", "#B800C4", "#FF6600", "#00A8F3", "#FFD700", "#8B4513", "#FF1493", "#7FFF00", "#9400D3"]
			return cs[i % cs.length]
		}

		// Define line generator.
		// Given data points, it generates an SVG path.
		const line = d3
			.line<{ x: number; y: number }>()
			.x((d) => xScale(d.x))
			.y((d) => yScale(d.y))

		// Draw data.
		svg.selectAll(".line")
			.data(chartData().leaders)
			.enter()
			.append("path")
			.attr("class", "line")
			.attr("fill", "none")
			.attr("stroke", (_, i) => color(i))
			.attr("stroke-width", 2)
			.attr("stroke-dasharray", "2 2")
			.attr("stroke-linejoin", "round")
			.attr("d", (d) => line(d.values) as string)

		// Add X and Y axis
		svg.append("g")
			.attr("class", "x-axis")
			.attr("transform", `translate(0,${height})`)
			.call(d3.axisBottom(xScale).tickSize(0).tickPadding(10))
			.call(
				d3
					.axisBottom(xScale)
					.tickSize(0)
					.tickFormat((d) => `${Math.round(d.valueOf() - minX)}`)
					.ticks(xTicksCount),
			)
			.attr("stroke-width", 2)
			.selectAll("text")
			.style("font-size", "12px")
			.style("font-family", "monospace")

		svg.append("g").attr("class", "y-axis").attr("stroke-width", 2).call(d3.axisLeft(yScale).tickSize(0).tickPadding(10)).selectAll("text").style("font-size", "12px").style("font-family", "monospace")

		// Removes the top-most and right-most borders of the chart
		svg.selectAll(".domain")
			.filter((_, i, _nodes) => i == 0 || i == 1)
			.attr("stroke", "none")

		// Add X-axis label
		svg.append("text")
			.attr("class", "x-axis-label")
			.attr("x", width / 2) // Center it horizontally
			.attr("y", height + margin.bottom) // Position it below the X-axis
			.attr("text-anchor", "middle") // Center the text
			.style("font-size", "10px")
			.style("font-family", "Aux Mono")
			.text("SECONDS ELAPSED")
	}

	function updateChart() {
		if (!svgRef) {
			return
		}
		// Remove previous chart before re-adding
		// This makes the chart update less smooth, but removes any issues with re-rendering.
		d3.select(svgRef).selectAll("*").remove()
		drawChart()
	}

	return <svg ref={svgRef}></svg>
}
