import { useState } from 'react'
import heroImg from './assets/hero.png'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import './App.css'
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import LandingPage from './pages/LandingPage';

function App() {
  const [count, setCount] = useState(0)

  return (
   <>
    {/* the assalaam the alaikum 🙋‍♂️🙋‍♂️🙋‍♀️🙋‍♀️ */}
    <Routes>
       <Route path="/" element={<LandingPage />} />
       <Route path ="/Header" element={<Header />} />
    </Routes>
   </>
  )
}

export default App
