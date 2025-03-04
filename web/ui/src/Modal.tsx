type ModalProps = {
    open: boolean
    message: string
}

export default function Modal(props: ModalProps) {
    return (
        <aside class={`fixed inset-0 flex items-center justify-center bg-black/20 transition-opacity duration-100 ${props.open ? 'opacity-100 visible' : 'opacity-0 invisible'}`}>
            <div class="bg-red-500 text-[#2A0D04] w-[80vw] md:w-[30vw] text-center p-8">
                <p class="uppercase">
                    &lt; {props.message} &gt;
                </p>
            </div>
        </aside>
    )
}