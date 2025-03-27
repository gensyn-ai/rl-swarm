interface ErrorMessageProps {
	message: string
}

export default function ErrorMessage(props: ErrorMessageProps) {
	return (
		<div class="font-mono text-red-600 bg-black/5 p-4 border border-red-600">
			<div class="flex items-center gap-2">
				<span class="text-xl">[!]</span>
				<span>{props.message}</span>
			</div>
		</div>
	)
}
