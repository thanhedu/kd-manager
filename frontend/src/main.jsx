import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

// ĐƯỜNG DẪN MỚI: styles.css nằm trong src/components/
import './components/styles.css'

createRoot(document.getElementById('root')).render(<App />)
