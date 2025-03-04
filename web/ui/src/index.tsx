/* @refresh reload */
import { render } from 'solid-js/web'
import './index.css'
import Swarm from './Swarm.tsx'

const root = document.getElementById('root')

render(() => <Swarm />, root!)
